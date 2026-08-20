from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split


DEVICE_LABELS = {
    "air_conditioner": "空调",
    "refrigerator": "冰箱",
    "water_heater": "热水器",
    "washing_machine": "洗衣机",
    "television": "电视",
    "lighting": "照明",
    "computer": "电脑",
    "other": "其他",
}


def extract_device_windows(energy_df: pd.DataFrame, window_points: int = 12) -> pd.DataFrame:
    rows = []
    energy = energy_df.copy()
    energy["timestamp"] = pd.to_datetime(energy["timestamp"])
    for device_id, group in energy.groupby("device_id"):
        g = group.sort_values("timestamp").reset_index(drop=True)
        device_type = g["device_type"].iloc[0] if "device_type" in g.columns else "other"
        for start in range(0, len(g) - window_points, window_points):
            chunk = g.iloc[start : start + window_points]
            power = chunk["power"].to_numpy()
            running = power > 15
            rows.append(
                {
                    "device_id": int(device_id),
                    "device_type": device_type,
                    "mean_power": float(power.mean()),
                    "peak_power": float(power.max()),
                    "runtime_ratio": float(running.mean()),
                    "power_std": float(power.std()),
                    "start_hour": int(chunk["timestamp"].iloc[0].hour),
                    "cycle_score": float(((power[1:] - power[:-1]) != 0).mean()) if len(power) > 1 else 0.0,
                }
            )
    return pd.DataFrame(rows)


def train_load_classifier(energy_df: pd.DataFrame, model_path: Path) -> dict:
    features = extract_device_windows(energy_df)
    x_cols = ["mean_power", "peak_power", "runtime_ratio", "power_std", "start_hour", "cycle_score"]
    x = features[x_cols]
    y = features["device_type"]
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=42, stratify=y
    )
    clf = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(x_train, y_train)
    pred = clf.predict(x_test)
    report = classification_report(y_test, pred, output_dict=True, zero_division=0)
    payload = {"model": clf, "features": x_cols}
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(payload, model_path)
    return {
        "model_name": "RandomForestClassifier",
        "accuracy": round(float(report["accuracy"]), 4),
        "macro_f1": round(float(report["macro avg"]["f1-score"]), 4),
        "samples": int(len(features)),
    }
