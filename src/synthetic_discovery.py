import argparse
import os

import networkx as nx
from causal_testing.discovery.abstract_discovery import Discovery

from discovery import (
    dag_confusion_matrix,
    evaluate_dag,
    run_baseline_discovery,
    run_ctf_discovery,
    setup_domain_knowledge,
    techniques,
)
from program_generation import dag_and_data


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output", help="Path for output DAG file (.dot)", required=True)
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
    parser.add_argument("-E", "--edge-probability", type=float, help="The probability of edge creation.", default=0.5)
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

    reference_dag, data = dag_and_data(
        n_nodes=args.nodes,
        p_edge=args.edge_probability,
        p_conditional=args.conditional_probability,
        num_points=args.data_amount,
        seed=args.seed,
    )

    expert_knowledge = (
        setup_domain_knowledge(reference_dag, args.expert_knowledge_amount) if args.technique != "GES" else None
    )

    try:
        if issubclass(technique, Discovery):
            inferred_dag = run_ctf_discovery(
                technique,
                df=data,
                expert_knowledge=expert_knowledge,
            )
        else:
            inferred_dag = run_baseline_discovery(
                technique,
                df=data,
                expert_knowledge=expert_knowledge,
            )

    except ValueError as e:
        inferred_dag = nx.DiGraph()
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
        | {
            "true_edges": len(reference_dag.edges),
            "inferred_edges": len(inferred_dag.edges),
            "true_non_edges": len(list(nx.non_edges(reference_dag))),
            "inferred_non_edges": len(list(nx.non_edges(inferred_dag))),
        }
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
