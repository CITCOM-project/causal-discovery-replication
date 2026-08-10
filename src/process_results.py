import os
from glob import glob
from itertools import takewhile

import matplotlib.pyplot as plt
import pandas as pd
import pydot
from tqdm import tqdm

plt.style.use("ggplot")


def read_data(data_path: str = None) -> pd.DataFrame:
    if data_path and os.path.exists(data_path):
        data = pd.read_csv(data_path, index_col=0)
    else:
        data = []
        for dag_path in tqdm(glob("results/**/*.dot", recursive=True)):
            split = os.path.normpath(os.path.splitext(dag_path)[0]).split(os.sep)
            system = list(takewhile(lambda directory: not directory.startswith("technique-"), split))
            dag = pydot.graph_from_dot_file(dag_path)[0]
            try:
                configuration = dict(map(lambda directory: directory.split("-"), split[len(system) :]))
            except ValueError:
                print(dag_path)
                continue
            configuration = {k: float(v) if k != "technique" else v for k, v in configuration.items()}
            configuration["system"] = system
            configuration |= dag.get_attributes()
            configuration["dag_path"] = dag_path
            data.append(configuration)
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
