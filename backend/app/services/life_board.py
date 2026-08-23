from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Device, EnergyRecord
from app.models.life import HomeFlag
from app.services.energy_service import DEVICE_CN, day_range, demo_day
from app.utils.pricing import carbon_of, tou_period

settings = get_settings()

SHIFT_RATIO = {
    "washing_machine": 1.0,
    "water_heater": 0.40,
    "computer": 0.50,
    "other": 0.40,
}

MISSION_SPECS = [
    {
        "key": "ac_26",
        "title": "空调拧到 26℃",
        "why": "高峰里每上调 1℃，按今日空调电量的 10% 估算。",
        "command": "把空调调到26度",
        "kind": "control",
    },
    {
        "key": "heater_off",
        "title": "掐掉夜间加热",
        "why": "凌晨已经出现过热水器异常启动，不要再挂着加热。",
        "command": "关掉热水器",
        "kind": "control",
    },
    {
        "key": "lights_off",
        "title": "关掉非必要照明",
        "why": "占用不高时灯还开着，就是纯浪费。",
        "command": "关掉灯",
        "kind": "control",
    },
    {
        "key": "computer_standby",
        "title": "电脑改待机",
        "why": "书房负荷可以错开高峰。",
        "command": "关掉电脑",
        "kind": "control",
    },
    {
        "key": "valley_wash",
        "title": "洗衣改约谷电",
        "why": "23:00 以后电价 0.28 元/kWh，现在洗最亏。",
        "command": "预约谷电洗衣",
        "kind": "schedule",
    },
]

COMFORT_MODES = {
    "eco": {"label": "省电", "ac": 26, "hint": "高峰优先节电，客厅仍够凉。"},
    "balanced": {"label": "均衡", "ac": 25, "hint": "少热一点，少花一点。"},
    "comfort": {"label": "清凉", "ac": 24, "hint": "舒适优先，高峰电费会上去。"},
}


def get_flags(db: Session, user_id: int) -> dict[str, str]:
    rows = db.scalars(select(HomeFlag).where(HomeFlag.user_id == user_id)).all()
    return {row.flag_key: row.value for row in rows}


def set_flag(db: Session, user_id: int, key: str, value: str, commit: bool = True) -> None:
    row = db.scalar(select(HomeFlag).where(HomeFlag.user_id == user_id, HomeFlag.flag_key == key))
    if row is None:
        db.add(HomeFlag(user_id=user_id, flag_key=key, value=value))
    else:
        row.value = value
    if commit:
        db.commit()
    else:
        db.flush()


def _hour_of(ts) -> int:
    return ts.hour if hasattr(ts, "hour") else int(str(ts)[11:13])


def analyze_loads(db: Session, user_id: int) -> dict:
    start, end = day_range(demo_day())
    rows = db.execute(
        select(EnergyRecord.timestamp, Device.name, Device.device_type, EnergyRecord.energy).join(
            Device, Device.id == EnergyRecord.device_id
        ).where(
            EnergyRecord.user_id == user_id,
            EnergyRecord.timestamp >= start,
            EnergyRecord.timestamp < end,
        )
    ).all()
    peak: dict[str, float] = {}
    valley: dict[str, float] = {}
    night: dict[str, float] = {}
    names: dict[str, str] = {}
    for ts, name, dtype, energy in rows:
        hour = _hour_of(ts)
        amount = float(energy or 0)
        names[dtype] = name
        period = tou_period(hour)
        if period == "peak":
            peak[dtype] = peak.get(dtype, 0.0) + amount
        elif period == "valley":
            valley[dtype] = valley.get(dtype, 0.0) + amount
        if hour < 6:
            night[dtype] = night.get(dtype, 0.0) + amount
    return {"peak": peak, "valley": valley, "night": night, "names": names}


def build_shift(loads: dict) -> dict:
    peak = loads["peak"]
    names = loads["names"]
    items = []
    movable = 0.0
    for dtype, ratio in SHIFT_RATIO.items():
        peak_kwh = float(peak.get(dtype) or 0)
        move = peak_kwh * ratio
        if peak_kwh < 0.02:
            continue
        movable += move
        items.append(
            {
                "device_type": dtype,
                "name": names.get(dtype, DEVICE_CN.get(dtype, dtype)),
                "peak_kwh": round(peak_kwh, 3),
                "ratio": ratio,
                "movable_kwh": round(move, 3),
                "saving_yuan": round(move * (settings.price_peak - settings.price_valley), 2),
            }
        )
    delta = settings.price_peak - settings.price_valley
    return {
        "peak_kwh": round(sum(peak.values()), 3),
        "movable_kwh": round(movable, 3),
        "saving_yuan": round(movable * delta, 2),
        "saving_carbon": carbon_of(movable),
        "price_gap": round(delta, 2),
        "note": "按今日高峰实测电量 × 可迁移比例估算，不是另造的一条负荷。",
        "items": items,
    }


def build_standby(loads: dict) -> dict:
    night = loads["night"]
    names = loads["names"]
    items = []
    wasted = 0.0
    for dtype, kwh in sorted(night.items(), key=lambda x: -x[1]):
        if dtype == "refrigerator" or kwh < 0.04:
            continue
        level = "alert" if dtype == "water_heater" or kwh >= 0.4 else "watch"
        wasted += kwh
        hint = {
            "water_heater": "对应 03:17 异常加热，优先关夜间定时。",
            "lighting": "凌晨不该还亮着。",
            "computer": "书房可以彻底待机。",
            "television": "客厅电视别挂待机。",
            "other": "插座待机还能再压一截。",
        }.get(dtype, "低占用时段仍在耗电。")
        items.append(
            {
                "device_type": dtype,
                "name": names.get(dtype, DEVICE_CN.get(dtype, dtype)),
                "kwh": round(kwh, 3),
                "cost": round(kwh * settings.price_valley, 2),
                "level": level,
                "hint": hint,
            }
        )
    return {
        "window": "00:00–06:00",
        "wasted_kwh": round(wasted, 3),
        "wasted_yuan": round(wasted * settings.price_valley, 2),
        "note": "冰箱全天运行不算浪费；这里只列凌晨非刚需负荷。",
        "items": items,
    }


def _device(devices: list[dict], dtype: str) -> dict | None:
    return next((d for d in devices if d["device_type"] == dtype), None)


def build_missions(devices: list[dict], flags: dict[str, str], shift: dict, standby: dict, whatif: dict) -> list[dict]:
    ac = _device(devices, "air_conditioner")
    heater = _device(devices, "water_heater")
    lights = _device(devices, "lighting")
    computer = _device(devices, "computer")
    inferred = {
        "ac_26": bool(ac and ac.get("setpoint") == 26),
        "heater_off": bool(heater and (heater.get("status") == "关闭" or heater.get("current_power", 1) == 0) and heater.get("controlled")),
        "lights_off": bool(lights and lights.get("status") == "关闭"),
        "computer_standby": bool(computer and computer.get("status") == "关闭"),
        "valley_wash": flags.get("schedule:valley_wash") == "booked",
    }
    heater_night = next((x["kwh"] for x in standby["items"] if x["device_type"] == "water_heater"), 0.35)
    wash_move = next((x["movable_kwh"] for x in shift["items"] if x["device_type"] == "washing_machine"), 0.0)
    hours_left = 3.5
    savings = {
        "ac_26": round(float(whatif.get("per_degree_kwh") or 0) * 2, 3),
        "heater_off": round(heater_night, 3),
        "lights_off": round((lights["current_power"] if lights else 0) / 1000 * hours_left, 3),
        "computer_standby": round((computer["current_power"] if computer else 0) / 1000 * hours_left, 3),
        "valley_wash": round(wash_move, 3),
    }
    rows = []
    for spec in MISSION_SPECS:
        key = spec["key"]
        done = flags.get(f"mission:{key}") == "done" or inferred.get(key, False)
        kwh = savings[key]
        rows.append(
            {
                **spec,
                "done": done,
                "saving_kwh": kwh,
                "saving_yuan": round(kwh * settings.price_peak, 2),
            }
        )
    return rows


def build_demand(stats: dict, flags: dict[str, str], missions: list[dict]) -> dict:
    current = float(stats.get("current_power") or 0)
    target_pct = 15
    cut = current * target_pct / 100
    done_n = sum(1 for m in missions if m["done"])
    status = flags.get("demand") or "pending"
    return {
        "id": "dr-20260819-2030",
        "title": "国网四川 · 演示削峰邀约",
        "window": "20:30–21:30",
        "target_percent": target_pct,
        "current_w": round(current, 1),
        "target_w": round(current - cut, 1),
        "cut_w": round(cut, 1),
        "reward_yuan": 2.0,
        "status": status,
        "progress": round(done_n / max(len(missions), 1) * 100, 0),
        "note": "演示邀约，奖励是示意金额，不接入真实电力市场。应下后管家会按节能方案去拧开关。",
    }


def build_schedule(flags: dict[str, str], shift: dict) -> list[dict]:
    wash = next((x for x in shift["items"] if x["device_type"] == "washing_machine"), None)
    heat = next((x for x in shift["items"] if x["device_type"] == "water_heater"), None)
    return [
        {
            "key": "valley_wash",
            "title": "洗衣机",
            "slot": "23:00",
            "period": "谷时",
            "saving_kwh": wash["movable_kwh"] if wash else 0,
            "saving_yuan": wash["saving_yuan"] if wash else 0,
            "booked": flags.get("schedule:valley_wash") == "booked",
            "hint": "现在高峰先别洗，谷电再启动。",
        },
        {
            "key": "heat_water",
            "title": "热水器预热",
            "slot": "23:00",
            "period": "谷时",
            "saving_kwh": heat["movable_kwh"] if heat else 0,
            "saving_yuan": heat["saving_yuan"] if heat else 0,
            "booked": flags.get("schedule:heat_water") == "booked",
            "hint": "夜间异常加热改成谷电预热，明早仍有热水。",
        },
    ]


def build_tomorrow(db: Session, user_id: int) -> dict:
    from app.services.prediction_service import get_prediction

    pred = get_prediction(db, user_id, 24)
    points = []
    for row in pred.get("forecast") or []:
        ts = row["timestamp"]
        if hasattr(ts, "strftime"):
            hour = ts.hour
            label = ts.strftime("%H:%M")
        else:
            text = str(ts)
            hour = int(text[11:13]) if len(text) >= 13 else 0
            label = text[11:16] if len(text) >= 16 else text
        points.append({"hour": hour, "label": label, "w": round(float(row["predicted_power"]), 1)})
    metrics = pred.get("metrics") or {}
    if not points:
        return {
            "ready": False,
            "model": pred.get("model_name"),
            "r2": metrics.get("R2"),
            "peak": None,
            "advice": "预测曲线还没写进库，先按今晚高峰守门。",
            "points": [],
        }
    peak = max(points, key=lambda x: x["w"])
    remaining_peak = [p for p in points if 18 <= p["hour"] < 22]
    tonight = [p for p in points if p["hour"] >= 21 or p["hour"] <= 7]
    focus = max(remaining_peak, key=lambda x: x["w"]) if remaining_peak else (max(tonight, key=lambda x: x["w"]) if tonight else peak)
    r2 = metrics.get("R2")
    r2_text = f"R² {r2}" if r2 is not None else "未写入精度"
    window = "剩余高峰" if remaining_peak else "接下来"
    return {
        "ready": True,
        "model": pred.get("model_name"),
        "r2": r2,
        "peak": peak,
        "tonight_peak": focus,
        "advice": f"{pred.get('model_name')} 看{window}最高约 {focus['w']:.0f} W（{focus['label']}）。{r2_text}。高峰结束前把空调留在 26℃。",
        "points": points[:16],
    }


def build_defense(stats: dict, clock: dict, anomalies: list, family: list, shift: dict, standby: dict, tomorrow: dict, score: float | None) -> dict:
    heater = next((a for a in anomalies if "热水" in (a.get("description") or "")), None)
    top = max(family, key=lambda x: x["kwh"]) if family else None
    r2 = tomorrow.get("r2")
    return {
        "headline": "空调占四成所以耗电；03:17 热水器和晚高峰才是浪费。",
        "facts": [
            {"label": "今日用电", "value": f"{float(stats['today_energy']):.2f} kWh"},
            {"label": "第一负荷", "value": f"{stats['main_device']} {float(stats['main_device_share']):.1f}%"},
            {"label": "能源评分", "value": "--" if score is None else str(score)},
            {"label": "当前电价", "value": f"{clock['period_label']} {clock['price']} 元"},
            {"label": "可迁移电费", "value": f"{shift['saving_yuan']} 元"},
            {"label": "凌晨浪费", "value": f"{standby['wasted_kwh']} kWh"},
            {"label": "预测 R²", "value": "--" if r2 is None else str(r2)},
            {"label": "异常", "value": "03:17 热水器" if heater else "无高优异常"},
        ],
        "family_top": None if not top else f"{top['name']} 行为归因约 {top['kwh']} kWh（不是每人一块表）",
        "closing": "管家可把空调拧到 26℃ 并掐夜间加热；洗衣机改约 23:00 谷电。",
    }


def build_challenge(missions: list[dict], badges: list[dict]) -> dict:
    done = sum(1 for m in missions if m["done"])
    lit = sum(1 for b in badges if b.get("earned"))
    target = 3
    points = done * 20 + lit * 10
    return {
        "title": "今晚家庭挑战",
        "goal": f"做完 {target} 项任务",
        "done": done,
        "target": target,
        "points": points,
        "badges": lit,
        "label": "节能先锋" if done >= target else "起步中",
    }


def build_comfort(flags: dict[str, str]) -> dict:
    mode = flags.get("comfort") or "balanced"
    spec = COMFORT_MODES.get(mode, COMFORT_MODES["balanced"])
    return {"mode": mode, **spec, "command": f"把空调调到{spec['ac']}度"}


def complete_mission(db: Session, user_id: int, key: str, done: bool = True, execute: bool = False) -> dict:
    keys = {spec["key"] for spec in MISSION_SPECS}
    if key not in keys:
        raise HTTPException(status_code=404, detail="未知任务")
    spec = next(s for s in MISSION_SPECS if s["key"] == key)
    if execute and done:
        if spec["kind"] == "schedule":
            set_flag(db, user_id, f"schedule:{key}", "booked", commit=False)
        from app.services.butler_service import handle_command

        handle_command(db, user_id, spec["command"])
    set_flag(db, user_id, f"mission:{key}", "done" if done else "open", commit=True)
    from app.services.life_service import get_life_os

    return get_life_os(db, user_id)


def set_demand(db: Session, user_id: int, action: str) -> dict:
    action = (action or "").strip().lower()
    if action == "accept":
        from app.services.butler_service import handle_command

        handle_command(db, user_id, "执行今晚节能方案")
        set_flag(db, user_id, "demand", "accepted", commit=False)
        for key in ("ac_26", "heater_off", "lights_off", "computer_standby"):
            set_flag(db, user_id, f"mission:{key}", "done", commit=False)
        db.commit()
    elif action == "reset":
        set_flag(db, user_id, "demand", "pending", commit=True)
    else:
        set_flag(db, user_id, "demand", "declined", commit=True)
    from app.services.life_service import get_life_os

    return get_life_os(db, user_id)


def book_schedule(db: Session, user_id: int, task: str, booked: bool = True) -> dict:
    allowed = {"valley_wash", "heat_water"}
    if task not in allowed:
        raise HTTPException(status_code=404, detail="未知预约")
    set_flag(db, user_id, f"schedule:{task}", "booked" if booked else "open", commit=False)
    if task == "valley_wash":
        set_flag(db, user_id, "mission:valley_wash", "done" if booked else "open", commit=False)
    db.commit()
    from app.services.life_service import get_life_os

    return get_life_os(db, user_id)


def set_comfort(db: Session, user_id: int, mode: str, execute: bool = False) -> dict:
    if mode not in COMFORT_MODES:
        raise HTTPException(status_code=404, detail="未知模式")
    set_flag(db, user_id, "comfort", mode, commit=True)
    if execute:
        ac = COMFORT_MODES[mode]["ac"]
        from app.services.butler_service import handle_command

        handle_command(db, user_id, f"把空调调到{ac}度")
    from app.services.life_service import get_life_os

    return get_life_os(db, user_id)
