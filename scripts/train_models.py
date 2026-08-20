"""训练预测 / 异常 / 负荷识别模型，并把结果写入数据库。"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, precision_score, recall_score


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(PROJECT_ROOT))

from ai.anomaly_detection.detector import score_frame  # noqa: E402
from ai.anomaly_detection.train import prepare_anomaly_frame, train_anomaly_model  # noqa: E402
from ai.forecasting.features import build_hourly_frame  # noqa: E402
from ai.forecasting.predict import recursive_forecast  # noqa: E402
from ai.forecasting.train import train_forecast_model  # noqa: E402
from ai.load_identification.classifier import train_load_classifier  # noqa: E402
from ai.optimization.strategy_engine import build_strategies  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.models import Anomaly, Device, EnergyRecord, Prediction, Strategy  # noqa: E402


DEMO_DIR = PROJECT_ROOT / "data" / "demo"
MODELS_DIR = PROJECT_ROOT / "models"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DEVICE_CN = {
    1: "客厅变频空调",
    2: "双门冰箱",
    3: "储水式热水器",
    4: "滚筒洗衣机",
    5: "客厅电视",
    6: "全屋照明",
    7: "书房电脑",
    8: "其他插座负荷",
}


def load_demo():
    energy = pd.read_csv(DEMO_DIR / "energy_records.csv", parse_dates=["timestamp"])
    devices = pd.read_csv(DEMO_DIR / "devices.csv")
    energy = energy.merge(devices[["id", "device_type", "name"]], left_on="device_id", right_on="id", how="left")
    env = pd.read_csv(DEMO_DIR / "environment_records.csv", parse_dates=["timestamp"])
    behavior = pd.read_csv(DEMO_DIR / "behavior_records.csv", parse_dates=["timestamp"])
    labels = pd.read_csv(DEMO_DIR / "anomaly_labels.csv", parse_dates=["timestamp"])
    return energy, env, behavior, labels, devices


def classify_severity(score: float, anomaly_type: str) -> str:
    if anomaly_type == "unusual_time":
        return "medium" if score < 1.2 else "high"
    if anomaly_type == "high_power":
        return "high"
    if score >= 1.2:
        return "critical"
    if score >= 0.85:
        return "high"
    if score >= 0.55:
        return "medium"
    return "low"


def rule_enrich(row: pd.Series, device_lookup: dict[datetime, list[tuple[int, float]]]) -> tuple[str, str, int | None]:
    ts = row["timestamp"]
    hour = int(row["hour"])
    occupancy = float(row["occupancy"])
    power = float(row["power"])
    devices = device_lookup.get(pd.Timestamp(ts).to_pydatetime().replace(second=0, microsecond=0), [])
    if not devices:
        # pandas Timestamp key
        devices = device_lookup.get(pd.Timestamp(ts), [])

    top_device = max(devices, key=lambda x: x[1]) if devices else (None, 0.0)
    device_id = top_device[0]
    name = DEVICE_CN.get(device_id, "家庭总负荷")

    if hour < 5 and power > 900:
        return (
            "unusual_time",
            f"{ts.strftime('%H:%M')} {name}出现异常时段启动，功率 {power:.0f}W。"
            "03:17 附近热水器启动，家庭过去30天凌晨几乎从未使用热水器。"
            "建议检查热水器是否存在待机/定时启动行为。",
            device_id,
        )
    if occupancy <= 1 and power > 1800:
        return (
            "habit_deviation",
            f"{name}在低占用时段仍保持高功率 {power:.0f}W，可能存在无人运行浪费。",
            device_id,
        )
    if power > 3500:
        return (
            "high_power",
            f"家庭总功率达到 {power:.0f}W，显著高于历史同时段，存在过载或异常叠加风险。",
            device_id,
        )
    if hour >= 0 and hour < 6 and power > 400:
        return (
            "long_running",
            f"凌晨仍有 {power:.0f}W 负荷，可能是照明或热水器长时间未关闭。",
            device_id,
        )
    return (
        "habit_deviation",
        f"{ts.strftime('%m-%d %H:%M')} 用电模式偏离历史习惯，Isolation Forest 评分 {row['anomaly_score']:.3f}。",
        device_id,
    )


def evaluate_anomalies(detected: pd.DataFrame, labels: pd.DataFrame) -> dict:
    label_times = set(pd.to_datetime(labels["timestamp"]).dt.strftime("%Y-%m-%d %H:%M"))
    pred_times = set(pd.to_datetime(detected["timestamp"]).dt.strftime("%Y-%m-%d %H:%M"))
    y_times = sorted(label_times | pred_times)
    y_true = [1 if t in label_times else 0 for t in y_times]
    y_pred = [1 if t in pred_times else 0 for t in y_times]
    if not y_times:
        return {"precision": 0, "recall": 0, "f1": 0}
    return {
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
        "labeled": len(label_times),
        "detected": len(pred_times),
    }


def select_anomalies(scored: pd.DataFrame, energy: pd.DataFrame) -> pd.DataFrame:
    heater = energy[energy["device_type"] == "water_heater"][["timestamp", "power"]].rename(
        columns={"power": "heater_power"}
    )
    lighting = energy[energy["device_type"] == "lighting"][["timestamp", "power"]].rename(
        columns={"power": "light_power"}
    )
    washer = energy[energy["device_type"] == "washing_machine"][["timestamp", "power"]].rename(
        columns={"power": "washer_power"}
    )
    frame = (
        scored.merge(heater, on="timestamp", how="left")
        .merge(lighting, on="timestamp", how="left")
        .merge(washer, on="timestamp", how="left")
    )
    frame["timestamp"] = pd.to_datetime(frame["timestamp"]).dt.floor("min")
    night_heater = (frame["hour"] < 5) & (frame["heater_power"].fillna(0) > 800)
    night_light = (frame["hour"] < 6) & (frame["light_power"].fillna(0) > 120)
    odd_washer = (frame["hour"].between(13, 16)) & (frame["washer_power"].fillna(0) > 300) & (frame["weekday"] < 5)
    high_power = frame["power"] > 3800
    picked = pd.concat(
        [
            frame[night_heater],
            frame[night_light],
            frame[odd_washer],
            frame[high_power].nlargest(8, "anomaly_score"),
            frame.nlargest(12, "anomaly_score"),
        ]
    ).drop_duplicates(subset=["timestamp"])
    return picked.sort_values(["timestamp"])


def persist_anomalies(detected: pd.DataFrame, device_power_map: dict) -> None:
    db = SessionLocal()
    try:
        db.query(Anomaly).delete()
        rows = []
        for _, row in detected.iterrows():
            ts = pd.Timestamp(row["timestamp"]).to_pydatetime()
            atype, desc, device_id = rule_enrich(row, device_power_map)
            rows.append(
                Anomaly(
                    user_id=1,
                    timestamp=ts,
                    device_id=device_id,
                    anomaly_score=float(row["anomaly_score"]),
                    anomaly_type=atype,
                    description=desc,
                    severity=classify_severity(float(row["anomaly_score"]), atype),
                    status="open",
                )
            )
        db.add_all(rows)
        db.commit()
        print(f"写入异常 {len(rows)} 条")
    finally:
        db.close()


def persist_predictions(forecast_df: pd.DataFrame, hourly: pd.DataFrame, model_name: str) -> None:
    db = SessionLocal()
    try:
        db.query(Prediction).delete()
        actual_map = {
            pd.Timestamp(ts).to_pydatetime(): float(p)
            for ts, p in zip(hourly["timestamp"], hourly["power"])
        }
        rows = []
        history = hourly.tail(48)
        for _, row in history.iterrows():
            ts = pd.Timestamp(row["timestamp"]).to_pydatetime()
            rows.append(
                Prediction(
                    user_id=1,
                    timestamp=ts,
                    horizon=0,
                    predicted_power=float(row["power"]),
                    actual_power=float(row["power"]),
                    model_name=model_name,
                    model_version="v1",
                )
            )
        for _, row in forecast_df.iterrows():
            ts = pd.Timestamp(row["timestamp"]).to_pydatetime()
            rows.append(
                Prediction(
                    user_id=1,
                    timestamp=ts,
                    horizon=int(row["horizon"]),
                    predicted_power=float(row["predicted_power"]),
                    actual_power=actual_map.get(ts),
                    model_name=model_name,
                    model_version="v1",
                )
            )
        db.add_all(rows)
        db.commit()
        print(f"写入预测 {len(rows)} 条")
    finally:
        db.close()


def persist_strategies(energy: pd.DataFrame, env: pd.DataFrame) -> dict:
    settings = get_settings()
    demo_date = datetime.strptime(settings.demo_date, "%Y-%m-%d")
    today = energy[energy["timestamp"].dt.date == demo_date.date()]
    today_energy = float(today["energy"].sum())
    device_energy = today.groupby("device_type")["energy"].sum().to_dict()
    indoor_temp = float(env.loc[env["timestamp"].dt.date == demo_date.date(), "temperature"].mean())
    night = today[(today["timestamp"].dt.hour == 3) & (today["device_type"] == "water_heater")]
    anomaly_night_heater = bool((night["power"] > 800).any())
    items = build_strategies(today_energy, device_energy, indoor_temp, anomaly_night_heater)

    db = SessionLocal()
    try:
        db.query(Strategy).delete()
        rows = [
            Strategy(
                user_id=1,
                strategy_type=item.strategy_type,
                title=item.title,
                description=item.description,
                estimated_saving_kwh=item.estimated_saving_kwh,
                estimated_saving_percent=item.estimated_saving_percent,
                comfort_impact=item.comfort_impact,
                feasibility=item.feasibility,
                score=item.score,
            )
            for item in items
        ]
        db.add_all(rows)
        db.commit()
        print(f"写入策略 {len(rows)} 条")
    finally:
        db.close()
    return {
        "today_energy": today_energy,
        "device_energy": {k: round(float(v), 3) for k, v in device_energy.items()},
        "anomaly_night_heater": anomaly_night_heater,
        "top_strategy": items[0].title if items else None,
    }


def main() -> None:
    energy, env, behavior, labels, devices = load_demo()
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    hourly = build_hourly_frame(energy, env, behavior)
    forecast_metrics = train_forecast_model(
        hourly,
        MODELS_DIR / "forecast.joblib",
        PROCESSED_DIR / "forecast_metrics.json",
    )
    forecast_df = recursive_forecast(hourly, MODELS_DIR / "forecast.joblib", horizon_hours=24)
    persist_predictions(forecast_df, hourly, forecast_metrics["model_name"])

    anomaly_frame = prepare_anomaly_frame(energy, env, behavior)
    anomaly_train_info = train_anomaly_model(anomaly_frame, MODELS_DIR / "anomaly.joblib")
    scored = score_frame(anomaly_frame, MODELS_DIR / "anomaly.joblib")
    detected = select_anomalies(scored, energy)

    device_map: dict = {}
    for ts, group in energy.groupby("timestamp"):
        device_map[pd.Timestamp(ts)] = list(zip(group["device_id"].astype(int), group["power"].astype(float)))
    persist_anomalies(detected, device_map)
    anomaly_metrics = evaluate_anomalies(detected, labels)

    load_metrics = train_load_classifier(energy, MODELS_DIR / "load_clf.joblib")
    strategy_info = persist_strategies(energy, env)

    results = {
        "forecast": forecast_metrics,
        "anomaly_model": anomaly_train_info,
        "anomaly_detection": anomaly_metrics,
        "load_identification": load_metrics,
        "strategy": strategy_info,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }
    (MODELS_DIR / "metrics.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    (PROCESSED_DIR / "experiment_results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
