import argparse
import os
import random  # no point seeding random since we can't seed the causal discovery techniques
import warnings
from collections import Counter
from time import time

import networkx as nx
import numpy as np
import pandas as pd
from causal_testing.causal_testing_framework import CausalTestingFramework
from causal_testing.discovery.abstract_discovery import Discovery
from causal_testing.discovery.hill_climber_discovery import HillClimberDiscovery
from causal_testing.specification.causal_dag import CausalDAG
from causallearn.search.ConstraintBased.PC import pc
from causallearn.search.PermutationBased.GRaSP import grasp
from causallearn.search.ScoreBased.GES import ges
from causallearn.utils.GraphUtils import GraphUtils
from causallearn.utils.PDAG2DAG import pdag2dag
from cdt.metrics import SHD, SID

warnings.filterwarnings("ignore")  # Hide warnings

techniques = {
    "HillClimberDiscovery": HillClimberDiscovery,
    "pc": pc,
    "ges": ges,
    "grasp": grasp,
}


def load_data(data_path: str, context: bool = False, variables: list[str] = None, data_amount: float = 1):
    # load data
    if context:
        dfs = []
        for i, path in enumerate(data_path):
            temp_df = pd.read_csv(path)
            temp_df["file_index"] = i
            dfs.append(temp_df)
        df = pd.concat(dfs, ignore_index=True)

        if variables:
            df = df[list(set(variables + ["file_index"]))]

    else:
        df = pd.concat((pd.read_csv(path) for path in data_path), ignore_index=True)
        if variables:
            df = df[variables]

    # Drop unnamed columns
    unnamed_columns = [c for c in df.columns if c.startswith("Unnamed: ")]
    df = df.drop(unnamed_columns, axis=1)

    assert not df.isna().any().any(), "Dataset cannot contain NaN values"
    assert not np.isinf(df.to_numpy()).any(), "Dataset cannot contain Inf values"
    constant_cols = [col for col in df.columns if df[col].nunique() <= 1]
    assert not constant_cols, f"Columns {constant_cols} were constant."

    # encode categoricals
    cat_cols = df.select_dtypes(include=["object", "string"]).columns
    for col in cat_cols:
        df[col] = df[col].astype("category")

    return df.sample(frac=data_amount)


def run_causal_learn_discovery(technique, df: pd.DataFrame):
    causal_graph = technique(df.to_numpy())

    if technique == pc:
        pydot_graph = GraphUtils.to_pydot(pdag2dag(causal_graph.G), labels=list(df.columns))
    elif technique == ges:
        pydot_graph = GraphUtils.to_pydot(pdag2dag(causal_graph["G"]), labels=list(df.columns))
    elif technique == grasp:
        pydot_graph = GraphUtils.to_pydot(pdag2dag(causal_graph), labels=list(df.columns))
    else:
        raise ValueError(f"Unsupported technique {technique}.")

    dag = CausalDAG()
    dag.graph["graph"] = {}
    for node in pydot_graph.get_nodes():
        dag.add_node(node.get_label())
    for edge in pydot_graph.get_edges():
        [source] = pydot_graph.get_node(str(edge.get_source()))
        [target] = pydot_graph.get_node(str(edge.get_destination()))
        dag.add_edge(source.get_label(), target.get_label())
    return dag


def run_ctf_discovery(technique, df: pd.DataFrame, **kwargs) -> nx.DiGraph:
    # Need to reset index to allow for multiple files having the same index (i.e. starting at zero).
    # Otherwise you end up with duplicate indices, which causes problems further down the line
    start_time = time()
    discover = technique(
        df=df,
        alpha=0.01,
        **kwargs,
    )
    dag = discover.discover()
    end_time = time()

    dag.graph["graph"] = {"time": end_time - start_time, "seed": start_time}

    return dag


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--data", nargs="+", required=True, help="Path(s) to data file(s).")
    parser.add_argument("-o", "--output", help="Path for output DAG file (.dot)", required=True)
    parser.add_argument(
        "-t", "--technique", help="The algorithm to run. One of GES, HillClimbSearch, PC", required=True
    )

    parser.add_argument("-r", "--reference-dag", help="Path to reference (ground truth) dag.", required=True)
    parser.add_argument(
        "-e",
        "--expert-knowledge-amount",
        type=float,
        help="The proportion of edges and non-edges to be given to the discovery algorithm. (Between 0 and 1)",
    )
    parser.add_argument(
        "-D", "--data-amount", type=float, help="The proportion of the data to use. (Between 0 and 1)", default=1
    )
    return parser.parse_args()


def evaluate_dag(dag: nx.DiGraph, df: pd.DataFrame):
    causal_dag = CausalDAG(datatypes=df.dtypes)
    causal_dag.add_nodes_from(dag.nodes())
    causal_dag.add_edges_from(dag.edges())
    framework = CausalTestingFramework(dag=causal_dag, df=df, test_cases=causal_dag.generate_causal_tests())
    framework.run_tests(silent=True)

    return {
        k: v / len(framework.test_cases)
        for k, v in Counter([test.result.outcome for test in framework.test_cases]).items()
    }


def dag_confusion_matrix(reference_dag: nx.DiGraph, inferred_dag: nx.DiGraph):

    true = set(reference_dag.edges())
    false = set(nx.non_edges(reference_dag))
    positives = set(inferred_dag.edges())
    negatives = set(nx.non_edges(inferred_dag))

    return {
        "true_positives": true.intersection(positives),
        "false_positives": false.intersection(positives),
        "true_negatives": true.intersection(negatives),
        "false_negatives": false.intersection(negatives),
    }


def dag_difference_metrics(reference_dag: nx.DiGraph, inferred_dag: nx.DiGraph):
    return {
        "true_edges": len(reference_dag.edges),
        "inferred_edges": len(inferred_dag.edges),
        "true_non_edges": len(list(nx.non_edges(reference_dag))),
        "inferred_non_edges": len(list(nx.non_edges(inferred_dag))),
        "structural_hamming": SHD(reference_dag, inferred_dag),
        "structural_intervention": SID(reference_dag, inferred_dag),
        "edit_distance": next(nx.algorithms.similarity.optimize_graph_edit_distance(reference_dag, inferred_dag)),
    }


if __name__ == "__main__":
    args = parse_args()

    if args.technique not in techniques:
        raise ValueError(f"Unsupported technique {args.technique}. Must be one of {list(techniques)}.")
    technique = techniques[args.technique]

    reference_dag = CausalDAG(args.reference_dag)

    data = load_data(
        args.data,
        context=args.context,
        variables=list(reference_dag.nodes()),
        data_amount=args.data_amount,
    )

    expert_knowledge = (
        setup_domain_knowledge(reference_dag, args.expert_knowledge_amount)
        if args.reference_dag and args.expert_knowledge_amount
        else None
    )

    try:
        if issubclass(technique, Discovery):
            inferred_dag = run_ctf_discovery(
                technique,
                df=data,
                expert_knowledge=expert_knowledge,
                context=args.context,
            )
        else:
            inferred_dag = run_baseline_discovery(
                technique,
                df=data,
                expert_knowledge=expert_knowledge,
                context=args.context,
            )

    except ValueError as e:
        inferred_dag = nx.DiGraph()
        inferred_dag.nodes = reference_dag.nodes
        inferred_dag.graph["graph"] = {"error": str(e)}

    inferred_dag.graph["graph"] |= (
        {
            "technique": args.technique,
            "expert_knowledge_amount": args.expert_knowledge_amount,
            "data_points": len(data),
            "required_edges": len(expert_knowledge.required_edges) if expert_knowledge else 0,
            "forbidden_edges": len(expert_knowledge.forbidden_edges) if expert_knowledge else 0,
            "pass": 0,
            "fail": 0,
            "inestimable": 0,
        }
        | {f"directional_{key}": len(value) for key, value in dag_confusion_matrix(reference_dag, inferred_dag).items()}
        | {
            f"non_directional_{key}": len(value)
            for key, value in dag_confusion_matrix(reference_dag.to_undirected(), inferred_dag.to_undirected()).items()
        }
        | dag_difference_metrics(reference_dag, inferred_dag)
    )
    try:
        # Do this as a separate step in case the DAG is cyclic
        inferred_dag.graph["graph"] |= {k.name.lower(): v for k, v in evaluate_dag(inferred_dag, data).items()}

    except (nx.HasACycle, ValueError) as e:
        if "error" not in inferred_dag.graph["graph"]:
            inferred_dag.graph["graph"] = {"error": str(e)}

    # output
    root, _ = os.path.split(args.output)
    if not os.path.exists(root):
        os.makedirs(root)
    nx.drawing.nx_pydot.write_dot(inferred_dag, args.output)
