import os
from glob import glob
from multiprocessing import Pool

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pydot
from scikit_posthocs import posthoc_nemenyi_friedman
from scipy.stats import friedmanchisquare, spearmanr
from tqdm import tqdm

plt.style.use("ggplot")

mpl.use("pgf")

# 2. Configure Matplotlib to use LaTeX for text rendering
mpl.rcParams.update(
    {
        "pgf.texsystem": "pdflatex",  # or "xelatex", "lualatex"
        "text.usetex": True,  # Enables TeX parsing for all text elements
        "font.family": "serif",  # Matches LaTeX default serif font
        "pgf.preamble": r"\providecommand{\toolname}{\textsc{hillClimber}}",
        # "pgf.preamble": "\n".join(
        #     [  # Optional: load custom TeX packages
        #         r"\usepackage[utf8]{inputenc}",
        #         r"\usepackage[T1]{fontenc}",
        #     ]
        # ),
    }
)

RED = "#D55E00"
BLUE = "#0072B2"
GREEN = "#009E73"
MAGENTA = "#CC79A7"

technique_colours = {r"\toolname": RED, "GES": BLUE, "PC": GREEN, "NOTEARS": MAGENTA}
technique_labels = {"HillClimberDiscovery": r"\toolname", "ges": "GES", "pc": "PC", "notears": "NOTEARS"}


def compute_stats(df, column, save_path, p_alpha=0.05, low_is_good=False):
    # Reshape from Long to Wide Format
    df_wide = df[["seed", "technique", column]].pivot(index="seed", columns="technique", values=column)
    ranked_medians = df_wide.median().sort_values(ascending=low_is_good)

    print("=" * 30, column, "=" * 30)
    print(ranked_medians.round(3))

    # Friedman Test
    stat, p_value = friedmanchisquare(*[df_wide[col] for col in df_wide.columns])

    print(f"Friedman Test Statistic: {stat:.3e} p-value: {p_value:.3e}\n")

    # Post-Hoc Nemenyi Test
    if p_value < p_alpha:
        print("Overall significance detected (p < 0.05). Running Nemenyi post-hoc test...\n")

        # Calculate Nemenyi p-values matrix
        nemenyi_matrix = posthoc_nemenyi_friedman(df_wide)

        print("Nemenyi Post-Hoc Pairwise p-value Matrix:")
        print(nemenyi_matrix.round(4))

        ranked_medians = ranked_medians.index

        # Extract specific comparison between top two techniques
        print(
            f"\np-value between best ({ranked_medians[0]}) and 2nd best ({ranked_medians[1]}): {nemenyi_matrix.loc[ranked_medians[0], ranked_medians[1]]:.3e}"
        )
    print("=" * 80)


def read_file(dag_path):
    split = os.path.normpath(os.path.splitext(dag_path)[0]).split(os.sep)
    dag = pydot.graph_from_dot_file(dag_path)[0]
    configuration = {
        k: float(v) if k not in ["technique", "error", "output", "reference_output"] else v
        for k, v in dag.get_attributes().items()
    }
    configuration["dag_path"] = dag_path
    configuration["mutated"] = "mutated" in dag_path
    if "killed_mutant" in configuration:
        configuration["killed_mutant"] = configuration["killed_mutant"] == "true"

    return configuration


def read_data(data_path: str = None) -> pd.DataFrame:
    if data_path and os.path.exists(data_path):
        data = pd.read_csv(data_path, index_col=0)
    else:
        with Pool() as pool:
            data = pool.map(read_file, tqdm(glob("results_synthetic/**/*.dot", recursive=True)))
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
    data["normalised_pass"] = data["pass"] / data["reference_pass"]
    data["mutation_score"] = data["killed_mutants"] / data["total_mutants"]
    data["tested_mutation_score"] = data["tested_mutants"] / data["total_mutants"]
    data["ambiguous_mutation_score"] = data["ambiguous_mutants"] / data["total_mutants"]
    data["normalised_structural_hamming"] = data["structural_hamming"] / (((data["nodes"] * (data["nodes"] - 1))))
    data["normalised_structural_intervention"] = data["structural_intervention"] / (
        ((data["nodes"] * (data["nodes"] - 1)))
    )
    data["pass_rate"] = data["pass"]  # * 100
    data.rename({"conditional_probability": "probability_of_conditional"}, axis=1, inplace=True)

    # data = data.sort_values(["technique", "seed"])
    data["technique"] = data["technique"].replace(technique_labels)

    return data


def plot_accuracy(df: pd.DataFrame, column: str, label: str = None, extension: str = "pgf"):
    _, ax = plt.subplots()

    compute_stats(df, column, f"stats/{column}.tex")
    ax.boxplot(
        df.groupby("technique", sort=False)[column].apply(list),
        tick_labels=df.loc[~df[column].isnull()].groupby("technique", sort=False).groups.keys(),
    )
    ax.tick_params("x", rotation=45, rotation_mode="xtick")
    ax.set_ylabel(label if label else column.capitalize().replace("_", " "))
    if df[column].between(0, 1).all():
        ax.set_ylim(-0.01, 1.01)
    plt.tight_layout()
    # plt.savefig(f"figures/{column}.png")
    plt.savefig(f"figures/{column}.{extension}", bbox_inches="tight")
    plt.close()


def color(colour, flierprops=None):
    if flierprops is None:
        flierprops = {}
    return {
        "boxprops": {"color": colour},
        "capprops": {"color": colour},
        "whiskerprops": {"color": colour},
        "flierprops": {"color": colour, "markeredgecolor": colour} | flierprops,
        "medianprops": {"color": colour},
    }


def plot_grouped_boxplot(
    groups,
    savepath=None,
    width=0.6,
    labels=None,
    colours=None,
    markers=None,
    title=None,
    xticklabels=None,
    xlabel=None,
    ylabel=None,
    ax=None,
    showfliers=True,
    yticks=None,
    offset=0,
    figsize=(10, 6),
    legend=True,
):
    if ax is None:
        _, ax = plt.subplots(figsize=figsize)
    positions = max(len(x) for x in groups)
    plots = len(groups)
    if isinstance(labels, list) and len(labels) != plots:
        raise ValueError(
            f"If providing labels, please ensure that you provide as many as you have plots ({len(labels)})"
        )
    if isinstance(colours, list) and len(colours) != plots:
        raise ValueError("If providing colours, please ensure that you provide as many as you have plots")
    if isinstance(showfliers, bool):
        showfliers = [showfliers] * len(groups)
    if isinstance(showfliers, list) and len(showfliers) != plots:
        raise ValueError("If providing showfliers, please ensure that you provide as many as you have plots")
    for i, boxes in enumerate(groups):
        marker = markers[i] if isinstance(markers, list) else markers if markers is not None else "o"

        ax.boxplot(
            boxes,
            positions=np.array(range(positions)) * (plots + 1) + i + offset,
            widths=width,
            showfliers=showfliers[i],
            label=labels[i] if labels is not None else None,
            **color(
                colours[i] if colours is not None else None,
                flierprops={"marker": marker, "markersize": width * 2},
            ),
        )

    if xticklabels is not None:
        ax.set_xticks(
            np.array(range(len(xticklabels))) * (plots + 1) + (((plots + (plots / 2) - 1) * width) / 2),
            xticklabels,
        )
    if labels is not None and legend:
        ax.legend()
    if title is not None:
        ax.set_title(title)
    if xlabel is not None:
        ax.set_xlabel(xlabel)
    if ylabel is not None:
        ax.set_ylabel(ylabel)
    if yticks is not None:
        ax.set_yticks(yticks)
    if savepath is not None:
        plt.savefig(savepath, bbox_inches="tight", pad_inches=0)
        plt.clf()


def scatter(df: pd.DataFrame, x_column: str, y_column: str):
    res, p_value = spearmanr(df[x_column], df[y_column], nan_policy="omit")

    _, ax = plt.subplots()
    ax.scatter(df[x_column], df[y_column])
    ax.set_xlabel(x_column)
    ax.set_ylabel(y_column)
    ax.set_title(f"spearmanr={round(res,2)} ({round(p_value, 2)})")
    plt.tight_layout()
    # plt.savefig(f"figures/{x_column}_{y_column}.png")
    plt.savefig(f"figures/{x_column}_{y_column}.pgf", bbox_inches="tight")
    print("Statistic", res, "p-value", p_value)
    print(df[[x_column, y_column]])
    plt.close()


def scatters(
    df: pd.DataFrame, group_by: str, x_column: str, y_column: str, extension: str = "pgf", plot_best_fit=False
):
    print("=" * 20, x_column, y_column, "=" * 20)

    _, ax = plt.subplots()
    stats = {}
    for label, group in df.groupby(group_by):
        ax.scatter(group[x_column], group[y_column], label=label, color=technique_colours[label], alpha=0.5)

        if plot_best_fit:
            # Plot the line of best fit
            line_of_best_fit = np.poly1d(np.polyfit(group[x_column], group[y_column], 1))

            plt.plot(
                group[x_column].sort_values(),
                line_of_best_fit(group[x_column].sort_values()),
                color=technique_colours[label],
            )

        res, p_value = spearmanr(group[x_column], group[y_column], nan_policy="omit")
        stats[label] = {"Statistic": res, "p-value": f"{p_value:.3e}"}
    stats = pd.DataFrame(stats).T.sort_values("Statistic")
    print(stats)
    stats.to_latex(f"statistics/{x_column}_{y_column}.tex")

    ax.set_xlabel(x_column.capitalize().replace("_", " "))
    ax.set_ylabel(y_column.capitalize().replace("_", " "))
    plt.legend()
    plt.tight_layout()
    # plt.savefig(f"figures/{x_column}_{y_column}.png")
    plt.savefig(f"figures/{x_column}_{y_column}.{extension}", bbox_inches="tight")
    plt.close()
    print("=" * 80)


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


if __name__ == "__main__":
    if not os.path.exists("figures"):
        os.mkdir("figures")
    if not os.path.exists("statistics"):
        os.mkdir("statistics")
    df = read_data("data.csv")

    # Check we have all the results
    for technique, group in df.groupby("technique"):
        for seed in range(250):
            if seed not in map(int, group["seed"]):
                print(technique, seed)

    # RQ1
    print("RQ1")
    plot_accuracy(df, "mutation_score", "Mutation Score")
    for feature in ["nodes", "data_amount", "probability_of_conditional"]:
        scatters(df, "technique", feature, "mutation_score")

    # RQ2
    print("\nRQ2")
    measure_labels = {
        "pass_rate": "Pass rate",
        "normalised_structural_intervention": "Normalised SID",
        "normalised_structural_hamming": "Normalised SHD",
        "directional_bcr": "BCR",
    }
    measures = [
        "pass_rate",
        "normalised_structural_intervention",
        "normalised_structural_hamming",
        "directional_bcr",
    ]
    plot_grouped_boxplot(
        groups=np.array([df.groupby("technique", sort=False)[measure].apply(list) for measure in measures]).T,
        savepath="figures/accuracy_metrics.pgf",
        colours=[technique_colours[t] for t in df["technique"].unique()],
        labels=df["technique"].unique(),
        xticklabels=[measure_labels[m] for m in measures],
        xlabel="Metric",
        ylabel="Value",
    )
    stats = []

    short_feature_labels = {
        "nodes": "Nodes",
        "data_amount": "Data",
        "probability_of_conditional": "$p_c$",
    }
    for technique, group in df.groupby("technique"):
        for measure in [
            "pass_rate",
            "normalised_structural_intervention",
            "normalised_structural_hamming",
            "directional_bcr",
        ]:
            for feature in ["nodes", "data_amount", "probability_of_conditional"]:
                statistic, p_value = spearmanr(group[feature], group[measure])
                stats.append(
                    {
                        "technique": technique,
                        "feature": short_feature_labels[feature],
                        "measure": measure_labels[measure],
                        "statistic": statistic,
                        "p-value": p_value,
                    }
                )
    stats_df = pd.DataFrame(stats)

    table_df = stats_df.pivot(
        index="technique",
        columns=["measure", "feature"],
        values="statistic",  # or format statistic and p-value together
    )

    table_df.style.format(precision=3).to_latex(  # Format float decimal places
        buf="statistics/measure_correlations.tex",
        hrules=True,  # Enables booktabs rules (\toprule, \midrule, \bottomrule)
    )

    # RQ2
    print("\nRQ3")
    stats = []
    for measure in [
        "normalised_structural_intervention",
        "normalised_structural_hamming",
        "directional_bcr",
    ]:
        scatters(df, "technique", measure, "pass_rate")
        for technique, group in df.groupby("technique", sort=False):
            statistic, p_value = spearmanr(group[measure], group["pass_rate"])
            stats.append(
                {
                    "technique": technique,
                    "measure": measure_labels[measure],
                    "statistic": statistic,
                    "p-value": p_value,
                }
            )

    table_df = pd.DataFrame(stats).pivot(
        index="technique",
        columns=["measure"],
        values="statistic",  # or format statistic and p-value together
    )

    table_df.style.format(precision=3).to_latex(  # Format float decimal places
        buf="statistics/pass_correlations.tex",
        hrules=True,  # Enables booktabs rules (\toprule, \midrule, \bottomrule)
    )

    # Runtime
    plot_accuracy(df.assign(time=np.log(df["time"])), "time", "log(runtime)")
    print(df.groupby("technique")["time"].median().sort_values())

    print(sorted(df.columns))
