from ai.forecasting.features import regression_metrics
from ai.optimization.strategy_engine import build_strategies, simulate_savings
from ai.profiling.profile import energy_efficiency_score
from app.utils.speech import for_voice


def test_regression_metrics_not_fake():
    y_true = [100, 120, 140]
    y_pred = [110, 118, 150]
    metrics = regression_metrics(y_true, y_pred)
    assert set(metrics) >= {"MAE", "RMSE", "MAPE", "R2"}
    assert metrics["MAE"] > 0


def test_energy_score_bounds():
    result = energy_efficiency_score(18.42, 17.8, 2, 3800, 1.2)
    assert 0 <= result["energy_score"] <= 100


def test_strategy_engine_outputs_structured_advice():
    device_energy = {
        "air_conditioner": 7.7,
        "water_heater": 3.8,
        "refrigerator": 2.2,
        "lighting": 1.4,
        "computer": 1.2,
        "television": 0.9,
        "washing_machine": 0.6,
        "other": 0.4,
    }
    items = build_strategies(18.42, device_energy, 29.5, True)
    assert len(items) >= 3
    assert "建议" in items[0].description
    sim = simulate_savings(18.42, device_energy, [i.strategy_type for i in items[:3]], True)
    assert sim["after_kwh"] < sim["before_kwh"]
    assert sim["saving_percent"] > 0


def test_voice_reads_watt_in_chinese():
    spoken = for_voice("全家大约 515 W，最亮的是客厅变频空调 420W，已经压下 80.5 W。今日 18.73 kWh，功率 2.1 kW。")
    assert "瓦" in spoken
    assert "千瓦时" in spoken
    assert "千瓦" in spoken
    import re

    assert re.search(r"\d\s*[Ww]\b", spoken) is None
