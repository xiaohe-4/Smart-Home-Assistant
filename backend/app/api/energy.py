from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.schemas import EnergyHistoryOut, EnergySummaryOut, EnergyTodayOut, HourlyEnergyOut
from app.services.energy_service import day_range, demo_day, query_series, today_stats


router = APIRouter(prefix="/api/energy", tags=["energy"])
settings = get_settings()


@router.get("/today", response_model=EnergyTodayOut)
def energy_today(user_id: int = Query(default=settings.demo_user_id), db: Session = Depends(get_db)):
    stats = today_stats(db, user_id)
    start, end = day_range(demo_day())
    series = query_series(db, user_id, start, end, freq="5min")
    return {
        "date": stats["date"],
        "total_energy": stats["today_energy"],
        "current_power": stats["current_power"],
        "peak_power": stats["peak_power"],
        "peak_time": stats["peak_time"],
        "compared_yesterday_percent": stats["compared_yesterday_percent"],
        "compared_week_avg_percent": stats["compared_week_avg_percent"],
        "series": series,
    }


@router.get("/history", response_model=EnergyHistoryOut)
def energy_history(
    days: int = Query(default=7, ge=1, le=30),
    user_id: int = Query(default=settings.demo_user_id),
    db: Session = Depends(get_db),
):
    end = demo_day() + timedelta(days=1)
    start = demo_day() - timedelta(days=days - 1)
    series = query_series(db, user_id, start, end, freq="D" if days >= 7 else "h")
    total = sum(p["energy"] for p in series)
    return {"start": start, "end": end, "total_energy": round(total, 3), "series": series}


@router.get("/hourly", response_model=HourlyEnergyOut)
def energy_hourly(
    date: str | None = None,
    user_id: int = Query(default=settings.demo_user_id),
    db: Session = Depends(get_db),
):
    day = datetime.strptime(date, "%Y-%m-%d") if date else demo_day()
    start, end = day_range(day)
    points = query_series(db, user_id, start, end, freq="h")
    return {"date": day.strftime("%Y-%m-%d"), "points": points}


@router.get("/summary", response_model=EnergySummaryOut)
def energy_summary(user_id: int = Query(default=settings.demo_user_id), db: Session = Depends(get_db)):
    stats = today_stats(db, user_id)
    return {
        "today_energy": stats["today_energy"],
        "yesterday_energy": stats["yesterday_energy"],
        "week_avg_energy": stats["week_avg_energy"],
        "month_energy": stats["month_energy"],
        "current_power": stats["current_power"],
        "peak_power": stats["peak_power"],
        "main_device": stats["main_device"],
        "main_device_share": stats["main_device_share"],
    }
