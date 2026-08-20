from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ai.forecasting.features import FEATURE_COLUMNS
from app.core.config import get_settings
from app.models import BehaviorRecord, Device, EnergyRecord, EnvironmentRecord, User, WeatherRecord
from app.services.energy_service import day_range, demo_day
from app.services.insight_service import correlation_report, load_today_frame

settings = get_settings()

MODALITIES = {
    "energy": {
        "key": "energy",
        "label": "电力时序",
        "table": "energy_records",
        "hardware": "智能电表 / 插座功率计",
        "fields": ["timestamp", "device_id", "power", "voltage", "current", "energy"],
        "required": ["timestamp", "device_id", "power", "energy"],
        "used_by": ["预测", "异常", "电费", "负荷分解"],
        "note": "演示是分设备计量。页面上的负荷分解按表计汇总，不是从总电表做 NILM 盲拆。",
    },
    "environment": {
        "key": "environment",
        "label": "室内环境",
        "table": "environment_records",
        "hardware": "温湿度 / 光照 / CO₂ 传感器",
        "fields": ["timestamp", "temperature", "humidity", "light", "co2"],
        "required": ["timestamp", "temperature", "humidity"],
        "used_by": ["预测特征", "数字孪生", "空调建议"],
        "note": "室内温度进入 XGBoost；光照和 CO₂ 主要用于解释，不参与精度指标。",
    },
    "behavior": {
        "key": "behavior",
        "label": "行为占用",
        "table": "behavior_records",
        "hardware": "门磁、人体感应、手机在家、日程",
        "fields": ["timestamp", "occupancy", "location", "activity"],
        "required": ["timestamp", "occupancy"],
        "used_by": ["预测特征", "低占用浪费", "调度清单"],
        "note": "演示里占用/房间/活动由家庭作息规则生成，不是摄像头识别。",
    },
    "weather": {
        "key": "weather",
        "label": "天气与外部",
        "table": "weather_records",
        "hardware": "气象 API；电价来自配置",
        "fields": ["timestamp", "temperature", "humidity", "weather", "wind_speed"],
        "required": ["timestamp", "temperature", "weather"],
        "used_by": ["洞察文案", "空调 what-if", "峰谷电价"],
        "note": "XGBoost 主特征不含室外天气。电价、碳因子在配置里，换城市只改配置。",
    },
}

ADAPTERS = [
    {
        "id": "demo_csv",
        "label": "演示 CSV 管道",
        "status": "active",
        "how": "scripts/generate_demo_data.py → data/demo/*.csv → scripts/init_db.py",
        "writes": ["energy", "environment", "behavior", "weather"],
    },
    {
        "id": "rest_ingest",
        "label": "REST 采集适配器",
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
    aligned = energy & env & beh & weather
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
        "note": "对齐按演示日 5 分钟时间戳交集计算。四路都有点，预测和环境解释才能同时成立。",
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
                "title": "换接入层",
                "detail": "采集适配器按同一张合同写入四张表，不必改预测和策略代码。",
            },
            {
                "step": 2,
                "title": "改本地配置",
                "detail": f"城市、季节、峰平谷电价、碳因子都在配置里。当前 {settings.city} 峰 {settings.price_peak} / 平 {settings.price_flat} / 谷 {settings.price_valley}。",
            },
            {
                "step": 3,
                "title": "按户重训",
                "detail": "XGBoost 与 Isolation Forest 是在这户 30 日上拟合的。换家庭后跑 scripts/train_models.py。",
            },
        ],
        "limits": [
            "管家拧开关是家庭侧模拟，未对接真实 IoT。",
            "占用/活动在演示中由作息规则生成，不是视频识别。",
            "负荷分解来自分路计量；只有总电表时需要另接 NILM。",
        ],
        "honesty": "多模态不是图像或语音。演示数据是高质量仿真灌进标准表，程序跑的是库，不是每次现场编数。",
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
        broken.append("没有电力时序，预测、异常、电费全部停。")
    if "behavior" in dropped:
        broken.append("低占用浪费、离家关灯、调度清单里的人数会失真。")
    if "environment" in dropped:
        broken.append("预测仍可用功率滞后项，但热驱动解释变弱。")
    if "weather" in dropped:
        broken.append("空调室外温差文案会降级，XGBoost 主特征不受影响。")
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
        "broken": broken or ["当前四路都在，没有降级。"],
        "note": "这是同一日数据上的对照，不改数据库。缺模态时表可以左连接，模型用前向填充或空值，规则会降级而不是崩溃。",
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
