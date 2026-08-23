from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit

from ai.forecasting.features import FEATURE_COLUMNS, add_lag_features, regression_metrics
from ai.forecasting.model import build_regressor, save_model


def baseline_metrics(featured: pd.DataFrame, test_idx) -> dict:
    y = featured["power"].to_numpy()
    yesterday = featured["power"].shift(24).to_numpy()
    weekmean = (
        featured.groupby("hour", group_keys=False)["power"]
        .apply(lambda s: s.shift(1).rolling(7, min_periods=1).mean())
        .to_numpy()
    )
    y_test = y[test_idx]
    yest = yesterday[test_idx]
    week = weekmean[test_idx]
    valid_yest = np.isfinite(yest)
    valid_week = np.isfinite(week)
    return {
        "baseline_yesterday": regression_metrics(y_test[valid_yest], yest[valid_yest]) if valid_yest.any() else {},
        "baseline_weekmean": regression_metrics(y_test[valid_week], week[valid_week]) if valid_week.any() else {},
    }


def train_forecast_model(
    hourly_df: pd.DataFrame,
    model_path: Path,
    metrics_path: Path | None = None,
    feature_columns: list[str] | None = None,
) -> dict:
    cols = feature_columns or FEATURE_COLUMNS
    featured = add_lag_features(hourly_df)
    missing = [c for c in cols if c not in featured.columns]
    if missing:
        for name in missing:
            featured[name] = 0.0
    x = featured[cols]
    y = featured["power"]

    splitter = TimeSeriesSplit(n_splits=3)
    y_true_all = []
    y_pred_all = []
    last_test_idx = None
    for train_idx, test_idx in splitter.split(x):
        model, model_name = build_regressor()
        model.fit(x.iloc[train_idx], y.iloc[train_idx])
        pred = model.predict(x.iloc[test_idx])
        y_true_all.extend(y.iloc[test_idx].tolist())
        y_pred_all.extend(pred.tolist())
        last_test_idx = test_idx

    final_model, model_name = build_regressor()
    final_model.fit(x, y)
    overall = regression_metrics(y_true_all, y_pred_all)
    overall["model_name"] = model_name
    overall["model_version"] = "v1"
    overall["samples"] = int(len(featured))
    overall["split"] = "TimeSeriesSplit(n_splits=3)"
    overall["features"] = cols
    if last_test_idx is not None:
        overall.update(baseline_metrics(featured, last_test_idx))

    save_model(
        final_model,
        model_path,
        extra={"metrics": overall, "model_name": model_name, "features": cols},
    )
    if metrics_path:
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        pd.Series({k: v for k, v in overall.items() if not isinstance(v, (dict, list))}).to_json(
            metrics_path, force_ascii=False
        )

    return overall
