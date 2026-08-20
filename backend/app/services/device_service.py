from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Device, EnergyRecord
from app.models.actuator import DeviceActuator
from app.services.energy_service import demo_day, day_range


def list_devices(db: Session, user_id: int) -> list[Device]:
    return db.scalars(select(Device).where(Device.user_id == user_id).order_by(Device.id)).all()


def get_device(db: Session, user_id: int, device_id: int) -> Device | None:
    return db.scalar(select(Device).where(Device.user_id == user_id, Device.id == device_id))


def device_energy_breakdown(db: Session, user_id: int) -> list[dict]:
    today = demo_day()
    start, end = day_range(today)
    latest_ts = db.scalar(
        select(func.max(EnergyRecord.timestamp)).where(
            EnergyRecord.user_id == user_id,
            EnergyRecord.timestamp >= start,
            EnergyRecord.timestamp < end,
        )
    )
    rows = db.execute(
        select(
            Device.id,
            Device.name,
            Device.device_type,
            Device.rated_power,
            Device.status,
            func.sum(EnergyRecord.energy),
        )
        .join(EnergyRecord, EnergyRecord.device_id == Device.id)
        .where(
            Device.user_id == user_id,
            EnergyRecord.timestamp >= start,
            EnergyRecord.timestamp < end,
        )
        .group_by(Device.id)
        .order_by(func.sum(EnergyRecord.energy).desc())
    ).all()

    # SQLite 没有 iif 时退回 Python 统计
    if not rows:
        return []

    current_map = {}
    if latest_ts:
        current_rows = db.execute(
            select(EnergyRecord.device_id, EnergyRecord.power).where(
                EnergyRecord.user_id == user_id,
                EnergyRecord.timestamp == latest_ts,
            )
        ).all()
        current_map = {r[0]: float(r[1]) for r in current_rows}

    runtime_rows = db.execute(
        select(EnergyRecord.device_id, EnergyRecord.power).where(
            EnergyRecord.user_id == user_id,
            EnergyRecord.timestamp >= start,
            EnergyRecord.timestamp < end,
        )
    ).all()
    runtime = {}
    for device_id, power in runtime_rows:
        if power > 15:
            runtime[device_id] = runtime.get(device_id, 0) + 5 / 60

    total = sum(float(r[5] or 0) for r in rows) or 1.0
    result = []
    for row in rows:
        today_energy = float(row[5] or 0)
        result.append(
            {
                "id": row[0],
                "name": row[1],
                "device_type": row[2],
                "rated_power": float(row[3]),
                "status": "运行" if current_map.get(row[0], 0) > 15 else "待机",
                "today_energy": round(today_energy, 3),
                "share": round(today_energy / total * 100, 2),
                "runtime_hours": round(runtime.get(row[0], 0.0), 2),
                "current_power": round(current_map.get(row[0], 0.0), 1),
            }
        )
    return overlay_devices(db, user_id, result)


def overlay_devices(db: Session, user_id: int, devices: list[dict]) -> list[dict]:
    acts = {
        a.device_id: a
        for a in db.scalars(select(DeviceActuator).where(DeviceActuator.user_id == user_id)).all()
    }
    for item in devices:
        item.setdefault("baseline_power", item["current_power"])
        item.setdefault("controlled", False)
        item.setdefault("setpoint", None)
        item.setdefault("actuator_note", None)
        act = acts.get(item["id"])
        if not act:
            continue
        item["controlled"] = True
        item["setpoint"] = act.setpoint
        item["actuator_note"] = act.last_command
        if not act.enabled:
            item["status"] = "关闭"
            item["current_power"] = 0.0
        elif act.setpoint and item["device_type"] == "air_conditioner":
            factor = max(0.55, 1.0 - (float(act.setpoint) - 24.0) * 0.10)
            item["current_power"] = round(item["baseline_power"] * factor, 1)
            item["status"] = "运行" if item["current_power"] > 15 else "待机"
    return devices


def device_energy_series(db: Session, user_id: int, device_id: int) -> list[dict]:
    start, end = day_range(demo_day())
    rows = db.execute(
        select(EnergyRecord.timestamp, EnergyRecord.power, EnergyRecord.energy)
        .where(
            EnergyRecord.user_id == user_id,
            EnergyRecord.device_id == device_id,
            EnergyRecord.timestamp >= start,
            EnergyRecord.timestamp < end,
        )
        .order_by(EnergyRecord.timestamp)
    ).all()
    return [
        {"timestamp": r.timestamp, "power": float(r.power), "energy": float(r.energy)}
        for r in rows
    ]
