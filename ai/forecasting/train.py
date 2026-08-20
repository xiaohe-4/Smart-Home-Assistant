from pathlib import Path

import pandas as pd
from sklearn.model_selection import TimeSeriesSplit

from ai.forecasting.features import FEATURE_COLUMNS, add_lag_features, regression_metrics
from ai.forecasting.model import build_regressor, save_model


def train_forecast_model(
    hourly_df: pd.DataFrame,
    model_path: Path,
    metrics_path: Path | None = None,
) -> dict:
    featured = add_lag_features(hourly_df)
    x = featured[FEATURE_COLUMNS]
    y = featured["power"]

    splitter = TimeSeriesSplit(n_splits=3)
    last_metrics = {}
    y_true_all = []
    y_pred_all = []
    for train_idx, test_idx in splitter.split(x):
        model, model_name = build_regressor()
        model.fit(x.iloc[train_idx], y.iloc[train_idx])
        pred = model.predict(x.iloc[test_idx])
        last_metrics = regression_metrics(y.iloc[test_idx].to_numpy(), pred)
        last_metrics["model_name"] = model_name
        y_true_all.extend(y.iloc[test_idx].tolist())
        y_pred_all.extend(pred.tolist())

    final_model, model_name = build_regressor()
    final_model.fit(x, y)
    overall = regression_metrics(y_true_all, y_pred_all)
    overall["model_name"] = model_name
    overall["model_version"] = "v1"
    overall["samples"] = int(len(featured))

    save_model(final_model, model_path, extra={"metrics": overall, "model_name": model_name})
    if metrics_path:
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        pd.Series(overall).to_json(metrics_path, force_ascii=False)

    return overall
