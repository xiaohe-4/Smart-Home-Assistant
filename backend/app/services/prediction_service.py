from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.config import PROJECT_ROOT, get_settings
from app.models import Prediction
from app.services.energy_service import demo_day, day_range, query_series


settings = get_settings()
METRICS_PATH = PROJECT_ROOT / "models" / "metrics.json"


def _metrics_for_user(user_id: int) -> dict:
    if not METRICS_PATH.exists():
        return {}
    import json

    payload = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    if user_id == get_settings().real_user_id:
        return (payload.get("real") or {}).get("forecast") or {}
    return payload.get("forecast") or {}


def get_prediction(db: Session, user_id: int, hours: int) -> dict:
    today = demo_day()
    start, _ = day_range(today - timedelta(days=1))
    history_rows = (
        db.query(Prediction)
        .filter(
            Prediction.user_id == user_id,
            Prediction.horizon == 0,
            Prediction.timestamp >= start,
        )
        .order_by(Prediction.timestamp)
        .all()
    )
    forecast_rows = (
        db.query(Prediction)
        .filter(
            Prediction.user_id == user_id,
            Prediction.horizon > 0,
            Prediction.horizon <= hours,
        )
        .order_by(Prediction.timestamp)
        .all()
    )
    metrics = _metrics_for_user(user_id)
    if not forecast_rows:
        # 模型尚未训练时，用最近负荷作为保守回退，避免前端空白，但不伪造精度
        series = query_series(db, user_id, *day_range(today), freq="h")
        return {
            "horizon_hours": hours,
            "model_name": "untrained",
            "model_version": "v0",
            "metrics": {},
            "history": [
                {"timestamp": p["timestamp"], "predicted_power": p["power"], "actual_power": p["power"]}
                for p in series
            ],
            "forecast": [],
        }
    return {
        "horizon_hours": hours,
        "model_name": metrics.get("model_name", forecast_rows[0].model_name),
        "model_version": metrics.get("model_version", "v1"),
        "metrics": {
            k: v
            for k, v in metrics.items()
            if k in {"MAE", "RMSE", "MAPE", "R2"}
        },
        "history": [
            {
                "timestamp": row.timestamp,
                "predicted_power": row.predicted_power,
                "actual_power": row.actual_power,
            }
            for row in history_rows
        ],
        "forecast": [
            {
                "timestamp": row.timestamp,
                "predicted_power": row.predicted_power,
                "actual_power": row.actual_power,
            }
            for row in forecast_rows
        ],
    }
