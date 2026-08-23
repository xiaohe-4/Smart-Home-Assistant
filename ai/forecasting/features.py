from datetime import datetime, timedelta

import numpy as np
import pandas as pd


INTERVAL_MINUTES = 5
POINTS_PER_HOUR = 60 // INTERVAL_MINUTES
HOURS_PER_DAY = 24
POINTS_PER_DAY = HOURS_PER_DAY * POINTS_PER_HOUR


FEATURE_COLUMNS = [
    "lag_1",
    "lag_2",
    "lag_3",
    "lag_6",
    "lag_12",
    "lag_24",
    "rolling_mean_1h",
    "rolling_mean_3h",
    "rolling_mean_6h",
    "rolling_mean_24h",
    "temperature",
    "humidity",
    "occupancy",
    "hour",
    "weekday",
    "is_weekend",
]

DEGRADED_FEATURE_COLUMNS = [c for c in FEATURE_COLUMNS if c not in {"temperature", "humidity", "occupancy"}]


def hour_block_energy(power_w: float, minutes: int = INTERVAL_MINUTES) -> float:
    return power_w / 1000.0 * (minutes / 60.0)


def build_hourly_frame(
    energy_df: pd.DataFrame,
    env_df: pd.DataFrame,
    behavior_df: pd.DataFrame,
) -> pd.DataFrame:
    energy = energy_df.copy()
    energy["timestamp"] = pd.to_datetime(energy["timestamp"])
    energy["hour"] = energy["timestamp"].dt.floor("h")
    hourly_power = (
        energy.groupby("hour", as_index=False)["power"]
        .sum()
        .rename(columns={"hour": "timestamp", "power": "power"})
    )
    # 同一时刻多设备功率已在 groupby 中求和；再按小时取平均功率
    hourly = (
        energy.assign(hour_ts=energy["timestamp"].dt.floor("h"))
        .groupby("hour_ts", as_index=False)
        .agg(energy=("energy", "sum"), power=("power", "mean"))
        .rename(columns={"hour_ts": "timestamp"})
    )
    total_power = (
        energy.assign(hour_ts=energy["timestamp"].dt.floor("h"))
        .groupby(["hour_ts", "timestamp"], as_index=False)["power"]
        .sum()
        .groupby("hour_ts", as_index=False)["power"]
        .mean()
        .rename(columns={"hour_ts": "timestamp"})
    )
    hourly = hourly.drop(columns=["power"]).merge(total_power, on="timestamp")

    env = env_df.copy()
    env["timestamp"] = pd.to_datetime(env["timestamp"]).dt.floor("h")
    env_hourly = env.groupby("timestamp", as_index=False)[["temperature", "humidity"]].mean()

    behavior = behavior_df.copy()
    behavior["timestamp"] = pd.to_datetime(behavior["timestamp"]).dt.floor("h")
    occ = behavior.groupby("timestamp", as_index=False)["occupancy"].mean()

    frame = hourly.merge(env_hourly, on="timestamp", how="left").merge(occ, on="timestamp", how="left")
    frame = frame.sort_values("timestamp").reset_index(drop=True)
    frame["temperature"] = frame["temperature"].ffill().bfill().fillna(26.0)
    frame["humidity"] = frame["humidity"].ffill().bfill().fillna(55.0)
    frame["occupancy"] = frame["occupancy"].ffill().bfill().fillna(0)
    frame["hour"] = frame["timestamp"].dt.hour
    frame["weekday"] = frame["timestamp"].dt.weekday
    frame["is_weekend"] = (frame["weekday"] >= 5).astype(int)
    return frame


def add_lag_features(frame: pd.DataFrame) -> pd.DataFrame:
    df = frame.copy()
    for lag in (1, 2, 3, 6, 12, 24):
        df[f"lag_{lag}"] = df["power"].shift(lag)
    df["rolling_mean_1h"] = df["power"].shift(1).rolling(1).mean()
    df["rolling_mean_3h"] = df["power"].shift(1).rolling(3).mean()
    df["rolling_mean_6h"] = df["power"].shift(1).rolling(6).mean()
    df["rolling_mean_24h"] = df["power"].shift(1).rolling(24).mean()
    return df.dropna().reset_index(drop=True)


def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mae = float(np.mean(np.abs(y_true - y_pred)))
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    denom = np.clip(np.abs(y_true), 1e-6, None)
    mape = float(np.mean(np.abs((y_true - y_pred) / denom)) * 100)
    ss_res = float(np.sum((y_true - y_pred) ** 2))
    ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))
    r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0
    return {
        "MAE": round(mae, 4),
        "RMSE": round(rmse, 4),
        "MAPE": round(mape, 4),
        "R2": round(r2, 4),
    }


def next_timestamps(last_ts: datetime, hours: int) -> list[datetime]:
    return [last_ts + timedelta(hours=i + 1) for i in range(hours)]
