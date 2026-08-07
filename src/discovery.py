import argparse
import pandas as pd
import networkx as nx
from pgmpy.causal_discovery import HillClimbSearch, ExpertKnowledge, PC, GES
from time import time
from causal_testing.causal_testing_framework import CausalTestingFramework
from causal_testing.specification.causal_dag import CausalDAG
from collections import Counter
import random  # no point seeding random since we can't seed the causal discovery techniques
import os
from causal_testing.discovery.hill_climber_discovery import HillClimberDiscovery
from causal_testing.discovery.nsga_discovery import NSGADiscovery
from causal_testing.discovery.abstract_discovery import Discovery
import warnings

warnings.filterwarnings("ignore")  # Hide warnings


def setup_domain_knowledge(reference_dag_path: str, expert_knowledge_amount: float):
    reference_dag = nx.nx_pydot.read_dot(reference_dag_path)
    required_edges = set(reference_dag.edges())
    forbidden_edges = set(nx.non_edges(reference_dag))
    total_edges = len(required_edges) + len(forbidden_edges)
    sampled_edges = random.sample(
        sorted(required_edges.union(forbidden_edges)), round(total_edges * expert_knowledge_amount)
    )

    return ExpertKnowledge(
        required_edges=required_edges.intersection(sampled_edges),
        forbidden_edges=forbidden_edges.intersection(sampled_edges),
    )


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

    # clean data
    # df = df.replace([np.inf, -np.inf], np.nan)
    # df = df.dropna()

    # Drop unnamed columns
    unnamed_columns = [c for c in df.columns if c.startswith("Unnamed: ")]
    df = df.drop(unnamed_columns, axis=1)

    # encode categoricals
    cat_cols = df.select_dtypes(include=["object", "string"]).columns
    for col in cat_cols:
        df[col] = df[col].astype("category").cat.codes

    # remove zero-variance columns
    # variances = df.var()
    # constant_cols = variances[variances == 0].index
    # if len(constant_cols) > 0:
    #     print(f"Warning: Dropping constant columns due to zero variance: {list(constant_cols)}")
    #     df = df.drop(columns=constant_cols)
    return df.sample(frac=data_amount)


def run_baseline_discovery(
    technique, df: pd.DataFrame, expert_knowledge: ExpertKnowledge = None, context: bool = False
) -> nx.DiGraph:
    args = {"return_type": "dag"}
    if expert_knowledge:
        args["expert_knowledge"] = expert_knowledge

    start_time = time()
    estimator = technique(**args)
    estimator.fit(df)
    end_time = time()

    dag = estimator.causal_graph_
    dag.graph["graph"] = {"time": end_time - start_time}

    # post-processing removal
    if context and "file_index" in dag.nodes():
        dag.remove_node("file_index")
    return dag


def run_ctf_discovery(
    technique, df: pd.DataFrame, expert_knowledge: ExpertKnowledge = None, context: bool = False, **kwargs
) -> nx.DiGraph:
    # Need to reset index to allow for multiple files having the same index (i.e. starting at zero).
    # Otherwise you end up with duplicate indices, which causes problems further down the line
    start_time = time()
    discover = technique(
        df=df,
        exclude_edges=expert_knowledge.forbidden_edges if expert_knowledge else None,
        include_edges=expert_knowledge.required_edges if expert_knowledge else None,
        **kwargs,
    )
    dag = discover.discover()
    end_time = time()

    dag.graph["graph"] = {"time": end_time - start_time}

    # post-processing removal
    if context and "file_index" in dag.nodes():
        dag.remove_node("file_index")
    return dag


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--data", nargs="+", required=True, help="Path(s) to data file(s).")
    parser.add_argument("-o", "--output", help="Path for output DAG file (.dot)", required=True)
    parser.add_argument(
        "-t", "--technique", help="The algorithm to run. One of GES, HillClimbSearch, PC", required=True
    )

    parser.add_argument(
        "-c",
        "--context",
        action="store_true",
        default=False,
        help="Whether to include a 'context' column to store the source file.",
    )
    parser.add_argument("-r", "--reference-dag", help="Path to reference (ground truth) dag.")
    parser.add_argument(
        "-e",
        "--expert-knowledge-amount",
        type=float,
        help="The proportion of edges and non-edges to be given to the discovery algorithm. (Between 0 and 1)",
    )
    parser.add_argument(
        "-D", "--data-amount", type=float, help="The proportion of the data to use. (Between 0 and 1)", default=1
    )
    parser.add_argument(
        "-V",
        "--variables",
        help="The subset of variables from the data to consider. Defaults to all.",
        nargs="*",
        default=[],
    )
    return parser.parse_args()


def evaluate_dag(dag: nx.DiGraph, df: pd.DataFrame):
    causal_dag = CausalDAG(datatypes=df.dtypes)
    causal_dag.add_nodes_from(dag.nodes())
    causal_dag.add_edges_from(dag.edges())
    framework = CausalTestingFramework(dag=causal_dag, df=df, test_cases=causal_dag.generate_causal_tests())
    framework.run_tests(silent=True)

    return Counter([test.result.outcome for test in framework.test_cases])


if __name__ == "__main__":
    args = parse_args()

    techniques = {
        "PC": PC,
        "GES": GES,
        "HillClimbSearch": HillClimbSearch,
        "NSGADiscovery": NSGADiscovery,
        "HillClimberDiscovery": HillClimberDiscovery,
    }
    if args.technique not in techniques:
        raise ValueError(f"Unsupported technique {args.technique}. Must be one of {list(techniques)}.")
    technique = techniques[args.technique]

    data = load_data(args.data, context=args.context, variables=args.variables, data_amount=args.data_amount)
    expert_knowledge = (
        setup_domain_knowledge(args.reference_dag, args.expert_knowledge_amount)
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
        inferred_dag.graph["graph"] |= {
            "expert_knowledge_amount": args.expert_knowledge_amount,
            "data_points": len(data),
            "required_edges": len(expert_knowledge.required_edges) if expert_knowledge else 0,
            "forbidden_edges": len(expert_knowledge.forbidden_edges) if expert_knowledge else 0,
            "pass": 0,
            "fail": 0,
            "inestimable": 0,
        } | {k.name.lower(): v for k, v in evaluate_dag(inferred_dag, data).items()}

    except ValueError as e:
        inferred_dag = nx.DiGraph()
        inferred_dag.graph["graph"] = {"error": str(e)}

    # output
    root, _ = os.path.split(args.output)
    if not os.path.exists(root):
        os.makedirs(root)
    nx.drawing.nx_pydot.write_dot(inferred_dag, args.output)
