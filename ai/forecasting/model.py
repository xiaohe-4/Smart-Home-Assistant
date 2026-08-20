from pathlib import Path

import joblib
from sklearn.ensemble import RandomForestRegressor

from ai.forecasting.features import FEATURE_COLUMNS


def _try_xgboost():
    try:
        from xgboost import XGBRegressor

        return XGBRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.08,
            subsample=0.9,
            colsample_bytree=0.9,
            objective="reg:squarederror",
            random_state=42,
            n_jobs=4,
        )
    except Exception:
        return None


def build_regressor():
    model = _try_xgboost()
    if model is not None:
        return model, "XGBoostRegressor"
    return (
        RandomForestRegressor(
            n_estimators=300,
            max_depth=12,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
        ),
        "RandomForestRegressor",
    )


def save_model(model, path: Path, extra: dict | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"model": model, "features": FEATURE_COLUMNS, **(extra or {})}
    joblib.dump(payload, path)


def load_model(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"预测模型不存在: {path}")
    return joblib.load(path)
