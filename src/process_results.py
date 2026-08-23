import os
from glob import glob
from multiprocessing import Pool

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pydot
from scipy.stats import spearmanr
from tqdm import tqdm

plt.style.use("ggplot")


def read_file(dag_path):
    split = os.path.normpath(os.path.splitext(dag_path)[0]).split(os.sep)
    dag = pydot.graph_from_dot_file(dag_path)[0]
    configuration = {
        k: float(v) if k not in ["technique", "error", "output"] else v for k, v in dag.get_attributes().items()
    }
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
        # data.loc[data["error"].notna(), ["pass", "fail", "inestimable"]] = None

        # Set classification metrics to 0 if there was an error
        # data.loc[
        #     data["error"].notna(),
        #     [
        #         f"{directional}_{metric}"
        #         for directional in ["directional", "non_directional"]
        #         for metric in ["sensitivity", "specificity", "bcr"]
        #     ],
        # ] = 0
        if data_path:
            data.to_csv(data_path)

    return data


def plot_accuracy(df: pd.DataFrame, column: str):
    _, ax = plt.subplots()
    ax.boxplot(
        df.loc[~df[column].isnull()].groupby("technique")[column].apply(list),
        tick_labels=df.loc[~df[column].isnull()].groupby("technique").groups.keys(),
    )
    ax.tick_params("x", rotation=45, rotation_mode="xtick")
    ax.set_title(column.capitalize())
    ax.set_ylim(0, 1)
    plt.tight_layout()
    plt.savefig(f"figures/{column}.png")


def scatter(df: pd.DataFrame, x_column: str, y_column: str):
    _, ax = plt.subplots()
    ax.scatter(df[x_column], df[y_column])
    ax.set_xlabel(x_column)
    ax.set_ylabel(y_column)
    plt.tight_layout()
    plt.savefig(f"figures/{x_column}_{y_column}.png")
    res, p_value = spearmanr(df[x_column], df[y_column], nan_policy="omit")
    print("Statistic", res, "p-value", p_value)
    print(df[[x_column, y_column]])


def scatters(df: pd.DataFrame, group_by: str, x_column: str, y_column: str):
    _, ax = plt.subplots()
    for label, group in df.groupby(group_by):
        ax.scatter(df.loc[df[group_by] == label, x_column], df.loc[df[group_by] == label, y_column], label=label)
    ax.set_xlabel(x_column)
    ax.set_ylabel(y_column)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"figures/{x_column}_{y_column}.png")
    res, p_value = spearmanr(df[x_column], df[y_column], nan_policy="omit")


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


if __name__ == "__main__":
    if not os.path.exists("figures"):
        os.mkdir("figures")
    df = read_data("data.csv")

    # with open("synthetic_configurations.txt") as f:
    #     for line in f:
    #         line = line.strip()
    #         args = {k: v for k, v in chunks(line.split(" "), 2)}
    #         if not ((df["seed"] == int(args["-s"])) & (df["technique"] == args["-t"])).any():
    #             print(
    #                 "sbatch --time=04:00:00 --nodes=1 --ntasks=1 --cpus-per-task=1 --mem=8G apptainer exec apptainer.sif python src/synthetic_discovery.py",
    #                 line,
    #             )

    plot_accuracy(df, "pass")
    plot_accuracy(df, "fail")
    plot_accuracy(df, "inestimable")
    plot_accuracy(df, "directional_sensitivity")
    plot_accuracy(df, "non_directional_sensitivity")
    plot_accuracy(df, "directional_specificity")
    plot_accuracy(df, "non_directional_specificity")
    plot_accuracy(df, "directional_bcr")
    plot_accuracy(df, "non_directional_bcr")

    df["normalised_edit_distance"] = df["edit_distance"] / (df["true_edges"] + df["inferred_edges"])
    df["normalised_structural_hamming"] = df["structural_hamming"] / (df["true_edges"] + df["inferred_edges"])
    df["normalised_structural_intervention"] = df["structural_intervention"] / df["nodes"] * (df["nodes"] - 1)

    scatter(df, "directional_sensitivity", "pass")
    scatter(df, "directional_specificity", "pass")
    scatter(df, "normalised_edit_distance", "pass")
    scatter(df, "normalised_structural_hamming", "pass")
    scatter(df, "directional_sensitivity", "normalised_structural_hamming")
    scatter(df, "directional_sensitivity", "structural_hamming")
    scatter(df, "normalised_structural_intervention", "pass")

    # scatter(df, "nodes", "edit_distance")
    # scatter(df, "nodes", "structural_hamming")

    scatters(df, "technique", "data_amount", "pass")
    scatters(df, "technique", "nodes", "pass")
    scatters(df, "technique", "edge_probability", "pass")
    scatters(df, "technique", "conditional_probability", "pass")
