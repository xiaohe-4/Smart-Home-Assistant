from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from ai.forecasting.features import FEATURE_COLUMNS
from ai.load_identification.classifier import DEVICE_LABELS, extract_device_windows
from app.core.config import PROJECT_ROOT, get_settings
from app.models import Device, EnergyRecord
from app.services.energy_service import day_range, demo_day


settings = get_settings()
METRICS_PATH = PROJECT_ROOT / "models" / "metrics.json"
FORECAST_PATH = PROJECT_ROOT / "models" / "forecast.joblib"
LOAD_CLF_PATH = PROJECT_ROOT / "models" / "load_clf.joblib"

FEATURE_CN = {
    "lag_1": "前 1 小时功率",
    "lag_2": "前 2 小时功率",
    "lag_3": "前 3 小时功率",
    "lag_6": "前 6 小时功率",
    "lag_12": "前 12 小时功率",
    "lag_24": "前 24 小时功率",
    "rolling_mean_1h": "近 1 小时滚动均值",
    "rolling_mean_3h": "近 3 小时滚动均值",
    "rolling_mean_6h": "近 6 小时滚动均值",
    "rolling_mean_24h": "近 24 小时滚动均值",
    "temperature": "室内温度",
    "humidity": "室内湿度",
    "occupancy": "占用人数",
    "hour": "小时",
    "weekday": "星期",
    "is_weekend": "是否周末",
}

LOAD_FEATURE_CN = {
    "mean_power": "窗内平均功率",
    "peak_power": "窗内峰值功率",
    "runtime_ratio": "运行占比",
    "power_std": "功率标准差",
    "start_hour": "起始小时",
    "cycle_score": "功率跳变比",
}

FORECAST_HONESTY = (
    "XGBoost 在 TimeSeriesSplit 三折上汇总。准确率定义为 100-MAPE，不是分类准确率。"
    "主特征 16 列含占用和室内温湿度，不含室外天气。"
)
LOAD_HONESTY = (
    "RandomForest 做的是「有设备分路标签的 1 小时功率窗分类」，测试集 Accuracy 0.9513。"
    "这不是总表盲拆 NILM。页面上的空调/热水器占比来自分路电表汇总。"
    "下方推理示例与训练日重叠，只证明链路可跑，不能当第二套测试集。"
)
ANOMALY_HONESTY = (
    "Isolation Forest 给异常分，规则引擎给时段和设备。对照 13 个植入点，检出 27 条，"
    "Precision 0.2593 / Recall 0.5385 / F1 0.35。请主动展示，不要把检出条数当成准确率。"
)


def read_metrics() -> dict:
    if METRICS_PATH.exists():
        return json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    return {}


@lru_cache(maxsize=2)
def _joblib_load(path_str: str):
    path = Path(path_str)
    if not path.exists():
        return None
    try:
        import joblib

        return joblib.load(path)
    except Exception:
        return None


def _importance(payload: dict | None, cn_map: dict[str, str]) -> list[dict]:
    if not payload:
        return []
    model = payload.get("model")
    feats = list(payload.get("features") or [])
    if model is None or not hasattr(model, "feature_importances_") or not feats:
        return []
    values = [float(v) for v in model.feature_importances_]
    rows = []
    for name, value in zip(feats, values):
        rows.append(
            {
                "feature": name,
                "label": cn_map.get(name, name),
                "importance": round(value, 4),
            }
        )
    rows.sort(key=lambda r: r["importance"], reverse=True)
    return rows


def _forecast_block(raw: dict) -> dict:
    metrics = dict(raw.get("forecast") or {})
    payload = _joblib_load(str(FORECAST_PATH))
    return {
        "available": bool(metrics) or payload is not None,
        "model_name": metrics.get("model_name") or (payload or {}).get("model_name") or "untrained",
        "model_version": metrics.get("model_version", "v1"),
        "samples": metrics.get("samples"),
        "metrics": {
            k: metrics[k]
            for k in ("MAE", "RMSE", "MAPE", "R2", "accuracy")
            if k in metrics
        },
        "features": FEATURE_COLUMNS,
        "feature_importance": _importance(payload, FEATURE_CN),
        "not_in_model": ["outdoor_temp", "weather"],
        "honesty": FORECAST_HONESTY,
    }


def _anomaly_block(raw: dict) -> dict:
    det = dict(raw.get("anomaly_detection") or {})
    model = dict(raw.get("anomaly_model") or {})
    return {
        "available": bool(det),
        "model_name": model.get("model_name", "IsolationForest + rules"),
        "samples": model.get("samples"),
        "precision": det.get("precision"),
        "recall": det.get("recall"),
        "f1": det.get("f1"),
        "labeled": det.get("labeled"),
        "detected": det.get("detected"),
        "honesty": ANOMALY_HONESTY,
    }


def _strategy_block(raw: dict) -> dict:
    st = dict(raw.get("strategy") or {})
    device_energy = st.get("device_energy") or {}
    total = sum(float(v) for v in device_energy.values()) or 1.0
    shares = [
        {
            "device_type": key,
            "label": DEVICE_LABELS.get(key, key),
            "kwh": round(float(val), 3),
            "share": round(float(val) / total * 100, 1),
        }
        for key, val in sorted(device_energy.items(), key=lambda kv: -float(kv[1]))
    ]
    return {
        "today_energy": round(float(st["today_energy"]), 3) if st.get("today_energy") is not None else None,
        "top_strategy": st.get("top_strategy"),
        "anomaly_night_heater": st.get("anomaly_night_heater"),
        "devices": shares,
        "honesty": "策略节能量由规则引擎按今日分路电量实时模拟，不是大模型估算。",
    }


def _load_id_samples(db: Session, user_id: int, payload: dict | None) -> dict:
    empty = {"samples": [], "hits": 0, "n": 0, "confusions": [], "note": LOAD_HONESTY}
    if not payload or not payload.get("model"):
        return empty
    try:
        start, end = day_range(demo_day())
        rows = db.execute(
            select(
                EnergyRecord.device_id,
                EnergyRecord.timestamp,
                EnergyRecord.power,
                Device.device_type,
            )
            .join(Device, Device.id == EnergyRecord.device_id)
            .where(
                EnergyRecord.user_id == user_id,
                EnergyRecord.timestamp >= start,
                EnergyRecord.timestamp < end,
            )
            .order_by(EnergyRecord.timestamp)
        ).all()
        if not rows:
            return empty
        frame = pd.DataFrame(rows, columns=["device_id", "timestamp", "power", "device_type"])
        windows = extract_device_windows(frame)
        if windows.empty:
            return empty
        x_cols = list(payload.get("features") or LOAD_FEATURE_CN.keys())
        missing = [c for c in x_cols if c not in windows.columns]
        if missing:
            return empty
        preds = payload["model"].predict(windows[x_cols])
        windows = windows.copy()
        windows["pred"] = preds
        samples = []
        for dtype, group in windows.groupby("device_type", sort=False):
            row = group.iloc[len(group) // 2]
            samples.append(
                {
                    "device_type": str(dtype),
                    "label": DEVICE_LABELS.get(str(dtype), str(dtype)),
                    "pred": str(row["pred"]),
                    "pred_label": DEVICE_LABELS.get(str(row["pred"]), str(row["pred"])),
                    "hit": str(row["pred"]) == str(dtype),
                    "mean_power": round(float(row["mean_power"]), 1),
                    "peak_power": round(float(row["peak_power"]), 1),
                    "start_hour": int(row["start_hour"]),
                }
            )
        hits = sum(1 for s in samples if s["hit"])
        miss = windows[windows["pred"] != windows["device_type"]]
        confusions = []
        if not miss.empty:
            ranked = miss.groupby(["device_type", "pred"]).size().sort_values(ascending=False).head(5)
            for (src, dst), count in ranked.items():
                confusions.append(
                    {
                        "true": DEVICE_LABELS.get(str(src), str(src)),
                        "pred": DEVICE_LABELS.get(str(dst), str(dst)),
                        "count": int(count),
                    }
                )
        return {
            "samples": samples,
            "hits": hits,
            "n": len(samples),
            "confusions": confusions,
            "note": "演示窗与训练日重叠，命中数只证明推理链路可用，不能替代测试集 0.9513。",
        }
    except Exception:
        return empty


def _load_block(raw: dict, db: Session, user_id: int) -> dict:
    info = dict(raw.get("load_identification") or {})
    payload = _joblib_load(str(LOAD_CLF_PATH))
    live = _load_id_samples(db, user_id, payload)
    return {
        "available": bool(info) or payload is not None,
        "model_name": info.get("model_name", "RandomForestClassifier"),
        "accuracy": info.get("accuracy"),
        "macro_f1": info.get("macro_f1"),
        "samples": info.get("samples"),
        "not_nilm": True,
        "feature_importance": _importance(payload, LOAD_FEATURE_CN),
        "live": live,
        "honesty": LOAD_HONESTY,
    }


def speech_metrics() -> str:
    raw = read_metrics()
    fc = raw.get("forecast") or {}
    load = raw.get("load_identification") or {}
    det = raw.get("anomaly_detection") or {}
    if not fc and not load:
        return "模型指标文件尚未生成。请先运行 scripts/train_models.py，不要口头编造准确率。"
    return (
        f"预测是 {fc.get('model_name', 'XGBoost')}，R² {fc.get('R2')}，MAPE {fc.get('MAPE')}%，"
        f"准确率按 100-MAPE 计为 {fc.get('accuracy')}%，MAE {fc.get('MAE')} W。"
        f"负荷识别测试集 Accuracy {load.get('accuracy')}、macro-F1 {load.get('macro_f1')}，"
        f"这是有分路标签的窗口分类，不是总表盲拆 NILM。"
        f"异常检测 Precision {det.get('precision')}、Recall {det.get('recall')}、F1 {det.get('f1')}，"
        f"标注 {det.get('labeled')} 个点、检出 {det.get('detected')} 条，请把精确率和召回一起看。"
    )


def get_model_lab(db: Session, user_id: int | None = None) -> dict:
    uid = user_id or settings.demo_user_id
    raw = read_metrics()
    forecast = _forecast_block(raw)
    anomaly = _anomaly_block(raw)
    load = _load_block(raw, db, uid)
    strategy = _strategy_block(raw)
    return {
        "generated_at": raw.get("generated_at"),
        "source": "models/metrics.json + joblib",
        "forecast": forecast,
        "anomaly": anomaly,
        "load": load,
        "strategy": strategy,
        "honesty": "所有数字来自训练脚本落盘文件或当场加载的 joblib，不由大模型计算。",
    }
