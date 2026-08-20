"""生成 30 天、5 分钟粒度的高质量家庭多模态 Demo 数据。"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_DIR = PROJECT_ROOT / "data" / "demo"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

SEED = 42
DEMO_DATE = datetime(2026, 8, 19)
DAYS = 30
INTERVAL_MINUTES = 5
START = DEMO_DATE - timedelta(days=DAYS - 1)

HOUSEHOLD = {
    "id": 1,
    "name": "成都四口之家",
    "household_size": 4,
    "home_type": "三室两厅住宅",
}

DEVICES = [
    {"id": 1, "name": "客厅变频空调", "device_type": "air_conditioner", "rated_power": 1500},
    {"id": 2, "name": "双门冰箱", "device_type": "refrigerator", "rated_power": 120},
    {"id": 3, "name": "储水式热水器", "device_type": "water_heater", "rated_power": 2000},
    {"id": 4, "name": "滚筒洗衣机", "device_type": "washing_machine", "rated_power": 400},
    {"id": 5, "name": "客厅电视", "device_type": "television", "rated_power": 110},
    {"id": 6, "name": "全屋照明", "device_type": "lighting", "rated_power": 180},
    {"id": 7, "name": "书房电脑", "device_type": "computer", "rated_power": 220},
    {"id": 8, "name": "其他插座负荷", "device_type": "other", "rated_power": 80},
]

DEMO_SHARES = {
    "air_conditioner": 0.42,
    "water_heater": 0.21,
    "refrigerator": 0.12,
    "lighting": 0.08,
    "computer": 0.07,
    "television": 0.05,
    "washing_machine": 0.03,
    "other": 0.02,
}

TODAY_TARGET_KWH = 18.42
YESTERDAY_TARGET_KWH = 21.03
WEEK_AVG_TARGET_KWH = 17.85


def timestamps() -> list[datetime]:
    delta = timedelta(minutes=INTERVAL_MINUTES)
    total = DAYS * 24 * (60 // INTERVAL_MINUTES)
    return [START + i * delta for i in range(total)]


def outdoor_temp(ts: datetime, rng: np.random.Generator) -> float:
    hour = ts.hour + ts.minute / 60
    base = 28.5 + 5.2 * np.sin((hour - 10) / 24 * 2 * np.pi)
    day_shift = 0.35 * np.sin(ts.timetuple().tm_yday / 365 * 2 * np.pi)
    noise = rng.normal(0, 0.35)
    return float(np.clip(base + day_shift + noise, 24.0, 37.0))


def weather_label(temp: float, rng: np.random.Generator) -> str:
    roll = rng.random()
    if temp >= 34 and roll < 0.7:
        return "晴热"
    if roll < 0.15:
        return "阵雨"
    if roll < 0.45:
        return "多云"
    return "晴"


def occupancy_and_activity(ts: datetime, is_weekend: bool) -> tuple[int, str, str]:
    hour = ts.hour + ts.minute / 60
    if 0 <= hour < 6.5:
        return 4, "卧室", "sleeping"
    if 6.5 <= hour < 7.5:
        return 4, "餐厅", "cooking"
    if 7.5 <= hour < 8.5:
        return 2 if not is_weekend else 4, "客厅", "leaving_home" if not is_weekend else "resting"
    if 8.5 <= hour < 12:
        return (1 if not is_weekend else 3), "书房" if not is_weekend else "客厅", "working" if not is_weekend else "resting"
    if 12 <= hour < 13.5:
        return (2 if not is_weekend else 4), "餐厅", "cooking"
    if 13.5 <= hour < 18:
        return (1 if not is_weekend else 3), "书房", "working"
    if 18 <= hour < 19:
        return 4, "餐厅", "returning_home"
    if 19 <= hour < 23:
        return 4, "客厅", "watching_tv" if hour < 22 else "resting"
    return 4, "卧室", "sleeping"


def fridge_power(idx: int, rated: float, rng: np.random.Generator) -> float:
    cycle = 36  # 3 hours of 5-min points ≈ compressor pattern
    phase = (idx + int(rng.integers(0, 8))) % cycle
    if phase < 22:
        return float(rated * rng.uniform(0.85, 1.15))
    return float(rated * rng.uniform(0.08, 0.18))


def device_raw_power(
    device_type: str,
    ts: datetime,
    indoor_temp: float,
    occupancy: int,
    activity: str,
    idx: int,
    rng: np.random.Generator,
    rated: float,
    is_weekend: bool,
) -> float:
    hour = ts.hour + ts.minute / 60
    if device_type == "refrigerator":
        return fridge_power(idx, rated, rng)

    if device_type == "air_conditioner":
        load = 0.0
        if occupancy >= 1 and (hour >= 11 or hour < 1):
            load = 0.35
        if 18 <= hour <= 23.5 and occupancy >= 2:
            load = 0.85
        if activity == "sleeping" and (hour >= 22 or hour < 6):
            load = 0.55 if indoor_temp > 27 else 0.2
        if indoor_temp > 29:
            load = max(load, 0.7)
        if indoor_temp > 32:
            load = max(load, 0.9)
        if occupancy == 0:
            load *= 0.15
        return float(rated * load * rng.uniform(0.9, 1.08))

    if device_type == "water_heater":
        load = 0.05
        if 6.5 <= hour <= 8.0 or 18.0 <= hour <= 22.0:
            load = 0.75 if occupancy >= 2 else 0.45
        if activity == "cooking" and 18 <= hour <= 19:
            load = max(load, 0.35)
        return float(rated * load * rng.uniform(0.9, 1.05))

    if device_type == "washing_machine":
        weekday = ts.weekday()
        use_today = weekday in (2, 5, 6) or (ts.date() == (DEMO_DATE - timedelta(days=1)).date())
        if use_today and 19 <= hour <= 21.5:
            return float(rated * rng.uniform(0.7, 1.05))
        return float(rated * rng.uniform(0.0, 0.02))

    if device_type == "television":
        if 19 <= hour <= 23 and occupancy >= 2:
            return float(rated * rng.uniform(0.8, 1.05))
        if activity == "watching_tv":
            return float(rated * rng.uniform(0.75, 1.0))
        return float(rated * rng.uniform(0.02, 0.08))

    if device_type == "lighting":
        load = 0.05
        if 6.5 <= hour <= 7.5:
            load = 0.45
        if 18 <= hour <= 23.5:
            load = 0.8 if occupancy >= 2 else 0.35
        if activity == "sleeping":
            load = 0.04
        if occupancy == 0:
            load = 0.12
        return float(rated * load * rng.uniform(0.85, 1.1))

    if device_type == "computer":
        if (not is_weekend and 8 <= hour <= 18) or (19 <= hour <= 23):
            return float(rated * rng.uniform(0.55, 0.95))
        return float(rated * rng.uniform(0.05, 0.15))

    # other
    base = 0.25 + 0.15 * occupancy
    if 18 <= hour <= 22:
        base += 0.2
    return float(rated * np.clip(base, 0.1, 1.0) * rng.uniform(0.8, 1.1))


def inject_anomalies(
    energy_rows: list[dict],
    rng: np.random.Generator,
) -> list[dict]:
    labels = []
    normalized = []
    for row in energy_rows:
        ts = row["timestamp"]
        if isinstance(ts, pd.Timestamp):
            row["timestamp"] = ts.to_pydatetime()
        row["device_id"] = int(row["device_id"])
        normalized.append(row)
    lookup = {(int(row["device_id"]), row["timestamp"]): i for i, row in enumerate(normalized)}

    def set_power(device_id: int, ts: datetime, power: float, kind: str, desc: str, severity: str):
        key = (device_id, ts)
        if key not in lookup:
            return
        row = energy_rows[lookup[key]]
        row["power"] = power
        row["current"] = power / max(row["voltage"], 1)
        row["energy"] = power / 1000 * (INTERVAL_MINUTES / 60)
        labels.append(
            {
                "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
                "device_id": device_id,
                "anomaly_type": kind,
                "description": desc,
                "severity": severity,
            }
        )

    # Demo 核心异常：演示日凌晨热水器启动
    anomaly_ts = datetime(2026, 8, 19, 3, 15)
    for minutes in (0, 5, 10):
        ts = anomaly_ts + timedelta(minutes=minutes)
        set_power(
            3,
            ts,
            1200 + rng.uniform(0, 80),
            "unusual_time",
            "03:17 热水器异常启动，家庭过去30天凌晨几乎从未使用热水器",
            "medium",
        )

    # 其它可评估异常
    extra = [
        (datetime(2026, 8, 7, 2, 40), 1, 1600, "unusual_time", "凌晨空调异常高功率运行", "high"),
        (datetime(2026, 8, 11, 15, 10), 4, 420, "habit_deviation", "工作日下午洗衣机异常启动", "low"),
        (datetime(2026, 8, 14, 21, 20), 1, 2100, "high_power", "晚高峰空调功率异常冲高", "high"),
        (datetime(2026, 8, 16, 0, 30), 6, 160, "long_running", "凌晨照明长时间未关", "medium"),
        (datetime(2026, 8, 18, 13, 5), 7, 240, "habit_deviation", "无人在家时电脑满载运行", "low"),
    ]
    for ts, device_id, power, kind, desc, severity in extra:
        for minutes in (0, 5):
            set_power(device_id, ts + timedelta(minutes=minutes), power, kind, desc, severity)
    return labels


def scale_day(energy_df: pd.DataFrame, day: datetime, target_kwh: float, shares: dict[str, float] | None) -> pd.DataFrame:
    mask = energy_df["timestamp"].dt.date == day.date()
    day_df = energy_df.loc[mask].copy()
    if day_df.empty:
        return energy_df
    if shares:
        for device in DEVICES:
            dmask = day_df["device_id"] == device["id"]
            target = target_kwh * shares[device["device_type"]]
            current = day_df.loc[dmask, "energy"].sum()
            factor = target / current if current > 0 else 1.0
            day_df.loc[dmask, "power"] *= factor
            day_df.loc[dmask, "energy"] *= factor
            day_df.loc[dmask, "current"] = day_df.loc[dmask, "power"] / day_df.loc[dmask, "voltage"]
    else:
        current = day_df["energy"].sum()
        factor = target_kwh / current if current > 0 else 1.0
        day_df["power"] *= factor
        day_df["energy"] *= factor
        day_df["current"] = day_df["power"] / day_df["voltage"]
    energy_df.loc[mask] = day_df
    return energy_df


def generate() -> dict:
    rng = np.random.default_rng(SEED)
    ts_list = timestamps()
    energy_rows = []
    env_rows = []
    behavior_rows = []
    weather_rows = []

    indoor = 27.5
    for idx, ts in enumerate(ts_list):
        is_weekend = ts.weekday() >= 5
        outdoor = outdoor_temp(ts, rng)
        occupancy, location, activity = occupancy_and_activity(ts, is_weekend)
        # 室内温度受室外和空调影响的简化热模型
        indoor += 0.04 * (outdoor - indoor)
        if occupancy >= 3:
            indoor += 0.02
        humidity = float(np.clip(62 + 0.4 * (outdoor - 30) + rng.normal(0, 1.2), 45, 85))
        weather = weather_label(outdoor, rng)
        light = 0.0
        hour = ts.hour + ts.minute / 60
        if 6 <= hour <= 19:
            light = max(0, 900 * np.sin((hour - 6) / 13 * np.pi) + rng.normal(0, 20))
        co2 = 420 + occupancy * 180 + rng.normal(0, 25)

        env_rows.append(
            {
                "user_id": 1,
                "timestamp": ts,
                "temperature": round(indoor, 2),
                "humidity": round(humidity, 2),
                "light": round(max(0, light), 1),
                "co2": round(max(380, co2), 1),
            }
        )
        behavior_rows.append(
            {
                "user_id": 1,
                "timestamp": ts,
                "location": location,
                "occupancy": occupancy,
                "activity": activity,
            }
        )
        weather_rows.append(
            {
                "timestamp": ts,
                "temperature": round(outdoor, 2),
                "humidity": round(float(np.clip(humidity - 8 + rng.normal(0, 3), 40, 90)), 2),
                "weather": weather,
                "wind_speed": round(float(np.clip(rng.normal(2.2, 0.7), 0.3, 6.5)), 2),
            }
        )

        for device in DEVICES:
            power = device_raw_power(
                device["device_type"],
                ts,
                indoor,
                occupancy,
                activity,
                idx,
                rng,
                device["rated_power"],
                is_weekend,
            )
            voltage = float(rng.normal(221.5, 1.4))
            energy_rows.append(
                {
                    "user_id": 1,
                    "device_id": device["id"],
                    "device_type": device["device_type"],
                    "timestamp": ts,
                    "power": max(0.0, power),
                    "voltage": voltage,
                    "current": max(0.0, power) / max(voltage, 1.0),
                    "energy": hour_energy(max(0.0, power)),
                }
            )
            if device["device_type"] == "air_conditioner" and power > 400:
                indoor -= 0.015

    energy_df = pd.DataFrame(energy_rows)
    energy_df["timestamp"] = pd.to_datetime(energy_df["timestamp"])

    # 先校准日常曲线，再植入异常，避免缩放把 Demo 异常点冲掉
    for offset in range(2, 7):
        day = DEMO_DATE - timedelta(days=offset)
        scale_day(energy_df, day, 16.72, None)
    scale_day(energy_df, DEMO_DATE - timedelta(days=1), YESTERDAY_TARGET_KWH, None)
    scale_day(energy_df, DEMO_DATE, TODAY_TARGET_KWH, DEMO_SHARES)

    energy_rows = energy_df.to_dict(orient="records")
    for row in energy_rows:
        if not isinstance(row["timestamp"], datetime):
            row["timestamp"] = pd.to_datetime(row["timestamp"]).to_pydatetime()
    labels = inject_anomalies(energy_rows, rng)
    energy_df = pd.DataFrame(energy_rows)
    energy_df["timestamp"] = pd.to_datetime(energy_df["timestamp"])

    env_df = pd.DataFrame(env_rows)
    behavior_df = pd.DataFrame(behavior_rows)
    weather_df = pd.DataFrame(weather_rows)
    users_df = pd.DataFrame([HOUSEHOLD])
    devices_df = pd.DataFrame(
        [{**d, "user_id": 1, "status": "on"} for d in DEVICES]
    )
    labels_df = pd.DataFrame(labels)

    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    users_df.to_csv(DEMO_DIR / "users.csv", index=False)
    devices_df.to_csv(DEMO_DIR / "devices.csv", index=False)
    energy_df.drop(columns=["device_type"]).to_csv(DEMO_DIR / "energy_records.csv", index=False)
    env_df.to_csv(DEMO_DIR / "environment_records.csv", index=False)
    behavior_df.to_csv(DEMO_DIR / "behavior_records.csv", index=False)
    weather_df.to_csv(DEMO_DIR / "weather_records.csv", index=False)
    labels_df.to_csv(DEMO_DIR / "anomaly_labels.csv", index=False)

    today_mask = energy_df["timestamp"].dt.date == DEMO_DATE.date()
    today_total = float(energy_df.loc[today_mask, "energy"].sum())
    share_map = (
        energy_df.loc[today_mask]
        .groupby("device_id")["energy"]
        .sum()
        .to_dict()
    )
    type_map = {d["id"]: d["device_type"] for d in DEVICES}
    shares = {type_map[i]: round(v / today_total * 100, 2) for i, v in share_map.items()}
    summary = {
        "days": DAYS,
        "interval_minutes": INTERVAL_MINUTES,
        "points": len(ts_list),
        "energy_rows": int(len(energy_df)),
        "demo_date": DEMO_DATE.strftime("%Y-%m-%d"),
        "today_energy_kwh": round(today_total, 3),
        "yesterday_energy_kwh": round(
            float(energy_df.loc[energy_df["timestamp"].dt.date == (DEMO_DATE - timedelta(days=1)).date(), "energy"].sum()),
            3,
        ),
        "device_share_percent": shares,
        "injected_anomalies": int(labels_df["timestamp"].nunique()) if not labels_df.empty else 0,
    }
    (DEMO_DIR / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


def hour_energy(power_w: float) -> float:
    return power_w / 1000.0 * (INTERVAL_MINUTES / 60.0)


if __name__ == "__main__":
    generate()
