import argparse
import os

import networkx as nx
from causal_testing.discovery.abstract_discovery import Discovery

from discovery import (
    dag_confusion_matrix,
    dag_difference_metrics,
    evaluate_dag,
    run_causal_learn_discovery,
    run_ctf_discovery,
    techniques,
)
from program_generation import dag_and_data

# We set the number of edges per node to 2 to reflect the fact that most software errors come from small
# numbers of interacting variables
EDGES_PER_NODE = 2


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output", help="Path for output DAG file (.dot)", required=True)
    parser.add_argument("-r", "--reference-output", help="Path for reference DAG file (.dot)", required=True)
    parser.add_argument(
        "-t", "--technique", help="The algorithm to run. One of GES, HillClimbSearch, PC", required=True
    )

    parser.add_argument(
        "-k",
        "--expert-knowledge-amount",
        type=float,
        help="The proportion of edges and non-edges to be given to the discovery algorithm. (Between 0 and 1)",
        default=0,
    )
    parser.add_argument(
        "-D", "--data-amount", type=int, help="The number of the data points to generate.", required=True
    )
    parser.add_argument("-n", "--nodes", type=int, help="The number of nodes to generate.", required=True)
    parser.add_argument(
        "-c",
        "--conditional-probability",
        type=float,
        help="The probability of a causal relationship being conditional.",
        default=0.5,
    )
    parser.add_argument("-s", "--seed", type=int, help="Random seed.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.technique not in techniques:
        raise ValueError(f"Unsupported technique {args.technique}. Must be one of {list(techniques)}.")
    technique = techniques[args.technique]

    n_edges = EDGES_PER_NODE * args.nodes
    p_edge = min(n_edges / ((args.nodes * (args.nodes - 1)) / 2), 0.99)

    reference_dag, data = dag_and_data(
        n_nodes=args.nodes,
        p_edge=p_edge,
        p_conditional=args.conditional_probability,
        num_points=args.data_amount,
        seed=args.seed,
    )

    try:
        if args.technique in ["pc", "ges", "grasp"]:
            inferred_dag = run_causal_learn_discovery(technique=technique, df=data)
        else:
            inferred_dag = run_ctf_discovery(technique, df=data, random_seed=args.seed)

    except ValueError as e:
        inferred_dag = nx.DiGraph()
        inferred_dag.add_nodes_from(reference_dag.nodes)
        inferred_dag.graph["graph"] = {"error": str(e)}

    inferred_dag.graph["graph"] |= (
        vars(args)
        | {
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
        inferred_dag.graph["graph"] |= {"reference_" + k: v for k, v in evaluate_dag(reference_dag, data).items()}

    except (nx.HasACycle, ValueError) as e:
        if "error" not in inferred_dag.graph["graph"]:
            inferred_dag.graph["graph"] = vars(args) | {"error": str(e)}

    # output
    for output in [args.output, args.reference_output]:
        root, _ = os.path.split(output)
        if not os.path.exists(root):
            os.makedirs(root)
    nx.drawing.nx_pydot.write_dot(inferred_dag, args.output)
    nx.drawing.nx_pydot.write_dot(reference_dag, args.reference_output)
