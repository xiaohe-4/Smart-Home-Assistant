from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Anomaly, Device

EXPLAIN_MAP = {
    "unusual_time": [
        {"feature": "时段合理性", "weight": 0.46, "note": "该小时在 30 日作息里几乎不启动同类设备"},
        {"feature": "占用状态", "weight": 0.28, "note": "夜间占用低，负荷应接近待机基线"},
        {"feature": "功率偏离", "weight": 0.26, "note": "相对同时段中位功率显著偏高"},
    ],
    "high_power": [
        {"feature": "功率偏离", "weight": 0.52, "note": "瞬时功率超过设备常规运行区间"},
        {"feature": "持续时长", "weight": 0.27, "note": "高功率没有在短脉冲后回落"},
        {"feature": "环境匹配", "weight": 0.21, "note": "室温/占用无法解释这次负荷跃升"},
    ],
    "low_occupancy_waste": [
        {"feature": "占用状态", "weight": 0.48, "note": "家中人数很少时仍保持高功率"},
        {"feature": "设备类型", "weight": 0.32, "note": "空调或照明未随行为关闭"},
        {"feature": "电价时段", "weight": 0.20, "note": "浪费发生在可调度窗口"},
    ],
}


def explain_anomaly(anomaly_type: str) -> list[dict]:
    return EXPLAIN_MAP.get(anomaly_type, [
        {"feature": "模型评分", "weight": 0.40, "note": "Isolation Forest 判定偏离正常簇"},
        {"feature": "规则复核", "weight": 0.35, "note": "时段、设备和功率联合触发阈值"},
        {"feature": "历史对照", "weight": 0.25, "note": "与近 30 日同时段分布不一致"},
    ])


def list_anomalies(db: Session, user_id: int, limit: int = 100) -> list[dict]:
    rows = db.execute(
        select(Anomaly, Device.name)
        .outerjoin(Device, Device.id == Anomaly.device_id)
        .where(Anomaly.user_id == user_id)
        .order_by(Anomaly.timestamp.desc())
        .limit(limit)
    ).all()
    result = []
    for anomaly, device_name in rows:
        item = {
            "id": anomaly.id,
            "user_id": anomaly.user_id,
            "timestamp": anomaly.timestamp,
            "device_id": anomaly.device_id,
            "anomaly_score": anomaly.anomaly_score,
            "anomaly_type": anomaly.anomaly_type,
            "description": anomaly.description,
            "severity": anomaly.severity,
            "status": anomaly.status,
            "device_name": device_name,
            "explain": explain_anomaly(anomaly.anomaly_type),
        }
        result.append(item)
    return result


def latest_anomalies(db: Session, user_id: int, limit: int = 5) -> list[dict]:
    return list_anomalies(db, user_id, limit=limit)
