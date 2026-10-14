from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ai.forecasting.features import FEATURE_COLUMNS
from app.core.config import get_settings
from app.models import BehaviorRecord, Device, EnergyRecord, EnvironmentRecord, User, WeatherRecord
from app.services.energy_service import day_range, demo_day
from app.services.home_service import compare_homes, list_homes
from app.services.insight_service import correlation_report, load_today_frame

settings = get_settings()

MODALITIES = {
    "energy": {
        "key": "energy",
        "label": "用电记录",
        "table": "energy_records",
        "hardware": "智能电表 / 插座功率计",
        "fields": ["timestamp", "device_id", "power", "voltage", "current", "energy"],
        "required": ["timestamp", "device_id", "power", "energy"],
        "used_by": ["预测", "异常", "电费", "各电器占比"],
        "note": "演示按每台电器单独计量。页面上的占比是电表加总，不是从一块总表里拆出来的。",
    },
    "environment": {
        "key": "environment",
        "label": "室内环境",
        "table": "environment_records",
        "hardware": "温湿度 / 光照 / CO₂ 传感器",
        "fields": ["timestamp", "temperature", "humidity", "light", "co2"],
        "required": ["timestamp", "temperature", "humidity"],
        "used_by": ["预测", "室内状态", "空调建议"],
        "note": "室内温度会参与预测。光照和二氧化碳只用来解释，不计入准确率。",
    },
    "behavior": {
        "key": "behavior",
        "label": "人在哪",
        "table": "behavior_records",
        "hardware": "门磁、人体感应、手机在家、日程",
        "fields": ["timestamp", "occupancy", "location", "activity"],
        "required": ["timestamp", "occupancy"],
        "used_by": ["预测", "人少还在耗电", "今晚任务"],
        "note": "演示里占用/房间/活动由家庭作息规则生成，不是摄像头识别。",
    },
    "weather": {
        "key": "weather",
        "label": "室外天气",
        "table": "weather_records",
        "hardware": "气象 API；电价来自配置",
        "fields": ["timestamp", "temperature", "humidity", "weather", "wind_speed"],
        "required": ["timestamp", "temperature", "weather"],
        "used_by": ["说明文字", "空调假设", "峰谷电价"],
        "note": "预测的主要特征不含室外天气。电价和碳排放系数在配置里，换城市只改配置。",
    },
}

ADAPTERS = [
    {
        "id": "demo_csv",
        "label": "演示数据文件",
        "status": "active",
        "how": "scripts/generate_demo_data.py → data/demo/*.csv → scripts/init_db.py",
        "writes": ["energy", "environment", "behavior", "weather"],
    },
    {
        "id": "rest_ingest",
        "label": "接口采集",
        "status": "ready",
        "how": "POST /api/sources/validate 校验同一套字段；data_mode=live 后才写入。",
        "writes": ["energy", "environment", "behavior", "weather"],
    },
    {
        "id": "sql_swap",
        "label": "PostgreSQL 切换",
        "status": "ready",
        "how": "改 DATABASE_URL，表结构仍是 user_id + device_id + timestamp。",
        "writes": ["energy", "environment", "behavior", "weather"],
    },
]


def _iso(value) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat(sep=" ", timespec="minutes")
    return str(value)


def _span(db: Session, model, user_id: int | None = None) -> dict:
    stmt = select(func.min(model.timestamp), func.max(model.timestamp), func.count())
    if user_id is not None and hasattr(model, "user_id"):
        stmt = stmt.where(model.user_id == user_id)
    start, end, count = db.execute(stmt).one()
    return {"rows": int(count or 0), "start": _iso(start), "end": _iso(end)}


def _unique_ts(db: Session, model, user_id: int | None, start: datetime, end: datetime) -> set:
    stmt = select(model.timestamp).where(model.timestamp >= start, model.timestamp < end).distinct()
    if user_id is not None and hasattr(model, "user_id"):
        stmt = stmt.where(model.user_id == user_id)
    return set(db.scalars(stmt).all())


def _coverage(have: set, base: set) -> float:
    if not base:
        return 0.0
    return round(len(have & base) / len(base) * 100, 1)


def alignment_report(db: Session, user_id: int) -> dict:
    start, end = day_range(demo_day())
    energy = _unique_ts(db, EnergyRecord, user_id, start, end)
    env = _unique_ts(db, EnvironmentRecord, user_id, start, end)
    beh = _unique_ts(db, BehaviorRecord, user_id, start, end)
    weather = _unique_ts(db, WeatherRecord, None, start, end)
    degraded = user_id == settings.real_user_id
    aligned = energy if degraded else energy & env & beh & weather
    interval = 5
    ordered = sorted(energy)
    if len(ordered) >= 2:
        delta = (ordered[1] - ordered[0]).total_seconds() / 60
        if delta > 0:
            interval = int(delta)
    return {
        "date": settings.demo_date,
        "points": len(energy),
        "aligned": len(aligned),
        "percent": round(len(aligned) / max(len(energy), 1) * 100, 1),
        "interval_minutes": interval,
        "missing": {
            "environment": len(energy - env),
            "behavior": len(energy - beh),
            "weather": len(energy - weather),
        },
        "note": (
            "对照家庭没有人和天气数据，只按用电时间对齐。"
            if degraded
            else "按演示日每 5 分钟对齐。用电、室温、在家人数和天气都有记录时，预测和解释才能一起成立。"
        ),
        "degraded": degraded,
    }


def get_source_map(db: Session, user_id: int) -> dict:
    user = db.get(User, user_id)
    devices = db.scalars(select(Device).where(Device.user_id == user_id).order_by(Device.id)).all()
    spans = {
        "energy": _span(db, EnergyRecord, user_id),
        "environment": _span(db, EnvironmentRecord, user_id),
        "behavior": _span(db, BehaviorRecord, user_id),
        "weather": _span(db, WeatherRecord),
    }
    align = alignment_report(db, user_id)
    start, end = day_range(demo_day())
    energy_ts = _unique_ts(db, EnergyRecord, user_id, start, end)
    env_ts = _unique_ts(db, EnvironmentRecord, user_id, start, end)
    beh_ts = _unique_ts(db, BehaviorRecord, user_id, start, end)
    wea_ts = _unique_ts(db, WeatherRecord, None, start, end)
    modalities = []
    for key, spec in MODALITIES.items():
        ts = {"energy": energy_ts, "environment": env_ts, "behavior": beh_ts, "weather": wea_ts}[key]
        modalities.append(
            {
                **spec,
                **spans[key],
                "coverage": _coverage(ts, energy_ts),
                "active": spans[key]["rows"] > 0,
            }
        )
    return {
        "mode": settings.data_mode,
        "city": settings.city,
        "season": settings.season,
        "household": {
            "id": user_id,
            "name": user.name if user else "演示家庭",
            "size": user.household_size if user else 4,
            "home_type": user.home_type if user else "住宅",
        },
        "tariff": {
            "peak": settings.price_peak,
            "flat": settings.price_flat,
            "valley": settings.price_valley,
            "carbon": settings.carbon_kg_per_kwh,
        },
        "devices": [{"id": d.id, "name": d.name, "device_type": d.device_type, "rated_power": d.rated_power} for d in devices],
        "modalities": modalities,
        "alignment": align,
        "forecast_features": FEATURE_COLUMNS,
        "adapters": [{**a, "active": a["id"] == "demo_csv" and settings.data_mode == "demo"} for a in ADAPTERS],
        "portability": [
            {
                "step": 1,
                "title": "换采集方式",
                "detail": "新的采集程序按同一套字段写入四张表，预测和策略代码不用改。",
            },
            {
                "step": 2,
                "title": "改本地配置",
                "detail": f"城市、季节、峰平谷电价、碳因子都在配置里。当前 {settings.city} 峰 {settings.price_peak} / 平 {settings.price_flat} / 谷 {settings.price_valley}。",
            },
            {
                "step": 3,
                "title": "换家庭后重新训练",
                "detail": "预测和异常模型是用这一家 30 天的数据训练的。换一户后运行 scripts/train_models.py。",
            },
        ],
        "limits": [
            "管家开关是模拟的，没有接真实设备。",
            "演示里的「人在不在家」按作息生成，不是摄像头识别。",
            "各电器占比来自分路电表。只有一块总表时，识别不了具体电器。",
        ],
        "homes": list_homes(db),
        "compare": compare_homes(db),
        "load_identification_applicable": user_id != settings.real_user_id,
        "honesty": "演示家庭是仿真数据，用来稳定走出凌晨 03:17 这一幕。对照家庭来自公开负荷或真实导出，没有人和天气，缺的部分不硬算。仿真的 R² 不能当成真实家庭的精度。",
    }


def degrade_report(db: Session, user_id: int, dropped: list[str]) -> dict:
    dropped = [item for item in dropped if item in MODALITIES]
    frame = load_today_frame(db, user_id)
    before = correlation_report(frame)
    after_frame = frame.copy()
    if not after_frame.empty:
        if "behavior" in dropped and "occupancy" in after_frame:
            after_frame["occupancy"] = None
        if "environment" in dropped:
            for col in ("temperature", "humidity"):
                if col in after_frame:
                    after_frame[col] = None
        if "weather" in dropped:
            for col in ("outdoor_temp", "weather"):
                if col in after_frame:
                    after_frame[col] = None
    after = correlation_report(after_frame)
    broken = []
    if "energy" in dropped:
        broken.append("没有用电记录时，预测、异常和电费都算不了。")
    if "behavior" in dropped:
        broken.append("人少还在耗电、离家关灯、今晚任务里的人数会不准。")
    if "environment" in dropped:
        broken.append("预测仍可用之前的功率，但不好再解释是不是室温把电用高了。")
    if "weather" in dropped:
        broken.append("空调和室外温差的说明会变短。预测用的主要特征不受影响。")
    kept_features = []
    lost_features = []
    mapping = {
        "environment": ["temperature", "humidity"],
        "behavior": ["occupancy"],
        "weather": [],
        "energy": [c for c in FEATURE_COLUMNS if c.startswith("lag") or c.startswith("rolling") or c == "hour"],
    }
    lost = set()
    for key in dropped:
        lost.update(mapping.get(key, []))
    for feat in FEATURE_COLUMNS:
        (lost_features if feat in lost else kept_features).append(feat)
    return {
        "dropped": dropped,
        "before": {
            "power_vs_temperature": before.get("power_vs_temperature"),
            "power_vs_occupancy": before.get("power_vs_occupancy"),
            "power_vs_outdoor": before.get("power_vs_outdoor"),
        },
        "after": {
            "power_vs_temperature": after.get("power_vs_temperature"),
            "power_vs_occupancy": after.get("power_vs_occupancy"),
            "power_vs_outdoor": after.get("power_vs_outdoor"),
        },
        "kept_features": kept_features,
        "lost_features": lost_features,
        "broken": broken or ["用电、室温、在家人数和天气都在，没有缺项。"],
        "note": "这是同一天数据的对照，不会改数据库。缺了某一路时，仍用已有记录对齐；模型用前一个值或空值补上，规则会放宽，不会直接报错。",
    }


def validate_ingest(modality: str, rows: list[dict]) -> dict:
    spec = MODALITIES.get(modality)
    if spec is None:
        return {"ok": False, "detail": "未知模态", "errors": [{"row": 0, "field": "modality", "error": "只接受 energy/environment/behavior/weather"}]}
    if not rows:
        return {"ok": False, "detail": "没有行", "errors": [{"row": 0, "field": "rows", "error": "至少一行"}]}
    errors = []
    for i, row in enumerate(rows[:300]):
        if not isinstance(row, dict):
            errors.append({"row": i, "field": "_", "error": "行必须是对象"})
            continue
        for field in spec["required"]:
            if row.get(field) in (None, ""):
                errors.append({"row": i, "field": field, "error": "必填缺失"})
        if modality == "energy":
            try:
                power = float(row.get("power"))
                if power < 0:
                    errors.append({"row": i, "field": "power", "error": "功率不能为负"})
            except (TypeError, ValueError):
                errors.append({"row": i, "field": "power", "error": "功率必须是数字"})
        if modality == "behavior" and row.get("occupancy") is not None:
            try:
                occ = int(row.get("occupancy"))
                if occ < 0 or occ > 12:
                    errors.append({"row": i, "field": "occupancy", "error": "人数应在 0–12"})
            except (TypeError, ValueError):
                errors.append({"row": i, "field": "occupancy", "error": "人数必须是整数"})
    writable = settings.data_mode == "live"
    return {
        "ok": not errors,
        "modality": modality,
        "rows": len(rows),
        "checked": min(len(rows), 300),
        "errors": errors[:30],
        "would_write": writable and not errors,
        "mode": settings.data_mode,
        "note": "演示模式只校验合同，不写入，避免冲掉 30 日实验数据。把 data_mode 设为 live 后，同一接口才落库。",
        "contract": {"required": spec["required"], "fields": spec["fields"], "hardware": spec["hardware"]},
    }
