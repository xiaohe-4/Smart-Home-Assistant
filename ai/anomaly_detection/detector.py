from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


ANOMALY_FEATURES = [
    "power",
    "rolling_mean",
    "rolling_std",
    "hour",
    "weekday",
    "temperature",
    "occupancy",
]


def train_isolation_forest(frame: pd.DataFrame, model_path: Path) -> dict:
    model = IsolationForest(
        n_estimators=300,
        contamination=0.03,
        random_state=42,
        n_jobs=-1,
    )
    x = frame[ANOMALY_FEATURES]
    model.fit(x)
    scores = -model.decision_function(x)
    payload = {"model": model, "features": ANOMALY_FEATURES}
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(payload, model_path)
    return {
        "model_name": "IsolationForest",
        "samples": int(len(frame)),
        "score_mean": float(np.mean(scores)),
        "score_std": float(np.std(scores)),
    }


def score_frame(frame: pd.DataFrame, model_path: Path) -> pd.DataFrame:
    payload = joblib.load(model_path)
    model = payload["model"]
    scores = -model.decision_function(frame[ANOMALY_FEATURES])
    preds = model.predict(frame[ANOMALY_FEATURES])
    out = frame.copy()
    out["anomaly_score"] = scores
    out["iforest_flag"] = (preds == -1).astype(int)
    return out
