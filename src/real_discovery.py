import argparse
import os
from glob import glob

import networkx as nx
import pandas as pd

from discovery import (
    evaluate_dag,
    run_causal_learn_discovery,
    run_ctf_discovery,
    run_gcastle_discovery,
    techniques,
)


def get_valid_columns(file_path: str) -> list[str]:
    """
    Filter out irrelevant and non-usable columns.
    """
    df = pd.read_csv(file_path)

    valid_cols = [
        c
        for c in df.columns
        if "Unnamed" not in c  # Errant index columns from saving dataframes
        and "index" not in c  # run indices
        and "seed" not in c  # random seeds
        and "weather"
        not in c  # Duplicated columns in one of the CARLA datasets (e.g. cloudiness and weather_cloudiness)
        and df[c].nunique(dropna=False) > 1  # Check unique count without dropping NaNs
        and not df[c].isnull().any()  # Ensure no NaN values in columns
    ]
    return valid_cols


def main():
    """
    Run the discovery.
    """
    data_file_variables = {f: get_valid_columns(f) for f in sorted(glob("data/*.csv"))}

    for seed in range(30):
        for technique in techniques:
            for data_file, columns in data_file_variables.items():
                data = pd.read_csv(data_file)[columns]

                if technique == "HillClimberDiscovery":
                    inferred_dag = run_ctf_discovery(
                        df=data,
                        random_seed=seed,
                    )
                elif technique == "notears":
                    inferred_dag = run_gcastle_discovery(technique=technique, df=data)
                else:
                    for col in data:
                        if pd.api.types.is_bool_dtype(data[col]):
                            data[col] = data[col].astype(int)
                        if not pd.api.types.is_numeric_dtype(data[col]):
                            data[col] = data[col].apply({value: inx for inx, value in enumerate(data[col].unique())})

                    inferred_dag = run_causal_learn_discovery(technique=technique, df=data)

                config_args = {
                    "technique": technique,
                    "data_file": data_file,
                    "data_amount": len(data),
                    "nodes": len(columns),
                    "seed": seed,
                }

                inferred_dag.graph["graph"] |= config_args | {
                    "pass": 0,
                    "fail": 0,
                    "inestimable": 0,
                }
                try:
                    # Do this as a separate step in case the DAG is cyclic - it shouldn't be!
                    inferred_dag.graph["graph"] |= evaluate_dag(inferred_dag, data)

                except (nx.HasACycle, ValueError) as e:
                    if "error" not in inferred_dag.graph["graph"]:
                        inferred_dag.graph["graph"] = config_args | {"error": str(e)}

                # output
                output = os.path.join("results_real", technique, f"{seed}.dot")
                root, _ = os.path.split(output)
                if not os.path.exists(root):
                    os.makedirs(root)
                nx.drawing.nx_pydot.write_dot(inferred_dag, output)


if __name__ == "__main__":
    main()
