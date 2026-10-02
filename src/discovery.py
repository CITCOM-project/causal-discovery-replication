import argparse
import os
import warnings
from collections import Counter
from time import time

import networkx as nx
import numpy as np
import pandas as pd
from castle.algorithms import Notears
from causal_testing.causal_testing_framework import CausalTestingFramework
from causal_testing.discovery.abstract_discovery import Discovery, simple_cycle
from causal_testing.discovery.hill_climber_discovery import HillClimberDiscovery
from causal_testing.specification.causal_dag import CausalDAG
from causallearn.search.ConstraintBased.PC import pc
from causallearn.search.ScoreBased.GES import ges
from cdt.metrics import SHD, SID, precision_recall

warnings.filterwarnings("ignore")  # Hide warnings

techniques = {
    "HillClimberDiscovery": HillClimberDiscovery,
    "pc": pc,
    "ges": ges,
    "notears": Notears,
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


def pdag_to_dag(pdag: CausalDAG) -> CausalDAG:
    directed_edges = []
    undirected_edges = set()

    for u, v in pdag.edges():
        if pdag.has_edge(v, u):
            # Sort node names/indices to avoid adding (u,v) and (v,u)
            undirected_edges.add(tuple(sorted([u, v])))
        else:
            directed_edges.append((u, v))

    dag = CausalDAG(ignore_cycles=True)
    dag.add_nodes_from(pdag.nodes)
    dag.add_edges_from(directed_edges)

    if dag.is_acyclic():
        topo_order = {node: rank for rank, node in enumerate(nx.topological_sort(dag))}
        for u, v in undirected_edges:
            if topo_order[u] < topo_order[v]:
                dag.add_edge(u, v)
            else:
                dag.add_edge(v, u)
        return dag
    node_1, node_2 = simple_cycle(dag)[0]
    pdag.remove_edge(node_1, node_2)
    return pdag_to_dag(pdag)


def run_causal_learn_discovery(technique, df: pd.DataFrame) -> CausalDAG:
    start_time = time()
    try:
        match technique:
            case "pc":
                causal_graph = pc(data=df.to_numpy(), node_names=df.columns, max_k=6).G
            case "ges":
                causal_graph = ges(
                    X=df.to_numpy(),
                    node_names=df.columns,
                )["G"]
            case _:
                raise ValueError(f"Invalid technique {technique}.")

        pdag = CausalDAG(ignore_cycles=True)
        pdag.add_nodes_from(df.columns)
        pdag.add_edges_from(
            map(lambda edge: (edge.get_node1().get_name(), edge.get_node2().get_name()), causal_graph.get_graph_edges())
        )
        dag = pdag_to_dag(pdag)
    except ValueError as e:
        # If the discovery algorithm fails, we know no more than the variables we have
        dag = CausalDAG(ignore_cycles=True)
        dag.add_nodes_from(df.columns)
        dag.graph["graph"] = dag.graph.get("graph", {}) | {"error": str(e)}

    end_time = time()

    dag.graph["graph"] = dag.graph.get("graph", {}) | {"time": end_time - start_time}
    assert dag.is_acyclic()
    return dag


def run_gcastle_discovery(technique, df: pd.DataFrame) -> CausalDAG:
    start_time = time()
    model = techniques[technique]()
    model.learn(df)

    pdag = CausalDAG(ignore_cycles=True)
    pdag.add_nodes_from(df.columns)
    for i, u in enumerate(df.columns):
        for j, v in enumerate(df.columns):
            if model.causal_matrix[i, j] != 0:
                pdag.add_edge(u, v)
    dag = pdag_to_dag(pdag)
    end_time = time()

    dag.graph["graph"] = dag.graph.get("graph", {}) | {"time": end_time - start_time}
    assert dag.is_acyclic()
    return dag


def run_ctf_discovery(df: pd.DataFrame, random_seed: int = None, **kwargs) -> CausalDAG:
    start_time = time()
    if random_seed is None:
        random_seed = start_time
    discover = HillClimberDiscovery(
        df=df,
        random_seed=random_seed,
        exclude_edges=[(".*", r"X\d+")] + kwargs.pop("exclude_edges", []),
        **kwargs,
    )
    dag = discover.discover()
    end_time = time()

    dag.graph["graph"] = dag.graph.get("graph", {}) | {"time": end_time - start_time}
    assert dag.is_acyclic()
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

    causal_dag = CausalDAG(datatypes=df.dtypes, ignore_cycles=True)
    causal_dag.add_nodes_from(dag.nodes())
    causal_dag.add_edges_from(dag.edges())

    framework = CausalTestingFramework(dag=causal_dag, df=df, test_cases=causal_dag.generate_causal_tests())
    framework.run_tests(silent=True)
    counts = {
        k.name.lower(): v / len(framework.test_cases)
        for k, v in Counter([test.result.outcome for test in framework.test_cases]).items()
    }
    framework.save_results("/tmp/results.json")
    return counts


def dag_confusion_matrix(reference_dag: nx.DiGraph, inferred_dag: nx.DiGraph):

    return {
        "true_positives": [edge for edge in inferred_dag.edges if edge in reference_dag.edges],
        "false_positives": [edge for edge in inferred_dag.edges if edge not in reference_dag.edges],
        "true_negatives": [edge for edge in nx.non_edges(inferred_dag) if edge not in reference_dag.edges],
        "false_negatives": [edge for edge in nx.non_edges(inferred_dag) if edge in reference_dag.edges],
    }


def dag_difference_metrics(reference_dag: nx.DiGraph, inferred_dag: nx.DiGraph):
    print(precision_recall(reference_dag, inferred_dag))
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

    try:
        if issubclass(technique, Discovery):
            inferred_dag = run_ctf_discovery(technique, df=data, context=args.context, random_seed=args.seed)
        else:
            inferred_dag = run_causal_learn_discovery(
                technique,
                df=data,
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
        inferred_dag.graph["graph"] |= evaluate_dag(inferred_dag, data)

    except (nx.HasACycle, ValueError) as e:
        if "error" not in inferred_dag.graph["graph"]:
            inferred_dag.graph["graph"] = {"error": str(e)}

    # output
    root, _ = os.path.split(args.output)
    if not os.path.exists(root):
        os.makedirs(root)
    nx.drawing.nx_pydot.write_dot(inferred_dag, args.output)
