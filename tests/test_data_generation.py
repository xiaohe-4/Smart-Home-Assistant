import json

from scripts.generate_demo_data import DEMO_DATE, generate
import scripts.generate_demo_data as gen


def test_generate_demo_data(tmp_path, monkeypatch):
    demo_dir = tmp_path / "demo"
    processed_dir = tmp_path / "processed"
    monkeypatch.setattr(gen, "DEMO_DIR", demo_dir)
    monkeypatch.setattr(gen, "PROCESSED_DIR", processed_dir)
    summary = generate()
    assert summary["points"] == 30 * 24 * 12
    assert summary["energy_rows"] == summary["points"] * 8
    assert abs(summary["today_energy_kwh"] - 18.42) < 0.4
    shares = summary["device_share_percent"]
    assert shares["air_conditioner"] > 35
    assert shares["water_heater"] > 15
    assert (demo_dir / "energy_records.csv").exists()
    payload = json.loads((demo_dir / "summary.json").read_text(encoding="utf-8"))
    assert payload["demo_date"] == DEMO_DATE.strftime("%Y-%m-%d")
