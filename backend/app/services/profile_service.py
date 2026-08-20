import json
from pathlib import Path

from sqlalchemy.orm import Session

from ai.optimization.strategy_engine import device_saving_table
from ai.profiling.profile import energy_efficiency_score, portrait_summary
from app.core.config import PROJECT_ROOT
from app.models import Anomaly, User
from app.services.energy_service import today_stats


def get_profile(db: Session, user_id: int) -> dict:
    user = db.get(User, user_id)
    stats = today_stats(db, user_id)
    score_info = get_energy_score(db, user_id)
    potential = get_saving_potential(db, user_id)
    portrait = portrait_summary(
        stats["today_energy"],
        stats["yesterday_energy"],
        stats["week_avg_energy"],
        stats["month_energy"],
        stats["peak_power"],
        stats["peak_time"],
        stats["main_device"],
        score_info["energy_score"],
        potential["total_saving_percent"],
    )
    return {
        "household_name": user.name if user else "演示家庭",
        "household_size": user.household_size if user else 4,
        "home_type": user.home_type if user else "住宅",
        "city": "成都",
        "season": "夏季",
        **portrait,
    }


def get_energy_score(db: Session, user_id: int) -> dict:
    stats = today_stats(db, user_id)
    anomaly_count = (
        db.query(Anomaly)
        .filter(Anomaly.user_id == user_id, Anomaly.severity.in_(["medium", "high", "critical"]))
        .count()
    )
    waste = sum(
        v * 0.12
        for k, v in stats["device_energy"].items()
        if k in {"lighting", "water_heater", "other"}
    )
    return energy_efficiency_score(
        stats["today_energy"],
        stats["week_avg_energy"],
        anomaly_count,
        stats["peak_power"],
        waste,
    )


def get_saving_potential(db: Session, user_id: int) -> dict:
    stats = today_stats(db, user_id)
    devices = device_saving_table(stats["device_energy"], stats["device_names"])
    total_base = sum(d["baseline_kwh"] for d in devices)
    total_save = sum(d["saving_kwh"] for d in devices)
    total_opt = total_base - total_save
    return {
        "total_baseline_kwh": round(total_base, 3),
        "total_optimized_kwh": round(total_opt, 3),
        "total_saving_kwh": round(total_save, 3),
        "total_saving_percent": round(total_save / max(total_base, 0.01) * 100, 2),
        "devices": devices,
    }


def assistant_summary(db: Session, user_id: int) -> dict:
    profile = get_profile(db, user_id)
    from app.services.anomaly_service import latest_anomalies

    latest = latest_anomalies(db, user_id, limit=1)
    anomaly_text = latest[0]["description"] if latest else None
    summary = (
        f"今天家庭用电 {profile['today_energy']:.2f} kWh，主要来自{profile['main_device']}。"
        f"系统评估当前能源效率为 {profile['energy_score']:.0f}/100，"
        f"预计通过优化运行策略可降低约 {profile['saving_potential_percent']:.1f}% 的能源消耗。"
    )
    if anomaly_text:
        summary += f"同时发现异常：{anomaly_text}"
    return {
        "summary": summary,
        "today_energy": profile["today_energy"],
        "main_device": profile["main_device"],
        "saving_potential": profile["saving_potential_percent"],
        "anomaly": anomaly_text,
    }


def experiment_results() -> dict:
    path = PROJECT_ROOT / "data" / "processed" / "experiment_results.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}
