from sqlalchemy import select
from sqlalchemy.orm import Session

from ai.optimization.strategy_engine import simulate_savings
from app.models import Strategy
from app.services.energy_service import today_stats
from app.services.insight_service import load_today_frame, replay_frames
from app.utils.pricing import carbon_of, estimate_bill


def list_strategies(db: Session, user_id: int) -> list[Strategy]:
    return db.scalars(
        select(Strategy).where(Strategy.user_id == user_id).order_by(Strategy.score.desc())
    ).all()


def top_strategies(db: Session, user_id: int, limit: int = 3) -> list[Strategy]:
    return list_strategies(db, user_id)[:limit]


def simulate(db: Session, user_id: int, strategy_ids: list[int]) -> dict:
    items = list_strategies(db, user_id)
    selected = [s for s in items if not strategy_ids or s.id in strategy_ids]
    stats = today_stats(db, user_id)
    result = simulate_savings(
        stats["today_energy"],
        stats["device_energy"],
        [s.strategy_type for s in selected],
        anomaly_night_heater=True,
    )
    avg_price = 0.55
    before_cost = estimate_bill(result["before_kwh"], avg_price)
    after_cost = estimate_bill(result["after_kwh"], avg_price)
    frame = load_today_frame(db, user_id)
    replay = replay_frames(frame, result["saving_percent"])
    hourly = [
        {
            "hour": row["hour"],
            "label": row["label"],
            "actual_power": row["power"],
            "optimized_power": row["optimized_power"],
            "actual_kwh": row["energy"],
            "optimized_kwh": round(
                row["energy"] * (row["optimized_power"] / row["power"]) if row["power"] else row["energy"],
                3,
            ),
        }
        for row in replay
    ]
    return {
        **result,
        "before_cost": before_cost,
        "after_cost": after_cost,
        "saving_cost": round(before_cost - after_cost, 2),
        "before_carbon": carbon_of(result["before_kwh"]),
        "after_carbon": carbon_of(result["after_kwh"]),
        "applied": selected,
        "hourly": hourly,
    }
