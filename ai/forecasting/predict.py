from datetime import timedelta

import numpy as np
import pandas as pd

from ai.forecasting.features import FEATURE_COLUMNS, add_lag_features
from ai.forecasting.model import load_model


def recursive_forecast(hourly_df: pd.DataFrame, model_path, horizon_hours: int = 24) -> pd.DataFrame:
    payload = load_model(model_path)
    model = payload["model"]
    feature_cols = list(payload.get("features") or FEATURE_COLUMNS)
    history = hourly_df.sort_values("timestamp").copy().reset_index(drop=True)
    if history.empty:
        return pd.DataFrame(columns=["timestamp", "predicted_power"])

    future_rows = []
    work = history.copy()
    last_ts = work["timestamp"].iloc[-1]
    last_temp = float(work["temperature"].fillna(26).iloc[-1]) if "temperature" in work else 26.0
    last_hum = float(work["humidity"].fillna(55).iloc[-1]) if "humidity" in work else 55.0
    last_occ = float(work["occupancy"].fillna(0).iloc[-1]) if "occupancy" in work else 0.0

    for step in range(1, horizon_hours + 1):
        ts = last_ts + timedelta(hours=step)
        hour = ts.hour
        weekday = ts.weekday()
        is_weekend = int(weekday >= 5)
        occ = last_occ if 7 <= hour <= 23 else max(1.0, last_occ * 0.4)
        row = {
            "timestamp": ts,
            "power": np.nan,
            "energy": np.nan,
            "temperature": last_temp,
            "humidity": last_hum,
            "occupancy": occ,
            "hour": hour,
            "weekday": weekday,
            "is_weekend": is_weekend,
        }
        tmp = pd.concat([work, pd.DataFrame([row])], ignore_index=True)
        featured = add_lag_features(tmp)
        for name in feature_cols:
            if name not in featured.columns:
                featured[name] = 0.0
        features = featured.iloc[[-1]][feature_cols]
        pred = float(model.predict(features)[0])
        pred = max(80.0, pred)
        tmp.loc[tmp.index[-1], "power"] = pred
        work = tmp
        future_rows.append({"timestamp": ts, "predicted_power": pred, "horizon": step})

    return pd.DataFrame(future_rows)
