import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Anomaly, BehaviorRecord, EnergyRecord, EnvironmentRecord, WeatherRecord
from app.core.config import PROJECT_ROOT
from app.services.anomaly_service import latest_anomalies
from app.services.device_service import device_energy_breakdown
from app.services.energy_service import day_range, demo_day, today_stats
from app.services.profile_service import assistant_summary, get_energy_score, get_profile, get_saving_potential
from app.utils.pricing import carbon_of, tou_period, tou_price


def load_today_frame(db: Session, user_id: int) -> pd.DataFrame:
    start, end = day_range(demo_day())
    energy_rows = db.execute(
        select(EnergyRecord.timestamp, EnergyRecord.power, EnergyRecord.energy).where(
            EnergyRecord.user_id == user_id,
            EnergyRecord.timestamp >= start,
            EnergyRecord.timestamp < end,
        )
    ).all()
    if not energy_rows:
        return pd.DataFrame()
    energy = pd.DataFrame(energy_rows, columns=["timestamp", "power", "energy"])
    energy["timestamp"] = pd.to_datetime(energy["timestamp"])
    total = energy.groupby("timestamp", as_index=False).agg(power=("power", "sum"), energy=("energy", "sum"))

    env_rows = db.execute(
        select(
            EnvironmentRecord.timestamp,
            EnvironmentRecord.temperature,
            EnvironmentRecord.humidity,
            EnvironmentRecord.light,
            EnvironmentRecord.co2,
        ).where(
            EnvironmentRecord.user_id == user_id,
            EnvironmentRecord.timestamp >= start,
            EnvironmentRecord.timestamp < end,
        )
    ).all()
    env = pd.DataFrame(env_rows, columns=["timestamp", "temperature", "humidity", "light", "co2"])
    if not env.empty:
        env["timestamp"] = pd.to_datetime(env["timestamp"])

    beh_rows = db.execute(
        select(
            BehaviorRecord.timestamp,
            BehaviorRecord.occupancy,
            BehaviorRecord.activity,
            BehaviorRecord.location,
        ).where(
            BehaviorRecord.user_id == user_id,
            BehaviorRecord.timestamp >= start,
            BehaviorRecord.timestamp < end,
        )
    ).all()
    beh = pd.DataFrame(beh_rows, columns=["timestamp", "occupancy", "activity", "location"])
    if not beh.empty:
        beh["timestamp"] = pd.to_datetime(beh["timestamp"])

    weather_rows = db.execute(
        select(
            WeatherRecord.timestamp,
            WeatherRecord.temperature,
            WeatherRecord.weather,
            WeatherRecord.humidity,
        ).where(WeatherRecord.timestamp >= start, WeatherRecord.timestamp < end)
    ).all()
    weather = pd.DataFrame(weather_rows, columns=["timestamp", "outdoor_temp", "weather", "outdoor_humidity"])
    if not weather.empty:
        weather["timestamp"] = pd.to_datetime(weather["timestamp"])

    frame = total.merge(env, on="timestamp", how="left").merge(beh, on="timestamp", how="left")
    if not weather.empty:
        frame = frame.merge(weather, on="timestamp", how="left")
    frame = frame.sort_values("timestamp").reset_index(drop=True)
    frame["hour"] = frame["timestamp"].dt.hour
    frame["period"] = frame["hour"].map(tou_period)
    frame["price"] = frame["hour"].map(tou_price)
    frame["cost"] = frame["energy"] * frame["price"]
    return frame


def tou_breakdown(frame: pd.DataFrame) -> dict:
    empty = {
        "peak_kwh": 0.0,
        "flat_kwh": 0.0,
        "valley_kwh": 0.0,
        "peak_cost": 0.0,
        "flat_cost": 0.0,
        "valley_cost": 0.0,
        "total_cost": 0.0,
        "avg_price": 0.0,
        "peak_share": 0.0,
    }
    if frame.empty:
        return empty
    grouped = frame.groupby("period")[["energy", "cost"]].sum()
    peak = float(grouped.loc["peak", "energy"]) if "peak" in grouped.index else 0.0
    flat = float(grouped.loc["flat", "energy"]) if "flat" in grouped.index else 0.0
    valley = float(grouped.loc["valley", "energy"]) if "valley" in grouped.index else 0.0
    total = peak + flat + valley
    total_cost = float(frame["cost"].sum())
    return {
        "peak_kwh": round(peak, 3),
        "flat_kwh": round(flat, 3),
        "valley_kwh": round(valley, 3),
        "peak_cost": round(float(grouped.loc["peak", "cost"]) if "peak" in grouped.index else 0.0, 2),
        "flat_cost": round(float(grouped.loc["flat", "cost"]) if "flat" in grouped.index else 0.0, 2),
        "valley_cost": round(float(grouped.loc["valley", "cost"]) if "valley" in grouped.index else 0.0, 2),
        "total_cost": round(total_cost, 2),
        "avg_price": round(total_cost / total, 3) if total else 0.0,
        "peak_share": round(peak / total * 100, 1) if total else 0.0,
    }


def correlation_report(frame: pd.DataFrame) -> dict:
    if frame.empty or len(frame) < 12:
        return {
            "power_vs_temperature": 0.0,
            "power_vs_occupancy": 0.0,
            "power_vs_outdoor": 0.0,
            "hourly": [],
        }
    def corr(a: str, b: str) -> float:
        sub = frame[[a, b]].dropna()
        if len(sub) < 8:
            return 0.0
        value = sub[a].corr(sub[b])
        return round(float(value) if pd.notna(value) else 0.0, 3)

    agg_map = {
        "power": ("power", "mean"),
        "energy": ("energy", "sum"),
        "temperature": ("temperature", "mean"),
        "occupancy": ("occupancy", "mean"),
    }
    if "outdoor_temp" in frame.columns:
        agg_map["outdoor_temp"] = ("outdoor_temp", "mean")
    hourly = (
        frame.assign(hour_ts=frame["timestamp"].dt.floor("h"))
        .groupby("hour_ts", as_index=False)
        .agg(**agg_map)
    )
    points = []
    for _, row in hourly.iterrows():
        points.append(
            {
                "timestamp": row["hour_ts"].to_pydatetime() if hasattr(row["hour_ts"], "to_pydatetime") else row["hour_ts"],
                "power": round(float(row["power"]), 1),
                "energy": round(float(row["energy"]), 3),
                "temperature": round(float(row["temperature"]), 1) if pd.notna(row["temperature"]) else None,
                "occupancy": round(float(row["occupancy"]), 2) if pd.notna(row["occupancy"]) else None,
                "outdoor_temp": round(float(row["outdoor_temp"]), 1)
                if "outdoor_temp" in row and pd.notna(row.get("outdoor_temp"))
                else None,
            }
        )
    return {
        "power_vs_temperature": corr("power", "temperature"),
        "power_vs_occupancy": corr("power", "occupancy"),
        "power_vs_outdoor": corr("power", "outdoor_temp") if "outdoor_temp" in frame.columns else 0.0,
        "hourly": points,
    }


def build_insights(db: Session, user_id: int, frame: pd.DataFrame, stats: dict, tou: dict) -> list[dict]:
    items: list[dict] = []
    if stats["compared_yesterday_percent"] is not None:
        direction = "下降" if stats["compared_yesterday_percent"] < 0 else "上升"
        items.append(
            {
                "level": "info" if stats["compared_yesterday_percent"] < 0 else "warn",
                "title": f"今日用电较昨日{direction} {abs(stats['compared_yesterday_percent']):.1f}%",
                "detail": f"今日 {stats['today_energy']:.2f} kWh，昨日 {stats['yesterday_energy']:.2f} kWh。",
            }
        )
    if tou["peak_share"] >= 35:
        items.append(
            {
                "level": "warn",
                "title": f"晚高峰用电占比 {tou['peak_share']:.1f}%",
                "detail": f"18:00-22:00 消耗 {tou['peak_kwh']:.2f} kWh，电费 {tou['peak_cost']:.2f} 元，具备错峰空间。",
            }
        )
    if not frame.empty and "occupancy" in frame:
        away = frame[frame["occupancy"].fillna(0) <= 1]
        waste = float(away["energy"].sum()) if not away.empty else 0.0
        if waste >= 1.5:
            items.append(
                {
                    "level": "warn",
                    "title": "低占用时段仍有明显用电",
                    "detail": f"家中少于 2 人时仍消耗 {waste:.2f} kWh，优先检查空调、照明和电脑待机。",
                }
            )
    latest = latest_anomalies(db, user_id, limit=1)
    if latest:
        items.append(
            {
                "level": "alert",
                "title": "检测到异常用能事件",
                "detail": latest[0]["description"],
            }
        )
    items.append(
        {
            "level": "ok",
            "title": f"主要耗能来自{stats['main_device']}",
            "detail": f"占比约 {stats['main_device_share']:.1f}%。提高设定温度或缩短运行时间，通常是收益最大的动作。",
        }
    )
    return items[:6]


def digital_twin(db: Session, user_id: int, frame: pd.DataFrame) -> dict:
    import json

    devices = device_energy_breakdown(db, user_id)
    running = [d for d in devices if d["current_power"] > 15]
    if frame.empty:
        return {
            "as_of": None,
            "occupancy": 0,
            "activity": "unknown",
            "location": "unknown",
            "indoor_temp": None,
            "humidity": None,
            "co2": None,
            "weather": None,
            "outdoor_temp": None,
            "current_power": 0,
            "running_devices": running,
        }
    target = demo_day().replace(hour=20, minute=30)
    idx = (frame["timestamp"] - pd.Timestamp(target)).abs().idxmin()
    row = frame.loc[idx]
    return {
        "as_of": row["timestamp"].to_pydatetime() if hasattr(row["timestamp"], "to_pydatetime") else row["timestamp"],
        "occupancy": int(row.get("occupancy") or 0),
        "activity": str(row.get("activity") or "unknown"),
        "location": str(row.get("location") or "unknown"),
        "indoor_temp": round(float(row["temperature"]), 1) if pd.notna(row.get("temperature")) else None,
        "humidity": round(float(row["humidity"]), 1) if pd.notna(row.get("humidity")) else None,
        "co2": round(float(row["co2"]), 0) if pd.notna(row.get("co2")) else None,
        "weather": str(row["weather"]) if "weather" in row and pd.notna(row.get("weather")) else None,
        "outdoor_temp": round(float(row["outdoor_temp"]), 1) if "outdoor_temp" in row and pd.notna(row.get("outdoor_temp")) else None,
        "current_power": round(float(row["power"]), 1),
        "running_devices": running,
    }


def timeline_points(frame: pd.DataFrame) -> list[dict]:
    if frame.empty:
        return []
    sampled = frame.iloc[::3]
    points = []
    for _, row in sampled.iterrows():
        points.append(
            {
                "timestamp": row["timestamp"].to_pydatetime() if hasattr(row["timestamp"], "to_pydatetime") else row["timestamp"],
                "power": round(float(row["power"]), 1),
                "energy": round(float(row["energy"]), 4),
                "occupancy": int(row["occupancy"]) if pd.notna(row.get("occupancy")) else 0,
                "temperature": round(float(row["temperature"]), 1) if pd.notna(row.get("temperature")) else None,
                "period": row["period"],
            }
        )
    return points


ROOM_DEVICE_MAP = {
    "客厅": ["air_conditioner", "television", "other"],
    "厨房": ["refrigerator"],
    "卫生间": ["water_heater", "washing_machine"],
    "书房": ["computer"],
    "全屋": ["lighting"],
}


def month_heatmap(db: Session, user_id: int) -> list[dict]:
    from datetime import timedelta

    from app.models import EnergyRecord

    start, _ = day_range(demo_day() - timedelta(days=29))
    _, end = day_range(demo_day())
    rows = db.execute(
        select(EnergyRecord.timestamp, EnergyRecord.energy).where(
            EnergyRecord.user_id == user_id,
            EnergyRecord.timestamp >= start,
            EnergyRecord.timestamp < end,
        )
    ).all()
    if not rows:
        return []
    frame = pd.DataFrame(rows, columns=["timestamp", "energy"])
    frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    daily = frame.groupby(frame["timestamp"].dt.date)["energy"].sum().reset_index()
    return [
        {"date": str(d), "energy": round(float(v), 2)}
        for d, v in daily.itertuples(index=False)
    ]


def _forecast_faq(forecast: dict) -> str:
    r2 = forecast.get("R2")
    mape = forecast.get("MAPE")
    if r2 is None or mape is None:
        return "预测指标见模型实验舱。负荷识别不是总表 NILM。"
    mape_text = f"{mape:.2f}" if isinstance(mape, (int, float)) else str(mape)
    return f"R² {r2}，MAPE {mape_text}%。只报 MAE/RMSE/MAPE/R²，不用 100-MAPE 当准确率。负荷识别不是总表 NILM。"


def build_showcase(
    db: Session,
    user_id: int,
    frame: pd.DataFrame,
    stats: dict,
    tou: dict,
    carbon: float,
    potential: dict,
    score: dict,
) -> dict:
    import json

    devices = device_energy_breakdown(db, user_id)
    night = frame[frame["hour"] < 6] if not frame.empty else pd.DataFrame()
    night_kwh = float(night["energy"].sum()) if not night.empty else 0.0
    away = frame[frame["occupancy"].fillna(0) <= 1] if not frame.empty else pd.DataFrame()
    away_kwh = float(away["energy"].sum()) if not away.empty else 0.0
    metrics = {}
    metrics_path = PROJECT_ROOT / "models" / "metrics.json"
    if metrics_path.exists():
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    forecast = metrics.get("forecast", {})
    room_loads = []
    for room, types in ROOM_DEVICE_MAP.items():
        energy = sum(d["today_energy"] for d in devices if d["device_type"] in types)
        running = [d["name"] for d in devices if d["device_type"] in types and d["current_power"] > 15]
        room_loads.append(
            {
                "name": room,
                "energy": round(energy, 2),
                "running": running,
                "active": bool(running),
            }
        )
    sankey_links = [
        {"source": "电网", "target": d["name"], "value": round(d["today_energy"], 3)}
        for d in devices
        if d["today_energy"] > 0
    ]
    story = [
        {"time": "03:17", "title": "异常诊断", "detail": "热水器凌晨启动，与30日作息显著偏离。"},
        {"time": "07:00", "title": "早高峰", "detail": "起床、热水和照明叠加，谷段电价仍较低。"},
        {"time": "18:00", "title": "回家爬升", "detail": "全家回到客厅，空调成为第一负荷。"},
        {"time": "20:30", "title": "当前快照", "detail": f"功率 {stats['current_power']/1000:.2f} kW，{stats['main_device']} 占比 {stats['main_device_share']:.1f}%。"},
        {"time": "21:00", "title": "决策窗口", "detail": f"高峰已占总电量 {tou['peak_share']:.1f}%，现在调整空调收益最大。"},
    ]
    highlights = [
        {
            "tag": "多模态",
            "title": "电、环境、行为、电价同屏融合",
            "detail": f"功率与占用相关 {correlation_report(frame)['power_vs_occupancy'] if not frame.empty else 0:.2f}",
        },
        {
            "tag": "真模型",
            "title": f"{forecast.get('model_name', 'XGBoost')} 预测",
            "detail": f"R² {forecast.get('R2', '--')} · MAE {forecast.get('MAE', '--')} W",
        },
        {
            "tag": "结构",
            "title": "总量不差，结构有浪费",
            "detail": f"今日低于近 30 日中位，但高峰仍占 {tou['peak_share']:.1f}%",
        },
        {
            "tag": "可执行",
            "title": "策略同时算电量、电费、碳排",
            "detail": f"节能潜力 {potential['total_saving_percent']:.1f}%",
        },
    ]
    heatmap = month_heatmap(db, user_id)
    replay = replay_frames(frame, potential["total_saving_percent"])
    return {
        "highlights": highlights,
        "story": story,
        "heatmap": heatmap,
        "sankey": {"links": sankey_links},
        "rooms": room_loads,
        "equivalents": {
            "carbon_kg": carbon,
            "car_km": round(carbon / 0.21, 1),
            "tree_days": round(carbon / (21 / 365), 1),
            "night_kwh": round(night_kwh, 2),
            "away_kwh": round(away_kwh, 2),
            "score": score.get("energy_score"),
        },
        "questions": [
            {"q": "为什么耗电？", "a": f"主要来自{stats['main_device']}，占 {stats['main_device_share']:.1f}%。"},
            {"q": "哪里浪费？", "a": f"低占用仍用 {away_kwh:.2f} kWh，凌晨浪费 {night_kwh:.2f} kWh。"},
            {"q": "怎么节能？", "a": "先把空调 24℃ 调到 26℃，再关掉热水器夜间加热。"},
            {"q": "预测准不准？", "a": _forecast_faq(forecast)},
        ],
        "replay": replay,
        "dispatch": dispatch_plan(replay),
        "optimized_curve": [
            {"hour": r["hour"], "label": r["label"], "actual": r["power"], "optimized": r["optimized_power"]}
            for r in replay
        ],
        "benchmark": build_benchmark(heatmap, stats["today_energy"], carbon, tou),
    }


def hour_action(hour: int, power: float, period: str, occupancy: float) -> str:
    if hour < 6 and power > 800:
        return "关闭夜间高功率设备"
    if period == "peak" and power > 1600:
        return "错峰降低空调"
    if occupancy <= 1 and power > 700:
        return "无人场景降负荷"
    return "保持"


def replay_frames(frame: pd.DataFrame, saving_percent: float = 12.0) -> list[dict]:
    if frame.empty:
        return []
    hourly_energy = frame.groupby("hour")["energy"].sum()
    hourly_cost = frame.groupby("hour")["cost"].sum() if "cost" in frame.columns else pd.Series(dtype=float)
    raw = []
    for hour in range(24):
        part = frame[frame["hour"] == hour]
        if part.empty:
            continue
        row = part.iloc[len(part) // 2]
        period = str(row["period"])
        occupancy = float(row.get("occupancy") or 0)
        power = float(row["power"])
        peak_in_hour = float(part["power"].max())
        action = hour_action(hour, peak_in_hour, period, occupancy)
        raw.append(
            {
                "hour": hour,
                "label": f"{hour:02d}:00",
                "power": round(power, 1),
                "energy": round(float(hourly_energy.get(hour, 0.0)), 3),
                "cost": round(float(hourly_cost.get(hour, 0.0)), 2) if not hourly_cost.empty else 0.0,
                "occupancy": int(occupancy),
                "activity": str(row.get("activity") or ""),
                "location": str(row.get("location") or ""),
                "temperature": round(float(row["temperature"]), 1) if pd.notna(row.get("temperature")) else None,
                "period": period,
                "price": round(float(row["price"]), 2),
                "action": action,
                "alert": hour == 3 and peak_in_hour > 800,
            }
        )
    factors = allocate_saving_factors(raw, saving_percent)
    energy_so_far = 0.0
    cost_so_far = 0.0
    rows = []
    for item, factor in zip(raw, factors):
        energy_so_far += item["energy"]
        cost_so_far += item["cost"]
        optimized_power = round(item["power"] * factor, 1)
        brief = f"{item['label']} {item['location'] or '家中'}正在{item['activity'] or '待机'}，功率 {item['power']:.0f} W。"
        if item["action"] != "保持":
            brief += f"建议{item['action']}。"
        if item["alert"]:
            brief += "此时段与热水器异常启动重合。"
        rows.append(
            {
                **item,
                "optimized_power": optimized_power,
                "energy_so_far": round(energy_so_far, 3),
                "cost_so_far": round(cost_so_far, 2),
                "carbon_so_far": carbon_of(energy_so_far),
                "brief": brief,
            }
        )
    return rows


def allocate_saving_factors(hours: list[dict], saving_percent: float) -> list[float]:
    if not hours:
        return []
    total_energy = sum(h["energy"] for h in hours) or 1.0
    target = total_energy * max(saving_percent, 0.0) / 100.0
    weights = []
    for item in hours:
        weight = max(item["energy"], 0.001)
        if item["hour"] < 6:
            weight *= 2.4
        elif item["period"] == "peak":
            weight *= 1.9
        elif item["occupancy"] <= 1:
            weight *= 1.45
        if item["action"] != "保持":
            weight *= 1.2
        weights.append(weight)
    total_w = sum(weights) or 1.0
    factors = []
    for item, weight in zip(hours, weights):
        cut = min(target * weight / total_w, item["energy"] * 0.42)
        factor = 1.0 - cut / item["energy"] if item["energy"] else 1.0
        factors.append(max(0.58, min(1.0, factor)))
    return factors


def dispatch_plan(replay: list[dict]) -> list[dict]:
    plan = []
    for row in replay:
        if row["action"] != "保持":
            plan.append(
                {
                    "hour": row["hour"],
                    "label": row["label"],
                    "action": row["action"],
                    "power": row["power"],
                    "period": row["period"],
                    "reason": row.get("brief") or f"{row['label']} 功率 {row['power']:.0f}W，占用 {row['occupancy']} 人，电价 {row['price']} 元/kWh。",
                }
            )
    return plan[:8]


def build_benchmark(heatmap: list[dict], today_energy: float, carbon: float, tou: dict) -> dict:
    values = [float(item["energy"]) for item in heatmap]
    if not values:
        return {
            "today_kwh": round(today_energy, 2),
            "month_median_kwh": 0.0,
            "vs_median_percent": 0.0,
            "percentile": 0.0,
            "label": "样本不足",
            "peak_share": tou.get("peak_share", 0),
            "carbon_kg": carbon,
        }
    median = float(pd.Series(values).median())
    rank = sum(1 for value in values if value <= today_energy)
    percentile = round(rank / len(values) * 100, 1)
    if today_energy > median * 1.05:
        label = "高于近 30 日中位"
    elif today_energy < median * 0.95:
        label = "低于近 30 日中位"
    else:
        label = "接近近 30 日中位"
    return {
        "today_kwh": round(today_energy, 2),
        "month_median_kwh": round(median, 2),
        "vs_median_percent": round((today_energy - median) / median * 100, 1) if median else 0.0,
        "percentile": percentile,
        "label": label,
        "peak_share": tou.get("peak_share", 0),
        "carbon_kg": carbon,
    }


def radar_scores(db: Session, user_id: int, tou: dict, score: dict, potential: float, twin: dict) -> dict:
    indoor = twin.get("indoor_temp")
    if indoor is None:
        comfort = 78.0
        comfort_note = "演示时刻室内温度缺失，舒适维按中性 78 计"
    else:
        comfort = round(max(40.0, min(100.0, 100.0 - abs(float(indoor) - 26.0) * 8.0)), 1)
        comfort_note = f"按室内 {indoor}℃ 相对夏季舒适带 26℃ 计，过冷过热都扣分"
    anomaly_n = (
        db.query(Anomaly)
        .filter(Anomaly.user_id == user_id, Anomaly.severity.in_(["medium", "high", "critical"]))
        .count()
    )
    peak_share = float(tou.get("peak_share") or 0)
    return {
        "efficiency": float(score.get("energy_score") or 0),
        "offpeak": round(max(0.0, 100.0 - peak_share), 1),
        "comfort": comfort,
        "anomaly_control": round(max(40.0, 100.0 - min(40.0, anomaly_n * 3.5)), 1),
        "potential": round(min(100.0, float(potential or 0) * 6.0), 1),
        "notes": {
            "efficiency": "由当日能耗、峰值、异常和浪费项扣分得到",
            "offpeak": f"100 减去高峰电量占比 {peak_share}%",
            "comfort": comfort_note,
            "anomaly_control": f"按本户中高严重异常 {anomaly_n} 条扣分，不是写死的 82",
            "potential": f"今日可识别节能潜力 {float(potential or 0):.1f}%，按比例映射到 0–100",
        },
    }


def get_dashboard_insights(db: Session, user_id: int) -> dict:
    from app.services.strategy_service import top_strategies

    stats = today_stats(db, user_id)
    frame = load_today_frame(db, user_id)
    tou = tou_breakdown(frame)
    corr = correlation_report(frame)
    score = get_energy_score(db, user_id)
    potential = get_saving_potential(db, user_id)
    profile = get_profile(db, user_id)
    carbon = carbon_of(stats["today_energy"])
    twin = digital_twin(db, user_id, frame)
    radar = radar_scores(db, user_id, tou, score, potential["total_saving_percent"], twin)
    return {
        "stats": stats,
        "tou": tou,
        "carbon_kg": carbon,
        "month_carbon_kg": carbon_of(stats["month_energy"]),
        "energy_score": score,
        "saving_potential": potential["total_saving_percent"],
        "insights": build_insights(db, user_id, frame, stats, tou),
        "correlation": corr,
        "twin": twin,
        "radar": radar,
        "timeline": timeline_points(frame),
        "top_strategies": top_strategies(db, user_id, 3),
        "profile": profile,
        "assistant": assistant_summary(db, user_id),
        "showcase": build_showcase(db, user_id, frame, stats, tou, carbon, potential, score),
    }


def chat_with_assistant(db: Session, user_id: int, question: str) -> dict:
    payload = get_dashboard_insights(db, user_id)
    stats = payload["stats"]
    tou = payload["tou"]
    twin = payload["twin"]
    q = (question or "").strip()
    lower = q.lower()

    def answer(text: str, topic: str) -> dict:
        return {"question": q, "topic": topic, "answer": text, "today_energy": stats["today_energy"]}

    if any(k in q for k in ("怎么用", "使用说明", "操作指南", "说明书", "不会用", "如何使用")):
        return answer(
            "请打开左侧或顶栏的「使用说明」。五分钟路径：总览看今天花了多少 → 拖回放到 03:00 再回到 20:30 → 能耗看谁在用 → 异常看 03:17 热水器 → 对右下角管家说「执行今晚节能方案」。"
            "开关是模拟执行，不改历史曲线；冰箱不会关；语音请用本机 Chrome 打开 http://127.0.0.1:5174/ 。"
            "右下角「使用演示」是带练导览，文字说明请看本页。",
            "guide",
        )
    if any(k in q for k in ("数据从哪", "多模态", "从哪来", "传感器", "移植", "电表接入", "真实数据")):
        from app.services.source_service import get_source_map

        src = get_source_map(db, user_id)
        names = "、".join(m["label"] for m in src["modalities"] if m["active"])
        align = src["alignment"]["percent"]
        return answer(
            f"多模态不是图像或语音，是电力、环境、行为、天气四路时序。当前在库里对齐 {names}，演示日对齐 {align}%。"
            f"演示由 CSV 管道灌进标准表；移植时换采集适配器和本地电价，再按户重训模型。"
            f"{src['honesty']}",
            "sources",
        )
    if any(k in q for k in ("准不准", "MAPE", "准确率", "R²", "R2", "特征重要", "负荷识别", "NILM", "模型实验", "F1", "实验指标")):
        from app.services.model_lab import speech_metrics

        return answer(speech_metrics(), "models")
    if any(k in q for k in ("电网", "邀约", "削峰")):
        from app.services.life_service import get_life_os

        life = get_life_os(db, user_id)
        dr = life["demand"]
        return answer(
            f"{dr['title']}，窗口 {dr['window']}，目标削峰 {dr['target_percent']}%。"
            f"当前约 {dr['current_w']} W，应下后管家按节能方案执行。"
            f"{dr['note']}",
            "demand",
        )
    if any(k in q for k in ("待机", "凌晨浪费", "谁在偷电")):
        from app.services.life_service import get_life_os

        life = get_life_os(db, user_id)
        sb = life["standby"]
        names = "、".join(x["name"] for x in sb["items"][:3]) or "无明显非刚需"
        return answer(
            f"00:00–06:00 非刚需约 {sb['wasted_kwh']} kWh（冰箱不算）。{names}。{sb['note']}",
            "standby",
        )
    if any(k in q for k in ("明天", "明早", "接下来高峰")):
        from app.services.life_service import get_life_os

        return answer(get_life_os(db, user_id)["tomorrow"]["advice"], "tomorrow")
    if any(k in q for k in ("为什么", "耗电", "谁在用", "占比")):
        return answer(
            f"今天用电 {stats['today_energy']:.2f} kWh，第一大负荷是{stats['main_device']}，约占 {stats['main_device_share']:.1f}%。"
            f"晚高峰占比 {tou['peak_share']:.1f}%。室内约 {twin.get('indoor_temp')}℃，占用 {twin.get('occupancy')} 人，空调和环境温度是主要驱动因素。",
            "cause",
        )
    if any(k in q for k in ("浪费", "异常", "热水器", "凌晨")):
        latest = latest_anomalies(db, user_id, limit=1)
        extra = latest[0]["description"] if latest else "当前没有更高优先级的异常。"
        return answer(
            f"浪费主要来自高峰叠加、低占用运行和异常启动。{extra}",
            "waste",
        )
    if any(k in q for k in ("怎么", "节能", "建议", "策略")):
        titles = "；".join(s.title for s in payload["top_strategies"][:3]) or "暂无策略"
        return answer(
            f"系统当前优先建议：{titles}。综合节能潜力约 {payload['saving_potential']:.1f}%，可在策略页勾选后模拟效果。",
            "action",
        )
    if any(k in q for k in ("预测", "未来", "今晚")):
        return answer("未来 6 至 24 小时负荷由 XGBoost 按时序特征递推预测，可在「能耗预测」页查看真实值与预测值对比。", "forecast")
    if any(k in q for k in ("电费", "多少钱", "峰谷")):
        return answer(
            f"按成都峰谷电价估算，今日电费约 {tou['total_cost']:.2f} 元。峰段 {tou['peak_cost']:.2f} 元，平段 {tou['flat_cost']:.2f} 元，谷段 {tou['valley_cost']:.2f} 元。",
            "bill",
        )
    if any(k in q for k in ("碳", "排放", "环保")):
        return answer(
            f"今日用电对应约 {payload['carbon_kg']:.2f} kg CO₂e，本月累计约 {payload['month_carbon_kg']:.1f} kg。降低高峰空调负荷是减碳最快的路径。",
            "carbon",
        )
    if any(k in q for k in ("对比", "中位", "对标", "偏高", "百分位")):
        bench = payload.get("showcase", {}).get("benchmark") or {}
        return answer(
            f"今日用电 {bench.get('today_kwh', stats['today_energy'])} kWh，"
            f"相对近 30 日中位 {bench.get('month_median_kwh', '--')} kWh {bench.get('label', '')}，"
            f"约处于第 {bench.get('percentile', '--')} 百分位。高峰占比 {tou['peak_share']:.1f}%。",
            "benchmark",
        )
    summary = payload["assistant"]["summary"]
    return answer(summary, "overview")
