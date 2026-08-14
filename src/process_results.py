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
    try:
        configuration = dict(map(lambda directory: directory.split("-"), split[len(system) :]))
    except ValueError:
        pass
    configuration = {
        k: float(v) if k not in ["technique", "error"] else v for k, v in (configuration | dag.get_attributes()).items()
    }
    configuration["system"] = system
    configuration["dag_path"] = dag_path

    # Temp hack to normalise test_outcomes
    causal_dag = CausalDAG(dag_path, ignore_cycles=True)
    try:
        causal_dag.datatypes = {node: float for node in causal_dag.nodes}
        num_tests = len(causal_dag.generate_causal_tests())
        if num_tests:
            configuration["pass"] = configuration.get("pass", 0) / num_tests
            configuration["fail"] = configuration.get("fail", 0) / num_tests
            configuration["inestimable"] = configuration.get("inestimable", 0) / num_tests
    except ValueError as e:
        pass
    return configuration


def read_data(data_path: str = None) -> pd.DataFrame:
    if data_path and os.path.exists(data_path):
        data = pd.read_csv(data_path, index_col=0)
    else:
        with Pool() as pool:
            data = pool.map(read_file, tqdm(glob("results/**/*.dot", recursive=True)))
        data = pd.DataFrame(data)
        if data_path:
            data.to_csv(data_path)
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
    return data


def plot_accuracy(df: pd.DataFrame, column: str):
    _, ax = plt.subplots()
    ax.boxplot(df.loc[~df[column].isnull()].groupby("technique")[column].apply(list))
    ax.set_xticklabels(df.groupby("technique").groups.keys())
    ax.tick_params("x", rotation=45, rotation_mode="xtick")
    ax.set_title(column.capitalize())
    plt.tight_layout()
    plt.savefig(f"figures/{column}.png")


if __name__ == "__main__":
    if not os.path.exists("figures"):
        os.mkdir("figures")
    df = read_data("data.csv")
    df = df.loc[df["data"] == 1]
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
