import os

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from discovery import (
    dag_confusion_matrix,
    dag_difference_metrics,
    evaluate_dag,
    run_causal_learn_discovery,
    run_ctf_discovery,
    run_gcastle_discovery,
    techniques,
)
from process_results import BLUE, RED, plot_grouped_boxplot, technique_labels

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

data = pd.read_csv("data/foster_2024_carla.csv")


valid_cols = [
    # weather
    "cloudiness",
    "precipitation",
    "precipitation_deposits",
    "sun_altitude_angle",
    "sun_azimuth_angle",
    "wind_intensity",
    "ego_vehicle",
    "npc_vehicles",
    "pedestrians",
    "route_length",
    "outside_route_lanes",
    "infraction_penalty",
    "simulation_time",
    "system_time",
    "completion_score",
    "driving_score",
]

for col in data:
    if pd.api.types.is_bool_dtype(data[col]):
        data[col] = data[col].astype(int)
    if not pd.api.types.is_numeric_dtype(data[col]):
        indices = {value: inx for inx, value in enumerate(data[col].unique())}
        data[col] = [indices[x] for x in data[col]]

training_data = data.loc[data["carla_version"] == 10, valid_cols]
test_data = data.loc[data["carla_version"] == 11, valid_cols]

if not os.path.exists("carla_results.csv"):
    runs = []
    for technique in techniques:
        if technique == "HillClimberDiscovery":
            for seed in range(30):
                inferred_dag = run_ctf_discovery(
                    df=training_data,
                    random_seed=seed,
                )
                runs.append(
                    {"technique": technique}
                    | {f"training_{k}": v for k, v in evaluate_dag(inferred_dag, test_data).items()}
                    | {f"regression_{k}": v for k, v in evaluate_dag(inferred_dag, training_data).items()}
                )
        elif technique == "notears":
            inferred_dag = run_gcastle_discovery(technique=technique, df=training_data)
            runs.append(
                {"technique": technique}
                | {f"training_{k}": v for k, v in evaluate_dag(inferred_dag, test_data).items()}
                | {f"regression_{k}": v for k, v in evaluate_dag(inferred_dag, training_data).items()}
            )
        else:
            inferred_dag = run_causal_learn_discovery(technique=technique, df=training_data)
            runs.append(
                {"technique": technique}
                | {f"training_{k}": v for k, v in evaluate_dag(inferred_dag, test_data).items()}
                | {f"regression_{k}": v for k, v in evaluate_dag(inferred_dag, training_data).items()}
            )

    df = pd.DataFrame(runs)
    df.to_csv("carla_results.csv")
else:
    df = pd.read_csv("carla_results.csv")

df["technique"] = df["technique"].replace(technique_labels)
version_labels = {"training_pass": "v0.9.10.1", "regression_pass": "v0.9.11"}
plot_grouped_boxplot(
    groups=np.array([df.groupby("technique", sort=False)[version].apply(list) for version in version_labels]),
    savepath="figures/carla.pgf",
    colours=[RED, BLUE],
    xticklabels=df["technique"].unique(),
    labels=[version_labels[v] for v in version_labels],
    xlabel="CARLA version",
    ylabel="Pass Rate",
)
