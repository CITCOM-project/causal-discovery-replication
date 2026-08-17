import os
from glob import glob
from itertools import takewhile
from multiprocessing import Pool

import matplotlib.pyplot as plt
import pandas as pd
import pydot
from causal_testing.specification.causal_dag import CausalDAG
from tqdm import tqdm

plt.style.use("ggplot")


def read_file(dag_path):
    split = os.path.normpath(os.path.splitext(dag_path)[0]).split(os.sep)
    system = list(takewhile(lambda directory: not directory.startswith("technique-"), split))
    dag = pydot.graph_from_dot_file(dag_path)[0]
    configuration = dict(map(lambda directory: directory.split("-"), split[len(system) :]))
    configuration = {
        k: float(v) if k not in ["technique", "error"] else v for k, v in (configuration | dag.get_attributes()).items()
    }
    configuration["system"] = system
    configuration["dag_path"] = dag_path

    return configuration


def read_data(data_path: str = None) -> pd.DataFrame:
    if data_path and os.path.exists(data_path):
        data = pd.read_csv(data_path, index_col=0)
    else:
        with Pool() as pool:
            data = pool.map(read_file, tqdm(glob("results_synthetic/**/*.dot", recursive=True)))
        data = pd.DataFrame(data)

        data["directional_sensitivity"] = data["directional_true_positives"] / (
            data["directional_true_positives"] + data["directional_false_negatives"]
        )
        data["non_directional_sensitivity"] = data["non_directional_true_positives"] / (
            data["non_directional_true_positives"] + data["non_directional_false_negatives"]
        )
        data["directional_specificity"] = data["directional_true_negatives"] / (
            data["directional_true_negatives"] + data["directional_false_positives"]
        )
        data["non_directional_specificity"] = data["non_directional_true_negatives"] / (
            data["non_directional_true_negatives"] + data["non_directional_false_positives"]
        )
        data["directional_bcr"] = (data["directional_sensitivity"] + data["directional_specificity"]) / 2
        data["non_directional_bcr"] = (data["non_directional_sensitivity"] + data["non_directional_specificity"]) / 2

        # Set "pass", "fail", and "inestimable" to NaN if there was an error
        data.loc[data["error"].notna(), ["pass", "fail", "inestimable"]] = None

        # Set classification metrics to 0 if there was an error
        data.loc[
            data["error"].notna(),
            [
                f"{directional}_{metric}"
                for directional in ["directional", "non_directional"]
                for metric in ["sensitivity", "specificity", "bcr"]
            ],
        ] = 0
        if data_path:
            data.to_csv(data_path)

    return data


def plot_accuracy(df: pd.DataFrame, column: str):
    _, ax = plt.subplots()
    ax.boxplot(df.loc[~df[column].isnull()].groupby("technique")[column].apply(list))
    ax.set_xticklabels(df.groupby("technique").groups.keys())
    ax.tick_params("x", rotation=45, rotation_mode="xtick")
    ax.set_title(column.capitalize())
    ax.set_ylim(0, 1)
    plt.tight_layout()
    plt.savefig(f"figures/{column}.png")


if __name__ == "__main__":
    if not os.path.exists("figures"):
        os.mkdir("figures")
    df = read_data("data.csv")
    df = df.loc[df["data"] == 100]
    print(df)
    print(df.dtypes)
    plot_accuracy(df, "pass")
    plot_accuracy(df, "fail")
    plot_accuracy(df, "inestimable")
    plot_accuracy(df, "directional_sensitivity")
    plot_accuracy(df, "non_directional_sensitivity")
    plot_accuracy(df, "directional_specificity")
    plot_accuracy(df, "non_directional_specificity")
    plot_accuracy(df, "directional_bcr")
    plot_accuracy(df, "non_directional_bcr")
