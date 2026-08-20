from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Device, EnergyRecord


settings = get_settings()
DEVICE_CN = {
    "air_conditioner": "空调",
    "refrigerator": "冰箱",
    "water_heater": "热水器",
    "washing_machine": "洗衣机",
    "television": "电视",
    "lighting": "照明",
    "computer": "电脑",
    "other": "其他",
}


def demo_day() -> datetime:
    return datetime.strptime(settings.demo_date, "%Y-%m-%d")


def percent_change(current: float, baseline: float) -> float | None:
    if baseline <= 0:
        return None
    return round((current - baseline) / baseline * 100, 1)


def day_range(day: datetime) -> tuple[datetime, datetime]:
    start = datetime(day.year, day.month, day.day)
    return start, start + timedelta(days=1)


def query_energy_sum(db: Session, user_id: int, start: datetime, end: datetime) -> float:
    value = db.scalar(
        select(func.coalesce(func.sum(EnergyRecord.energy), 0.0)).where(
            EnergyRecord.user_id == user_id,
            EnergyRecord.timestamp >= start,
            EnergyRecord.timestamp < end,
        )
    )
    return float(value or 0.0)


def query_series(db: Session, user_id: int, start: datetime, end: datetime, freq: str = "5min") -> list[dict]:
    rows = db.execute(
        select(EnergyRecord.timestamp, func.sum(EnergyRecord.power), func.sum(EnergyRecord.energy))
        .where(
            EnergyRecord.user_id == user_id,
            EnergyRecord.timestamp >= start,
            EnergyRecord.timestamp < end,
        )
        .group_by(EnergyRecord.timestamp)
        .order_by(EnergyRecord.timestamp)
    ).all()
    if not rows:
        return []
    frame = pd.DataFrame(rows, columns=["timestamp", "power", "energy"])
    if freq != "5min":
        frame = (
            frame.set_index("timestamp")
            .resample(freq)
            .agg({"power": "mean", "energy": "sum"})
            .dropna()
            .reset_index()
        )
    return [
        {"timestamp": ts.to_pydatetime() if hasattr(ts, "to_pydatetime") else ts, "power": float(p), "energy": float(e)}
        for ts, p, e in frame.itertuples(index=False)
    ]


def today_stats(db: Session, user_id: int) -> dict:
    today = demo_day()
    start, end = day_range(today)
    yesterday_start, yesterday_end = day_range(today - timedelta(days=1))
    week_start = today - timedelta(days=7)
    month_start = today - timedelta(days=29)

    today_energy = query_energy_sum(db, user_id, start, end)
    yesterday_energy = query_energy_sum(db, user_id, yesterday_start, yesterday_end)
    week_energy = query_energy_sum(db, user_id, week_start, start)
    month_energy = query_energy_sum(db, user_id, month_start, end)
    week_avg = week_energy / 7 if week_energy else 0.0

    peak_row = db.execute(
        select(
            EnergyRecord.timestamp,
            func.sum(EnergyRecord.power).label("power"),
        )
        .where(
            EnergyRecord.user_id == user_id,
            EnergyRecord.timestamp >= start,
            EnergyRecord.timestamp < end,
        )
        .group_by(EnergyRecord.timestamp)
        .order_by(func.sum(EnergyRecord.power).desc())
        .limit(1)
    ).first()

    target = start + timedelta(hours=20, minutes=30)
    latest_row = db.execute(
        select(
            EnergyRecord.timestamp,
            func.sum(EnergyRecord.power).label("power"),
        )
        .where(
            EnergyRecord.user_id == user_id,
            EnergyRecord.timestamp == target,
        )
        .group_by(EnergyRecord.timestamp)
        .limit(1)
    ).first()
    if latest_row is None:
        latest_row = db.execute(
            select(
                EnergyRecord.timestamp,
                func.sum(EnergyRecord.power).label("power"),
            )
            .where(
                EnergyRecord.user_id == user_id,
                EnergyRecord.timestamp >= start,
                EnergyRecord.timestamp < end,
            )
            .group_by(EnergyRecord.timestamp)
            .order_by(EnergyRecord.timestamp.desc())
            .limit(1)
        ).first()

    device_rows = db.execute(
        select(Device.device_type, Device.name, func.sum(EnergyRecord.energy))
        .join(EnergyRecord, EnergyRecord.device_id == Device.id)
        .where(
            EnergyRecord.user_id == user_id,
            EnergyRecord.timestamp >= start,
            EnergyRecord.timestamp < end,
        )
        .group_by(Device.device_type, Device.name)
        .order_by(func.sum(EnergyRecord.energy).desc())
    ).all()
    main_device = device_rows[0][1] if device_rows else "未知"
    main_type = device_rows[0][0] if device_rows else "other"
    main_energy = float(device_rows[0][2]) if device_rows else 0.0

    return {
        "date": settings.demo_date,
        "today_energy": round(today_energy, 3),
        "yesterday_energy": round(yesterday_energy, 3),
        "week_avg_energy": round(week_avg, 3),
        "month_energy": round(month_energy, 3),
        "current_power": round(float(latest_row.power), 1) if latest_row else 0.0,
        "peak_power": round(float(peak_row.power), 1) if peak_row else 0.0,
        "peak_time": peak_row.timestamp if peak_row else None,
        "main_device": main_device,
        "main_device_type": main_type,
        "main_device_share": round(main_energy / today_energy * 100, 2) if today_energy else 0.0,
        "compared_yesterday_percent": percent_change(today_energy, yesterday_energy),
        "compared_week_avg_percent": percent_change(today_energy, week_avg),
        "device_energy": {row[0]: float(row[2]) for row in device_rows},
        "device_names": {row[0]: row[1] for row in device_rows},
    }
