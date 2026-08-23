import pandas as pd
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Device, EnergyRecord
from app.models.actuator import ButlerLog, DeviceActuator
from app.models.life import HomeRule
from app.services.anomaly_service import latest_anomalies
from app.services.device_service import device_energy_breakdown
from app.services.energy_service import day_range, demo_day, today_stats
from app.services.insight_service import load_today_frame, month_heatmap, tou_breakdown
from app.services.life_board import (
    analyze_loads,
    build_challenge,
    build_comfort,
    build_defense,
    build_demand,
    build_missions,
    build_schedule,
    build_shift,
    build_standby,
    build_tomorrow,
    get_flags,
)
from app.utils.pricing import carbon_of, tou_period, tou_price

PERIOD_CN = {"peak": "高峰", "flat": "平时", "valley": "谷时"}
DEFAULT_RULES = [
    {
        "key": "peak_guard",
        "title": "高峰守门",
        "when": "进入 18:00-22:00 高峰电价",
        "then": "提醒降空调、避开洗衣和电脑",
        "default": True,
    },
    {
        "key": "night_heater",
        "title": "凌晨热水保护",
        "when": "23:00-06:00 热水器高功率",
        "then": "允许管家关闭夜间加热",
        "default": True,
    },
    {
        "key": "away_light",
        "title": "低占用关灯",
        "when": "在家少于 2 人且照明仍开",
        "then": "关闭非必要照明",
        "default": True,
    },
    {
        "key": "valley_wash",
        "title": "谷电洗衣",
        "when": "洗衣机出现在高峰时段",
        "then": "建议改到 23:00 以后",
        "default": True,
    },
    {
        "key": "ac_setpoint",
        "title": "空调 26℃ 公约",
        "when": "高峰制冷且设定低于 26℃",
        "then": "提示上调设定温度",
        "default": False,
    },
]


def _as_of():
    return demo_day().replace(hour=20, minute=30)


def _next_period(hour: int, minute: int) -> tuple[str, str, int]:
    now_min = hour * 60 + minute
    schedule = [
        (7 * 60, "flat", "07:00"),
        (18 * 60, "peak", "18:00"),
        (22 * 60, "flat", "22:00"),
        (23 * 60, "valley", "23:00"),
        (24 * 60 + 7 * 60, "flat", "07:00"),
    ]
    for start, period, label in schedule:
        if start > now_min:
            return period, label, start - now_min
    return "flat", "07:00", 24 * 60 - now_min + 7 * 60


def build_clock() -> dict:
    now = _as_of()
    period = tou_period(now.hour)
    nxt_period, nxt_label, minutes = _next_period(now.hour, now.minute)
    advice = {
        "peak": f"高峰还剩 {minutes} 分钟，把空调维持 26℃ 最划算。",
        "flat": f"{minutes} 分钟后进入下一电价段，非刚需家电可以再等等。",
        "valley": "现在是谷电，适合洗衣、加热水。",
    }[period]
    return {
        "as_of": now.strftime("%H:%M"),
        "period": period,
        "period_label": PERIOD_CN[period],
        "price": tou_price(now.hour),
        "next_period": nxt_period,
        "next_label": PERIOD_CN[nxt_period],
        "next_at": nxt_label,
        "minutes_left": minutes,
        "advice": advice,
    }


def nilm_hourly(db: Session, user_id: int) -> dict:
    start, end = day_range(demo_day())
    rows = db.execute(
        select(EnergyRecord.timestamp, Device.name, EnergyRecord.energy).join(
            Device, Device.id == EnergyRecord.device_id
        ).where(
            EnergyRecord.user_id == user_id,
            EnergyRecord.timestamp >= start,
            EnergyRecord.timestamp < end,
        )
    ).all()
    if not rows:
        return {"hours": [f"{h:02d}:00" for h in range(24)], "series": []}
    frame = pd.DataFrame(rows, columns=["timestamp", "name", "energy"])
    frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    frame["hour"] = frame["timestamp"].dt.hour
    pivot = frame.groupby(["hour", "name"])["energy"].sum().unstack(fill_value=0).reindex(range(24), fill_value=0)
    hours = [f"{h:02d}:00" for h in range(24)]
    series = [{"name": str(col), "data": [round(float(pivot.loc[h, col]), 3) for h in range(24)]} for col in pivot.columns]
    return {"hours": hours, "series": series}


def family_split(stats: dict) -> list[dict]:
    energy = stats.get("device_energy") or {}
    total = float(stats.get("today_energy") or 0)
    computer = float(energy.get("computer") or 0)
    tv = float(energy.get("television") or 0)
    lighting = float(energy.get("lighting") or 0)
    dad_d = computer
    mom_d = lighting * 0.30
    kid1_d = tv * 0.40
    kid2_d = tv * 0.30 + lighting * 0.20
    assigned = dad_d + mom_d + kid1_d + kid2_d
    shared = max(0.0, total - assigned)
    each = shared / 4
    rows = [
        {"name": "爸爸", "role": "工作日书房办公", "direct_kwh": round(dad_d, 3), "shared_kwh": round(each, 3), "kwh": round(dad_d + each, 3), "habit": "电脑负荷几乎都发生在他独自在家的白天。"},
        {"name": "妈妈", "role": "晚餐与家务", "direct_kwh": round(mom_d, 3), "shared_kwh": round(each, 3), "kwh": round(mom_d + each, 3), "habit": "照明在做饭和回家时段更集中。"},
        {"name": "大宝", "role": "晚间客厅", "direct_kwh": round(kid1_d, 3), "shared_kwh": round(each, 3), "kwh": round(kid1_d + each, 3), "habit": "电视主要发生在 19:00 之后。"},
        {"name": "二宝", "role": "晚间陪伴", "direct_kwh": round(kid2_d, 3), "shared_kwh": round(each, 3), "kwh": round(kid2_d + each, 3), "habit": "与客厅活动、夜间照明相关。"},
    ]
    for row in rows:
        row["share"] = round(row["kwh"] / total * 100, 1) if total else 0.0
    return rows


def device_health(devices: list[dict]) -> list[dict]:
    hints = {
        "air_conditioner": "夏季运行偏长，建议清洗滤网，能把同样制冷做得更省。",
        "water_heater": "存在凌晨异常加热，优先检查定时，不要全天待机。",
        "refrigerator": "全天运行正常，注意门封和摆放间距。",
        "lighting": "低占用时段仍有照明，适合交给管家自动关灯。",
        "computer": "工作日白天是刚需，高峰可改待机。",
        "television": "晚间娱乐负荷，影响小。",
        "washing_machine": "适合挪到谷电再洗。",
        "other": "插座待机可再压一截。",
    }
    rows = []
    for item in devices:
        runtime = item.get("runtime_hours") or 0
        level = "ok"
        if item["device_type"] == "water_heater":
            level = "alert"
        elif runtime >= 10 or item["device_type"] in {"air_conditioner", "lighting"}:
            level = "watch"
        rows.append(
            {
                "id": item["id"],
                "name": item["name"],
                "device_type": item["device_type"],
                "runtime_hours": runtime,
                "today_energy": item["today_energy"],
                "status": item["status"],
                "level": level,
                "hint": hints.get(item["device_type"], "运行正常。"),
            }
        )
    return rows


def seed_rules(db: Session, user_id: int) -> dict[str, bool]:
    existing = {
        row.rule_key: row.armed
        for row in db.scalars(select(HomeRule).where(HomeRule.user_id == user_id)).all()
    }
    changed = False
    for spec in DEFAULT_RULES:
        if spec["key"] not in existing:
            db.add(HomeRule(user_id=user_id, rule_key=spec["key"], armed=spec["default"]))
            existing[spec["key"]] = spec["default"]
            changed = True
    if changed:
        db.commit()
    return existing


def toggle_rule(db: Session, user_id: int, key: str, armed: bool) -> dict:
    keys = {spec["key"] for spec in DEFAULT_RULES}
    if key not in keys:
        raise HTTPException(status_code=404, detail="未知规则")
    row = db.scalar(select(HomeRule).where(HomeRule.user_id == user_id, HomeRule.rule_key == key))
    if row is None:
        row = HomeRule(user_id=user_id, rule_key=key, armed=armed)
        db.add(row)
    else:
        row.armed = armed
    db.commit()
    return get_life_os(db, user_id)


def evaluate_rules(armed: dict[str, bool], occupancy: int, hour: int, devices: list[dict], heater_alert: bool) -> list[dict]:
    lighting_on = any(d["device_type"] == "lighting" and d["current_power"] > 15 for d in devices)
    washer_on = any(d["device_type"] == "washing_machine" and d["current_power"] > 15 for d in devices)
    ac = next((d for d in devices if d["device_type"] == "air_conditioner"), None)
    period = tou_period(hour)
    firing_map = {
        "peak_guard": period == "peak",
        "night_heater": hour < 6 or heater_alert,
        "away_light": occupancy <= 1 and lighting_on,
        "valley_wash": period == "peak" and washer_on,
        "ac_setpoint": period == "peak" and bool(ac) and (ac.get("setpoint") or 24) < 26,
    }
    rows = []
    for spec in DEFAULT_RULES:
        key = spec["key"]
        rows.append(
            {
                **spec,
                "armed": bool(armed.get(key, spec["default"])),
                "firing": bool(firing_map.get(key)) and bool(armed.get(key, spec["default"])),
            }
        )
    return rows


def build_notices(clock: dict, stats: dict, anomalies: list, rules: list[dict], logs: list) -> list[dict]:
    notices = [
        {
            "level": "warn" if clock["period"] == "peak" else "info",
            "title": f"当前{clock['period_label']}电价 {clock['price']} 元/kWh",
            "detail": clock["advice"],
            "action": "去执行节能",
        }
    ]
    if anomalies:
        notices.append({"level": "alert", "title": "异常待处理", "detail": anomalies[0]["description"], "action": "查看异常"})
    firing = [r for r in rules if r["firing"]]
    if firing:
        notices.append({"level": "warn", "title": f"{len(firing)} 条规则正在触发", "detail": "、".join(r["title"] for r in firing), "action": "查看规则"})
    notices.append(
        {
            "level": "info",
            "title": f"第一负荷 {stats['main_device']}",
            "detail": f"占比 {stats['main_device_share']:.1f}%，是今晚最值得动的开关。",
            "action": "叫管家",
        }
    )
    if logs:
        notices.append({"level": "ok", "title": "管家刚去办过", "detail": logs[0].speech, "action": "打开管家"})
    return notices[:5]


def build_badges(db: Session, user_id: int, anomalies: list) -> list[dict]:
    logs = db.scalars(select(ButlerLog).where(ButlerLog.user_id == user_id)).all()
    intents = {log.intent for log in logs}
    acts = {a.last_command for a in db.scalars(select(DeviceActuator).where(DeviceActuator.user_id == user_id)).all()}
    catalog = [
        {"id": "found_anomaly", "title": "火眼金睛", "how": "捕获凌晨热水器异常", "earned": bool(anomalies)},
        {"id": "set_26", "title": "二十六度公约", "how": "把空调拧到 26℃", "earned": "setpoint" in intents or any("26" in (c or "") for c in acts)},
        {"id": "eco_run", "title": "一键执行", "how": "让管家按策略去拧开关", "earned": "scene_eco" in intents},
        {"id": "night_guard", "title": "守夜人", "how": "关掉夜间加热或启用凌晨保护", "earned": "scene_sleep" in intents or "night_heater" in intents},
        {"id": "ask_why", "title": "打破砂锅", "how": "问过为什么耗电", "earned": "chat" in intents},
        {"id": "grid_hero", "title": "电网响应", "how": "应下削峰邀约或执行节能方案", "earned": "demand_accept" in intents or "scene_eco" in intents},
    ]
    return catalog


def seven_day_ledger(db: Session, user_id: int) -> list[dict]:
    heat = month_heatmap(db, user_id)[-7:]
    rows = []
    for item in heat:
        kwh = float(item["energy"])
        rows.append(
            {
                "date": item["date"],
                "kwh": kwh,
                "cost": round(kwh * 0.55, 2),
                "carbon": carbon_of(kwh),
            }
        )
    return rows


def get_life_os(db: Session, user_id: int) -> dict:
    stats = today_stats(db, user_id)
    frame = load_today_frame(db, user_id)
    tou = tou_breakdown(frame)
    devices = device_energy_breakdown(db, user_id)
    clock = build_clock()
    occupancy = 4
    indoor = None
    outdoor = None
    weather = None
    if not frame.empty:
        target = _as_of()
        idx = (frame["timestamp"] - pd.Timestamp(target)).abs().idxmin()
        row = frame.loc[idx]
        occupancy = int(row.get("occupancy") or 0)
        indoor = round(float(row["temperature"]), 1) if pd.notna(row.get("temperature")) else None
        outdoor = round(float(row["outdoor_temp"]), 1) if "outdoor_temp" in row and pd.notna(row.get("outdoor_temp")) else None
        weather = str(row["weather"]) if "weather" in row and pd.notna(row.get("weather")) else None
    anomalies = latest_anomalies(db, user_id, limit=3)
    heater_alert = any("热水器" in (a.get("description") or "") for a in anomalies)
    armed = seed_rules(db, user_id)
    rules = evaluate_rules(armed, occupancy, _as_of().hour, devices, heater_alert)
    logs = db.scalars(select(ButlerLog).where(ButlerLog.user_id == user_id).order_by(ButlerLog.id.desc()).limit(3)).all()
    month_cost = round(float(stats["month_energy"]) * (tou["avg_price"] or 0.55), 2)
    expected = round(float(stats["week_avg_energy"]) * 30 * (tou["avg_price"] or 0.55), 2)
    ac_kwh = float((stats.get("device_energy") or {}).get("air_conditioner") or 0)
    delta = None
    advice = "室内外温差数据不足。"
    if indoor is not None and outdoor is not None:
        delta = round(outdoor - indoor, 1)
        advice = f"室外 {outdoor}℃、室内 {indoor}℃。温差 {delta}℃，空调不要压到 24℃，26℃ 通常够用。"
    whatif = {
        "ac_kwh": round(ac_kwh, 3),
        "per_degree_kwh": round(ac_kwh * 0.10, 3),
        "note": "与策略引擎一致：空调每上调 1℃，按今日空调电量的 10% 估算。",
    }
    flags = get_flags(db, user_id)
    loads = analyze_loads(db, user_id)
    shift = build_shift(loads)
    standby = build_standby(loads)
    missions = build_missions(devices, flags, shift, standby, whatif)
    demand = build_demand(stats, flags, missions)
    schedule = build_schedule(flags, shift)
    tomorrow = build_tomorrow(db, user_id)
    badges = build_badges(db, user_id, anomalies)
    family = family_split(stats)
    score = None
    try:
        from app.services.profile_service import get_energy_score

        score = get_energy_score(db, user_id).get("energy_score")
    except Exception:
        score = None
    notices = build_notices(clock, stats, anomalies, rules, logs)
    if demand["status"] == "pending":
        notices.insert(
            0,
            {
                "level": "warn",
                "title": "电网邀约待应",
                "detail": f"{demand['window']} 目标削峰 {demand['target_percent']}%，示意奖励 {demand['reward_yuan']} 元。",
                "action": "应邀约",
            },
        )
    return {
        "clock": clock,
        "budget": {
            "month_kwh": stats["month_energy"],
            "month_cost": month_cost,
            "expected_cost": expected,
            "pace_percent": round(month_cost / expected * 100, 1) if expected else 0,
            "label": "快于近7日节奏" if expected and month_cost > expected else "不高于近7日外推",
            "avg_price": tou["avg_price"],
        },
        "nilm": nilm_hourly(db, user_id),
        "family": family,
        "health": device_health(devices),
        "weather": {"indoor": indoor, "outdoor": outdoor, "weather": weather, "delta": delta, "advice": advice},
        "rules": rules,
        "notices": notices[:6],
        "badges": badges,
        "ledger": seven_day_ledger(db, user_id),
        "whatif": whatif,
        "occupancy": occupancy,
        "missions": missions,
        "demand": demand,
        "shift": shift,
        "standby": standby,
        "schedule": schedule,
        "tomorrow": tomorrow,
        "defense": build_defense(stats, clock, anomalies, family, shift, standby, tomorrow, score),
        "challenge": build_challenge(missions, badges),
        "comfort": build_comfort(flags),
        "tou": {"peak_kwh": tou["peak_kwh"], "peak_share": tou["peak_share"], "total_cost": tou["total_cost"]},
    }
