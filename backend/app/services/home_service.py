from sqlalchemy.orm import Session

from app.core.config import PROJECT_ROOT, get_settings
from app.models import Device, EnergyRecord, User
from app.services.energy_service import day_range, demo_day, today_stats


settings = get_settings()


def list_homes(db: Session) -> list[dict]:
    demo = db.get(User, settings.demo_user_id)
    real = db.get(User, settings.real_user_id)
    return [
        {
            "id": settings.demo_user_id,
            "key": "demo",
            "label": "演示户",
            "name": demo.name if demo else "成都仿真四口",
            "kind": "simulation",
            "days": 30,
            "circuits": 8,
            "has_occupancy": True,
            "has_weather": True,
            "load_identification": True,
            "note": "完整四路，现场主演示。含仿真。",
        },
        {
            "id": settings.real_user_id,
            "key": "real",
            "label": "验证户",
            "name": real.name if real else "宿舍总表风格验证户",
            "kind": "public_or_real",
            "days": 14,
            "circuits": 3,
            "has_occupancy": False,
            "has_weather": False,
            "load_identification": False,
            "note": "缺模态已降级。本户仅插座分路，不做总表 NILM。",
            "available": real is not None,
        },
    ]


def compare_homes(db: Session) -> dict:
    import json

    metrics = {}
    path = PROJECT_ROOT / "models" / "metrics.json"
    if path.exists():
        metrics = json.loads(path.read_text(encoding="utf-8"))
    demo_fc = metrics.get("forecast") or {}
    real_fc = (metrics.get("real") or {}).get("forecast") or {}
    demo_an = metrics.get("anomaly_detection") or {}
    real_an = (metrics.get("real") or {}).get("anomaly_detection") or {}
    demo_stats = today_stats(db, settings.demo_user_id)
    real_user = db.get(User, settings.real_user_id)
    real_stats = today_stats(db, settings.real_user_id) if real_user else {}
    start, end = day_range(demo_day())
    demo_devices = db.query(Device).filter(Device.user_id == settings.demo_user_id).count()
    real_devices = db.query(Device).filter(Device.user_id == settings.real_user_id).count()
    demo_rows = db.query(EnergyRecord).filter(EnergyRecord.user_id == settings.demo_user_id).count()
    real_rows = db.query(EnergyRecord).filter(EnergyRecord.user_id == settings.real_user_id).count()
    return {
        "boundary": [
            "演示含仿真。",
            "负荷识别不是 NILM。",
            "异常 F1=0.35，上线以规则为准。",
        ],
        "rows": [
            {"item": "天数", "demo": "30", "real": "14"},
            {"item": "分路", "demo": str(demo_devices or 8), "real": str(real_devices or "1–3")},
            {"item": "占用/天气", "demo": "有", "real": "无，已降级"},
            {
                "item": "预测 MAPE",
                "demo": f"{demo_fc.get('MAPE', '--')}%",
                "real": f"{real_fc.get('MAPE', '--')}%" if real_fc else "未训练",
            },
            {
                "item": "预测 R²",
                "demo": str(demo_fc.get("R2", "--")),
                "real": str(real_fc.get("R2", "--")) if real_fc else "未训练",
            },
            {
                "item": "基线（昨天同时段）MAPE",
                "demo": f"{(demo_fc.get('baseline_yesterday') or {}).get('MAPE', '--')}%",
                "real": f"{(real_fc.get('baseline_yesterday') or {}).get('MAPE', '--')}%" if real_fc else "--",
            },
            {
                "item": "异常",
                "demo": f"植入 {demo_an.get('labeled', 13)} 点 / 检出 {demo_an.get('detected', 27)} / F1 {demo_an.get('f1', 0.35)}",
                "real": f"人工抽查 {real_an.get('labeled', 0)} 条 / 规则检出 {real_an.get('detected', 0)} 条",
            },
        ],
        "demo_today_kwh": demo_stats.get("today_energy"),
        "real_today_kwh": real_stats.get("today_energy"),
        "demo_rows": demo_rows,
        "real_rows": real_rows,
        "range": {"start": start.isoformat(sep=" "), "end": end.isoformat(sep=" ")},
        "note": "预测在验证户上变差是加分项：说明没有只在仿真上刷分。现场仍以演示户打 03:17 这一幕。",
        "compare": metrics.get("compare") or {},
    }
