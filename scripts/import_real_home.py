"""导入验证户：公开住宅负荷风格的 14 天、3 路插座，对齐到现有表字段。

优先读 data/raw/real_home_01/ 下的导出 CSV；没有则按公开住宅典型日曲线
（工作日双峰、凌晨基线、插座短脉冲）重建一户宿舍样本，仅用于跑通导入轨
和缺模态对照。答辩时可把智能插座 App 导出或 UK-DALE/REDD 切片覆盖 raw 目录。
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import delete


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.models import Device, EnergyRecord, User  # noqa: E402


RAW_DIR = PROJECT_ROOT / "data" / "raw" / "real_home_01"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REAL_USER_ID = 2
INTERVAL_MINUTES = 5
DAYS = 14
SEED = 2026


DEVICES = [
    {"id": 101, "name": "空调插座", "device_type": "air_conditioner", "rated_power": 1200},
    {"id": 102, "name": "热水壶", "device_type": "water_heater", "rated_power": 1800},
    {"id": 103, "name": "其他插座", "device_type": "other", "rated_power": 200},
]


def _target_end() -> datetime:
    return datetime.strptime(get_settings().demo_date, "%Y-%m-%d") + timedelta(days=1)


def _build_public_style() -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(SEED)
    end = _target_end()
    start = end - timedelta(days=DAYS)
    stamps = pd.date_range(start, end, freq=f"{INTERVAL_MINUTES}min", inclusive="left")
    step = INTERVAL_MINUTES / 60.0
    rows: list[dict] = []
    labels: list[datetime] = []

    for ts in stamps:
        hour = ts.hour
        minute = ts.minute
        weekday = ts.weekday()
        weekend = weekday >= 5
        # 空调：工作日傍晚到夜间，周末更晚；凌晨基线
        if 18 <= hour <= 23 or (weekend and 14 <= hour <= 17):
            ac = 280 + 420 * (0.55 + 0.45 * np.sin((hour - 18) / 6 * np.pi))
            ac += rng.normal(0, 35)
        elif 0 <= hour < 6:
            ac = 18 + rng.normal(0, 6)
        else:
            ac = 45 + rng.normal(0, 12)
        ac = float(np.clip(ac, 8, 1100))

        kettle = 2.0 + rng.normal(0, 1.2)
        burst = False
        if hour in {7, 8, 12, 18, 22} and minute < 15 and rng.random() < (0.55 if not weekend else 0.7):
            kettle = 1750 + rng.normal(0, 40)
            burst = True
        if hour in {2, 3, 4} and minute < 10 and rng.random() < 0.04:
            kettle = 1680 + rng.normal(0, 50)
            burst = True
            labels.append(ts.to_pydatetime())
        kettle = float(np.clip(kettle, 0, 1900))

        other = 55 + 40 * (1 if 19 <= hour <= 23 else 0.25) + rng.normal(0, 8)
        if weekend and 10 <= hour <= 16:
            other += 25
        other = float(np.clip(other, 15, 220))

        for device in DEVICES:
            power = {"air_conditioner": ac, "water_heater": kettle, "other": other}[device["device_type"]]
            if burst and device["device_type"] != "water_heater":
                pass
            rows.append(
                {
                    "timestamp": ts,
                    "device_id": device["id"],
                    "device": device["device_type"],
                    "power": round(power, 2),
                    "voltage": 220.0,
                    "energy": round(power / 1000.0 * step, 6),
                }
            )
    energy = pd.DataFrame(rows)
    label_df = pd.DataFrame({"timestamp": labels, "note": "夜间热水壶抽查点"})
    return energy, label_df


def _read_raw() -> pd.DataFrame | None:
    candidates = list(RAW_DIR.glob("*.csv"))
    if not candidates:
        return None
    path = next((p for p in candidates if p.name.lower() != "readme.csv"), candidates[0])
    text = path.read_text(encoding="utf-8", errors="ignore").splitlines()[:1]
    header = text[0] if text else ""
    if ";" in header and "Global_active_power" in header:
        raw = pd.read_csv(path, sep=";", na_values=["?"])
        raw["timestamp"] = pd.to_datetime(raw["Date"] + " " + raw["Time"], dayfirst=True, errors="coerce")
        raw = raw.dropna(subset=["timestamp"])
        raw["power"] = pd.to_numeric(raw["Global_active_power"], errors="coerce") * 1000
        raw["energy"] = raw["power"] / 1000.0 * (INTERVAL_MINUTES / 60.0)
        raw["device_id"] = 103
        raw["device"] = "other"
        return raw[["timestamp", "device_id", "device", "power", "energy"]]
    frame = pd.read_csv(path)
    cols = {c.lower(): c for c in frame.columns}
    ts_col = cols.get("timestamp") or cols.get("time") or cols.get("datetime")
    pw_col = cols.get("power") or cols.get("watts") or cols.get("w")
    if ts_col is None or pw_col is None:
        raise ValueError(f"无法识别导出列: {list(frame.columns)}，需要 timestamp + power")
    out = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(frame[ts_col]),
            "power": pd.to_numeric(frame[pw_col], errors="coerce"),
        }
    )
    device_col = cols.get("device") or cols.get("device_type") or cols.get("name")
    if device_col:
        mapping = {d["device_type"]: d["id"] for d in DEVICES}
        out["device"] = frame[device_col].astype(str)
        out["device_id"] = out["device"].map(lambda x: mapping.get(x, 103))
    else:
        out["device"] = "other"
        out["device_id"] = 103
    out = out.dropna(subset=["timestamp", "power"])
    return out


def align_and_resample(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    frame = frame.set_index("timestamp").sort_index()
    pieces = []
    for device_id, part in frame.groupby("device_id"):
        resampled = part["power"].resample(f"{INTERVAL_MINUTES}min").mean().interpolate(limit=6).ffill().bfill()
        block = resampled.reset_index()
        block["device_id"] = int(device_id)
        device = next((d for d in DEVICES if d["id"] == int(device_id)), DEVICES[-1])
        block["device"] = device["device_type"]
        pieces.append(block)
    aligned = pd.concat(pieces, ignore_index=True)
    end = _target_end()
    last = aligned["timestamp"].max()
    if pd.notna(last):
        shift = end - (pd.Timestamp(last).floor("D") + timedelta(days=1))
        aligned["timestamp"] = aligned["timestamp"] + shift
    start = end - timedelta(days=DAYS)
    aligned = aligned[(aligned["timestamp"] >= start) & (aligned["timestamp"] < end)]
    aligned["voltage"] = 220.0
    aligned["energy"] = (aligned["power"].clip(lower=0) / 1000.0 * (INTERVAL_MINUTES / 60.0)).round(6)
    aligned["power"] = aligned["power"].clip(lower=0).round(2)
    return aligned.reset_index(drop=True)


def write_processed(energy: pd.DataFrame, labels: pd.DataFrame) -> Path:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out = PROCESSED_DIR / "real_home_01.csv"
    energy.to_csv(out, index=False)
    if not labels.empty:
        labels.to_csv(PROCESSED_DIR / "real_home_01_labels.csv", index=False)
    (RAW_DIR / "README.txt").write_text(
        "户型：单人宿舍   人数：1\n"
        "采集起止：演示日往前 14 天（默认按公开住宅负荷曲线重建）\n"
        "设备：空调插座 / 热水壶 / 其他插座\n"
        "授权：仅竞赛演示，脱敏，home_id=real_01\n"
        "覆盖方法：把 App 导出 CSV（timestamp,power[,device]）放到本目录后重新运行 scripts/import_real_home.py\n",
        encoding="utf-8",
    )
    return out


def import_to_db(energy: pd.DataFrame) -> None:
    db = SessionLocal()
    try:
        db.execute(delete(EnergyRecord).where(EnergyRecord.user_id == REAL_USER_ID))
        db.execute(delete(Device).where(Device.user_id == REAL_USER_ID))
        db.execute(delete(User).where(User.id == REAL_USER_ID))
        db.commit()
        db.add(
            User(
                id=REAL_USER_ID,
                name="验证户·宿舍总表风格",
                household_size=1,
                home_type="单人宿舍",
            )
        )
        db.flush()
        for spec in DEVICES:
            db.add(
                Device(
                    id=spec["id"],
                    user_id=REAL_USER_ID,
                    name=spec["name"],
                    device_type=spec["device_type"],
                    rated_power=spec["rated_power"],
                    status="on",
                )
            )
        db.flush()
        payload = [
            {
                "user_id": REAL_USER_ID,
                "device_id": int(row.device_id),
                "timestamp": pd.Timestamp(row.timestamp).to_pydatetime(),
                "power": float(row.power),
                "voltage": 220.0,
                "current": float(row.power) / 220.0,
                "energy": float(row.energy),
            }
            for row in energy.itertuples(index=False)
        ]
        for start in range(0, len(payload), 4000):
            db.bulk_insert_mappings(EnergyRecord, payload[start : start + 4000])
        db.commit()
        print(f"验证户入库: user_id={REAL_USER_ID}, energy={len(payload)}")
    finally:
        db.close()


def main() -> dict:
    raw = _read_raw()
    source = "raw_export"
    labels = pd.DataFrame(columns=["timestamp", "note"])
    if raw is None:
        energy, labels = _build_public_style()
        source = "public_style_rebuild"
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        energy.to_csv(RAW_DIR / "export.csv", index=False)
    else:
        energy = align_and_resample(raw)
    write_processed(energy, labels)
    import_to_db(energy)
    today = energy[energy["timestamp"].dt.date == (_target_end() - timedelta(days=1)).date()]
    summary = {
        "home_id": "real_01",
        "user_id": REAL_USER_ID,
        "source": source,
        "days": DAYS,
        "circuits": int(energy["device_id"].nunique()),
        "rows": int(len(energy)),
        "today_energy_kwh": round(float(today["energy"].sum()), 3) if not today.empty else 0,
        "has_occupancy": False,
        "has_weather": False,
        "load_identification": False,
        "note": "无占用/天气，预测走降级特征；无分路标签时不做家电分类准确率。",
    }
    (PROCESSED_DIR / "real_home_01_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


if __name__ == "__main__":
    main()
