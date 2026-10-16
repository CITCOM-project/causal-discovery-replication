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

data = pd.read_csv("data/foster_2024_carla.csv")


def get_valid_columns(df: pd.DataFrame) -> list[str]:
    """
    Filter out irrelevant and non-usable columns.
    """

    valid_cols = [
        c
        for c in df.columns
        if "Unnamed" not in c  # Errant index columns from saving dataframes
        and "index" not in c  # run indices
        and "id" not in c  # run indices
        and "seed" not in c  # random seeds
        and "version" not in c  # random seeds
        and "weather"
        not in c  # Duplicated columns in one of the CARLA datasets (e.g. cloudiness and weather_cloudiness)
        and df[c].nunique(dropna=False) > 1  # Check unique count without dropping NaNs
        and not df[c].isnull().any()  # Ensure no NaN values in columns
    ]
    return valid_cols


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


seed = 0

training_data = data.loc[data["carla_version"] == 10, valid_cols]
test_data = data.loc[data["carla_version"] == 11, valid_cols]

for technique in techniques:
    if technique == "HillClimberDiscovery":
        inferred_dag = run_ctf_discovery(
            df=training_data,
            random_seed=seed,
        )
    elif technique == "notears":
        inferred_dag = run_gcastle_discovery(technique=technique, df=training_data)
    else:
        for col in training_data:
            if pd.api.types.is_bool_dtype(training_data[col]):
                training_data[col] = training_data[col].astype(int)
            if not pd.api.types.is_numeric_dtype(training_data[col]):
                indices = {value: inx for inx, value in enumerate(training_data[col].unique())}
                training_data[col] = [indices[x] for x in training_data[col]]
        inferred_dag = run_causal_learn_discovery(technique=technique, df=training_data)

    print(evaluate_dag(inferred_dag, test_data))
    print(evaluate_dag(inferred_dag, training_data))
