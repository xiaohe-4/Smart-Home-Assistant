from pathlib import Path

import pandas as pd

from ai.anomaly_detection.detector import train_isolation_forest


def prepare_anomaly_frame(
    energy_df: pd.DataFrame,
    env_df: pd.DataFrame,
    behavior_df: pd.DataFrame,
) -> pd.DataFrame:
    energy = energy_df.copy()
    energy["timestamp"] = pd.to_datetime(energy["timestamp"])
    total = (
        energy.groupby("timestamp", as_index=False)["power"]
        .sum()
        .sort_values("timestamp")
        .reset_index(drop=True)
    )
    env = env_df.copy()
    env["timestamp"] = pd.to_datetime(env["timestamp"])
    behavior = behavior_df.copy()
    behavior["timestamp"] = pd.to_datetime(behavior["timestamp"])

    frame = total.merge(
        env[["timestamp", "temperature"]],
        on="timestamp",
        how="left",
    ).merge(
        behavior[["timestamp", "occupancy"]],
        on="timestamp",
        how="left",
    )
    frame["temperature"] = frame["temperature"].ffill().bfill()
    frame["occupancy"] = frame["occupancy"].ffill().bfill().fillna(0)
    frame["hour"] = frame["timestamp"].dt.hour
    frame["weekday"] = frame["timestamp"].dt.weekday
    frame["rolling_mean"] = frame["power"].rolling(12, min_periods=3).mean()
    frame["rolling_std"] = frame["power"].rolling(12, min_periods=3).std().fillna(0)
    return frame.dropna().reset_index(drop=True)


def train_anomaly_model(frame: pd.DataFrame, model_path: Path) -> dict:
    return train_isolation_forest(frame, model_path)
