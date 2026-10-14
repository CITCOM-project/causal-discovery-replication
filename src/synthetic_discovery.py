import argparse
import os
from collections import Counter

import networkx as nx
import pandas as pd
from causal_testing.causal_testing_framework import CausalTestingFramework
from causal_testing.specification.causal_dag import CausalDAG
from causal_testing.testing.causal_test_case import CausalTestCase

from discovery import (
    dag_confusion_matrix,
    dag_difference_metrics,
    evaluate_dag,
    run_causal_learn_discovery,
    run_ctf_discovery,
    run_gcastle_discovery,
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
    parser.add_argument("-t", "--technique", help=f"The algorithm to run. One of {list(techniques)}", required=True)
    parser.add_argument(
        "-D", "--data-amount", type=int, help="The number of the data points to generate.", required=True
    )
    parser.add_argument("-n", "--nodes", type=int, help="The number of nodes to generate.", required=True)
    parser.add_argument(
        "-c",
        "--conditional-probability",
        type=float,
        help="The probability of a causal relationship being conditional.",
        default=0,
    )
    parser.add_argument("-s", "--seed", type=int, help="Random seed.")
    return parser.parse_args()


def infer_dag(args, data) -> CausalDAG:
    if args.technique == "HillClimberDiscovery":
        inferred_dag = run_ctf_discovery(
            df=data,
            random_seed=args.seed,
        )
    elif args.technique == "notears":
        inferred_dag = run_gcastle_discovery(technique=args.technique, df=data)
    else:
        inferred_dag = run_causal_learn_discovery(technique=args.technique, df=data)

    return inferred_dag


def killed_mutants(inferred_dag: CausalDAG, mutants, reference_tests: dict[str, int]):
    """
    Check whether the corresponding test case for a mutated edge failed, killing the mutant.
    Tested mutants represent mutated edges that correspond to a (treatment, outcome) test from the causal DAG.
    Killed mutants represent tests that passed for the raw data and failed for the mutated data, thereby unambiguously
    killing the mutant
    Ambiguous mutants represent tests that failed on both the raw data and the mutated data, thus technically killing
    the mutant, but not in a way that tells us much.
    """
    result = {"tested_mutants": 0, "killed_mutants": 0, "ambiguous_mutants": 0, "total_mutants": 0}

    for (treatment, outcome), mutated_data in mutants:
        ctf = CausalTestingFramework(dag=inferred_dag, df=mutated_data, test_cases=inferred_dag.generate_causal_tests())
        ctf.run_tests(silent=True)
        reference_test = [
            test
            for test in reference_tests
            if test.treatment_variable == treatment and test.outcome_variable == outcome
        ]
        mutant_test = [
            test for test in ctf.test_cases if test.treatment_variable == treatment and test.outcome_variable == outcome
        ]

        result["tested_mutants"] += 1
        result["tested_mutants"] += int(len(reference_test) > 0 and len(mutant_test) > 0)
        result["killed_mutants"] += int(
            len(reference_test) > 0
            and len(mutant_test) > 0
            and reference_test[0].result.passed
            and not mutant_test[0].result.passed
        )
        result["ambiguous_mutants"] += int(
            len(reference_test) > 0 and len(mutant_test) > 0 and not mutant_test[0].result.passed
        )
    return result


def main():
    args = parse_args()

    if os.path.exists(args.output):
        return

    if args.technique not in techniques:
        raise ValueError(f"Unsupported technique {args.technique}. Must be one of {list(techniques)}.")

    n_edges = EDGES_PER_NODE * args.nodes
    p_edge = min(n_edges / ((args.nodes * (args.nodes - 1)) / 2), 0.99)

    reference_dag, raw_data, mutants = dag_and_data(
        n_nodes=args.nodes,
        p_edge=p_edge,
        p_conditional=args.conditional_probability,
        num_points=args.data_amount,
        seed=args.seed,
    )

    for output in [args.output, args.reference_output]:
        root, _ = os.path.split(output)
        if not os.path.exists(root):
            os.makedirs(root)
    nx.drawing.nx_pydot.write_dot(reference_dag, args.reference_output)

    inferred_dag = infer_dag(args, raw_data)

    framework = CausalTestingFramework(dag=inferred_dag, df=raw_data, test_cases=inferred_dag.generate_causal_tests())
    framework.run_tests(silent=True)

    inferred_dag.graph["graph"] |= (
        vars(args)
        | killed_mutants(inferred_dag, mutants, framework.test_cases)
        | {
            "pass": 0,
            "fail": 0,
            "inestimable": 0,
        }
        | {
            k.name.lower(): v / len(framework.test_cases)
            for k, v in Counter([test.result.outcome for test in framework.test_cases]).items()
        }
        | {f"directional_{key}": len(value) for key, value in dag_confusion_matrix(reference_dag, inferred_dag).items()}
        | {
            f"non_directional_{key}": len(value)
            for key, value in dag_confusion_matrix(reference_dag.to_undirected(), inferred_dag.to_undirected()).items()
        }
        | dag_difference_metrics(reference_dag, inferred_dag)
    )
    inferred_dag.graph["graph"] |= {"reference_" + k: v for k, v in evaluate_dag(reference_dag, raw_data).items()}

    nx.drawing.nx_pydot.write_dot(inferred_dag, args.output)


if __name__ == "__main__":
    main()
