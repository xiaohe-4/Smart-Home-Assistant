import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.actuator import ButlerLog, DeviceActuator, HomeScene
from app.models.device import Device
from app.services.butler_kit import (
    SCENE_PLANS,
    SKILL_CATALOG,
    brief_home,
    clear_pending,
    get_memory,
    resolve_setpoint,
    set_pending,
    suggestions,
)
from app.services.device_service import device_energy_breakdown, list_devices
from app.utils.pricing import carbon_of
from app.utils.speech import for_voice

DEVICE_ALIASES = [
    ("air_conditioner", ["空调", "冷气", "制冷"]),
    ("water_heater", ["热水器", "热水"]),
    ("lighting", ["灯", "照明", "电灯"]),
    ("television", ["电视"]),
    ("computer", ["电脑", "计算机"]),
    ("washing_machine", ["洗衣机", "洗衣"]),
    ("refrigerator", ["冰箱"]),
]

CN_TEMP = {"二十四": 24, "二十五": 25, "二十六": 26, "二十七": 27, "二十八": 28}
PROTECTED = {"refrigerator"}
HOURS_LEFT = 3.5
PURE_CONFIRM = {"点头", "好的", "行", "行吧", "去吧", "就这么办", "照做", "同意", "同意了", "去拧", "嗯"}


def home_snapshot(db: Session, user_id: int) -> dict:
    devices = device_energy_breakdown(db, user_id)
    baseline = sum(d.get("baseline_power") or d["current_power"] for d in devices)
    current = sum(d["current_power"] for d in devices)
    saving_w = max(0.0, baseline - current)
    scene = db.get(HomeScene, user_id)
    logs = db.scalars(
        select(ButlerLog).where(ButlerLog.user_id == user_id).order_by(ButlerLog.id.desc()).limit(12)
    ).all()
    mem = get_memory(db, user_id)
    from app.services.anomaly_service import latest_anomalies
    from app.services.life_service import build_clock

    clock = build_clock()
    anomalies = latest_anomalies(db, user_id, limit=1)
    snapshot = {
        "scene": scene.scene if scene else "日常",
        "baseline_power": round(baseline, 1),
        "current_power": round(current, 1),
        "saving_w": round(saving_w, 1),
        "saving_kwh_est": round(saving_w / 1000 * HOURS_LEFT, 3),
        "saving_carbon": carbon_of(saving_w / 1000 * HOURS_LEFT),
        "devices": devices,
        "logs": [
            {"command": log.command, "intent": log.intent, "speech": log.speech, "created_at": log.created_at}
            for log in logs
        ],
        "pending_cmd": mem.pending_cmd or "",
        "pending_reason": mem.pending_reason or "",
        "preferred_ac": mem.preferred_ac,
        "quiet": mem.quiet,
        "skills": SKILL_CATALOG,
        "clock": clock,
    }
    snapshot["brief"] = brief_home(snapshot, clock, anomalies[0] if anomalies else None, mem)
    snapshot["suggestions"] = suggestions(snapshot, mem, clock)
    return snapshot


def _set_scene(db: Session, user_id: int, scene: str) -> None:
    row = db.get(HomeScene, user_id)
    if row is None:
        db.add(HomeScene(user_id=user_id, scene=scene))
    else:
        row.scene = scene


def _upsert(db: Session, user_id: int, device: Device, enabled: bool, setpoint: float | None, command: str) -> DeviceActuator:
    row = db.get(DeviceActuator, device.id)
    if row is None:
        row = DeviceActuator(
            device_id=device.id,
            user_id=user_id,
            enabled=enabled,
            setpoint=setpoint,
            last_command=command,
        )
        db.add(row)
    else:
        row.enabled = enabled
        row.setpoint = setpoint
        row.last_command = command
    return row


def _find_type(text: str, devices: list[Device]) -> str | None:
    for device in devices:
        if device.name and device.name in text:
            return device.device_type
    for dtype, keys in DEVICE_ALIASES:
        if any(key in text for key in keys):
            return dtype
    return None


def _parse_temp(text: str) -> int | None:
    for word, value in CN_TEMP.items():
        if word in text:
            return value
    match = re.search(r"(?:调到|设到|设置|拧到|调成|喜欢|以后)?\s*(\d{2})\s*度?", text)
    if match:
        value = int(match.group(1))
        if 22 <= value <= 30:
            return value
    return None


def _device_of(devices: list[Device], dtype: str) -> Device | None:
    return next((d for d in devices if d.device_type == dtype), None)


def _power_of(snapshot: dict, device_id: int) -> float:
    hit = next((d for d in snapshot["devices"] if d["id"] == device_id), None)
    return float(hit["current_power"]) if hit else 0.0


def _ac_setpoint(snapshot: dict, preferred: int) -> int:
    ac = next((d for d in snapshot["devices"] if d["device_type"] == "air_conditioner"), None)
    if ac and ac.get("setpoint"):
        return int(ac["setpoint"])
    return preferred


def handle_command(db: Session, user_id: int, raw: str) -> dict:
    text = re.sub(r"\s+", "", (raw or "").strip())
    text = text.replace("宝强", "").replace("管家", "")
    devices = list_devices(db, user_id)
    before = home_snapshot(db, user_id)
    mem = get_memory(db, user_id)

    if text in PURE_CONFIRM:
        if mem.pending_cmd:
            text = re.sub(r"\s+", "", mem.pending_cmd)
            clear_pending(db, user_id)
        else:
            log = ButlerLog(user_id=user_id, command=(raw or text)[:255], intent="confirm", speech="您还没让我备着活。说晚安、出门，或者执行节能就行。")
            db.add(log)
            db.commit()
            after = home_snapshot(db, user_id)
            return {**after, "speech": log.speech, "intent": "confirm", "actions": []}

    intent = "chat"
    speech = ""
    actions: list[dict] = []

    def act(device: Device, enabled: bool, setpoint: float | None, label: str) -> None:
        before_power = _power_of(before, device.id)
        _upsert(db, user_id, device, enabled, setpoint, label)
        db.flush()
        after_snap = device_energy_breakdown(db, user_id)
        after = next((d for d in after_snap if d["id"] == device.id), None)
        actions.append(
            {
                "device_id": device.id,
                "name": device.name,
                "device_type": device.device_type,
                "action": label,
                "before_power": before_power,
                "after_power": after["current_power"] if after else 0.0,
            }
        )

    def run_plan(plan: list, preferred: int) -> None:
        for key, enabled, setpoint, label in plan:
            device = _device_of(devices, key)
            if device:
                act(device, enabled, resolve_setpoint(setpoint, preferred), label.replace("偏好温度", f"{preferred}℃"))

    temp = _parse_temp(text)
    dtype = _find_type(text, devices)
    off = any(k in text for k in ("关", "掐", "停", "别开"))
    on = any(k in text for k in ("开", "启动", "恢复运行")) and not off
    preferred = mem.preferred_ac or 26

    scene_spec = next((spec for spec in SCENE_PLANS.values() if any(k in text for k in spec["keys"])), None)

    if any(k in text for k in ("恢复原样", "全部打开", "都打开", "还原", "取消控制")):
        intent = "reset"
        for device in devices:
            _upsert(db, user_id, device, True, None, "恢复")
        _set_scene(db, user_id, "日常")
        clear_pending(db, user_id)
        speech = "得嘞，家电都给您恢复原样了。您接着用，我在旁边盯着电。"
    elif scene_spec:
        intent = scene_spec["intent"]
        _set_scene(db, user_id, scene_spec["scene"])
        run_plan(scene_spec["plan"], preferred)
        speech = scene_spec["speech"].format(ac=preferred)
    elif any(k in text for k in ("只留冰箱", "除了冰箱")):
        intent = "scene_fridge_only"
        _set_scene(db, user_id, "只留冰箱")
        for device in devices:
            if device.device_type in PROTECTED:
                continue
            act(device, False, None, f"关闭{device.name}")
        speech = "除了冰箱，别的我都掐了。菜坏不了，电也能歇一歇。"
    elif any(k in text for k in ("接受邀约", "答应电网", "响应电网", "削峰邀约", "电网邀约", "接受电网")) or any(
        k in text for k in ("执行节能", "一键节能", "按建议", "听你的", "你去办", "今晚节能", "优化方案")
    ):
        is_dr = any(k in text for k in ("接受邀约", "答应电网", "响应电网", "削峰邀约", "电网邀约", "接受电网"))
        intent = "demand_accept" if is_dr else "scene_eco"
        _set_scene(db, user_id, "节能执行")
        run_plan(
            [
                ("air_conditioner", True, 26.0, "空调24→26℃"),
                ("water_heater", False, None, "热水器改定时，夜间关闭"),
                ("lighting", False, None, "关掉非必要照明"),
                ("computer", False, None, "高峰错峰，电脑待机"),
                ("television", True, None, "电视保持"),
            ],
            preferred,
        )
        if is_dr:
            from app.services.life_board import set_flag

            set_flag(db, user_id, "demand", "accepted", commit=False)
            for key in ("ac_26", "heater_off", "lights_off", "computer_standby"):
                set_flag(db, user_id, f"mission:{key}", "done", commit=False)
            speech = "电网这头我应下了。空调26度，热水器夜间掐了，灯关了，电脑也停了。削峰这事我盯着。"
        else:
            speech = "这点事我去干。空调26度，热水器夜间掐了，灯关了，电脑也停了。您看效果就行。"
    elif any(k in text for k in ("预约洗衣", "谷电洗衣", "预约谷电")):
        from app.services.life_board import set_flag

        intent = "schedule"
        set_flag(db, user_id, "schedule:valley_wash", "booked", commit=False)
        set_flag(db, user_id, "mission:valley_wash", "done", commit=False)
        washer = _device_of(devices, "washing_machine")
        if washer:
            act(washer, False, None, "高峰停洗，改约23:00")
        speech = "得嘞，洗衣机给您约到 23:00 谷电。现在高峰别开，到点再洗最划算。"
    elif any(k in text for k in ("拒绝邀约", "不应邀")):
        from app.services.life_board import set_flag

        intent = "demand_decline"
        set_flag(db, user_id, "demand", "declined", commit=False)
        speech = "行，这波电网邀约我先给您回了。家里开关不动，高峰您自己看着办。"
    elif any(k in text for k in ("处理异常", "热水器异常", "掐掉异常")):
        intent = "fix_anomaly"
        heater = _device_of(devices, "water_heater")
        if heater:
            act(heater, False, None, "关闭异常加热")
        _set_scene(db, user_id, "异常处置")
        speech = "凌晨那趟热水器我给掐了。定时别挂在半夜，谷电再热。"
    elif any(k in text for k in ("调高一度", "再热", "一度不够热", "太冷了")):
        intent = "ac_up"
        nxt = min(30, _ac_setpoint(before, preferred) + 1)
        device = _device_of(devices, "air_conditioner")
        if device:
            act(device, True, float(nxt), f"空调{nxt}℃")
            speech = f"得嘞，给您调到 {nxt} 度，少冻着，也少花高峰的钱。"
        else:
            speech = "家里没找到空调。"
    elif any(k in text for k in ("调低一度", "再冷", "再凉快", "太热了")):
        intent = "ac_down"
        nxt = max(22, _ac_setpoint(before, preferred) - 1)
        device = _device_of(devices, "air_conditioner")
        if device:
            act(device, True, float(nxt), f"空调{nxt}℃")
            speech = f"拧到 {nxt} 度了。再往下就费电，您可想好。"
        else:
            speech = "家里没找到空调。"
    elif any(k in text for k in ("按我习惯", "按偏好", "老样子的空调")):
        intent = "ac_pref"
        device = _device_of(devices, "air_conditioner")
        if device:
            act(device, True, float(preferred), f"空调{preferred}℃")
            speech = f"按您记下的习惯，空调 {preferred} 度。"
        else:
            speech = "家里没找到空调。"
    elif any(k in text for k in ("喜欢", "以后", "默认")) and temp is not None:
        intent = "remember_ac"
        mem.preferred_ac = temp
        device = _device_of(devices, "air_conditioner")
        if device and any(k in text for k in ("调", "拧", "设")):
            act(device, True, float(temp), f"空调{temp}℃")
            speech = f"记下了，以后按 {temp} 度。这回也给您拧上了。"
        else:
            speech = f"记下了。以后说按我习惯，我就拧到 {temp} 度。"
    elif any(k in text for k in ("安静", "别说话", "免打扰", "闭嘴")):
        intent = "quiet_on"
        mem.quiet = True
        speech = "那我先不念了。字还在，您看就行。想听了说：可以说话。"
    elif any(k in text for k in ("继续说", "可以说话", "打开语音", "别安静")):
        intent = "quiet_off"
        mem.quiet = False
        speech = "行，我又出声了。"
    elif any(k in text for k in ("使用说明", "怎么用", "说明书", "操作指南")):
        intent = "guide"
        speech = "使用说明在左侧菜单和顶栏。先看总览和回放，再来找我。您可以说汇报一下，或执行今晚节能方案。冰箱我不会关。"
        set_pending(db, user_id, "汇报一下", "先听家里现在怎样")
    elif any(k in text for k in ("你会干", "你能做", "有什么功能", "帮助", "菜单", "技能")):
        intent = "help"
        titles = "、".join(item["title"] for group in SKILL_CATALOG for item in group["items"][:4])
        speech = f"我能听、能说、能去拧开关，也能汇报。场景有晚安、起床、出门、回家、午休、看电影、做饭、学习、待客。您还可以说点头，我把备着的事办了。比如：{titles}。"
        set_pending(db, user_id, "汇报一下", "先听我汇报家里")
    elif any(k in text for k in ("汇报", "家里怎么样", "现在什么情况", "看看家", "状况")):
        intent = "brief"
        speech = before["brief"] + "您点头我就按备着的事去拧。"
        if not mem.pending_cmd:
            set_pending(db, user_id, "执行今晚节能方案", "高峰就按节能方案办")
    elif any(k in text for k in ("今晚任务", "我该干", "干什么", "今晚怎么办")):
        from app.services.life_service import get_life_os

        life = get_life_os(db, user_id)
        open_m = [m["title"] for m in life["missions"] if not m["done"]]
        intent = "missions"
        if open_m:
            speech = "今晚先办这几件：" + "；".join(open_m[:3]) + "。您点头我就去拧。"
            set_pending(db, user_id, "执行今晚节能方案", "今晚任务打包执行")
        else:
            speech = "今晚这张任务单都勾完了。您歇着，电我盯着。"
    elif any(k in text for k in ("待机", "偷电", "吸血鬼", "凌晨谁")):
        from app.services.life_service import get_life_os

        life = get_life_os(db, user_id)
        items = life["standby"]["items"]
        intent = "standby"
        if items:
            top = items[0]
            speech = f"凌晨 {life['standby']['window']} 非刚需还在用电 {life['standby']['wasted_kwh']} 度，最显眼的是{top['name']}，{top['hint']}您点头我就去掐。"
            set_pending(db, user_id, "处理热水器异常", "先掐凌晨加热")
        else:
            speech = "凌晨除了冰箱，没看出明显的待机浪费。"
    elif any(k in text for k in ("明天", "明早", "接下来最高")):
        from app.services.life_service import get_life_os

        life = get_life_os(db, user_id)
        intent = "tomorrow"
        speech = life["tomorrow"]["advice"]
    elif any(k in text for k in ("数据从哪", "多模态", "从哪来", "怎么移植", "电表")):
        from app.services.source_service import get_source_map

        src = get_source_map(db, user_id)
        intent = "sources"
        speech = (
            f"电不是我瞎编的。电力、室内环境、在家人数、天气四路对齐进同一张时间表，演示日对齐 {src['alignment']['percent']}%。"
            f"您要换一户，电表按这个合同接进来，电价改配置，模型再训一遍就行。"
        )
    elif any(k in text for k in ("预算", "这个月", "花了多少", "电费上限")):
        from app.services.life_service import get_life_os

        life = get_life_os(db, user_id)
        b = life["budget"]
        intent = "budget"
        speech = (
            f"近 30 日大概 {b['month_cost']} 元，按近 7 日节奏外推是 {b['expected_cost']} 元，"
            f"现在算 {b['label']}。高峰再降一截空调，月底会好看点。"
        )
    elif any(k in text for k in ("谁在用", "分账", "爸爸", "孩子")):
        from app.services.life_service import get_life_os

        life = get_life_os(db, user_id)
        top = max(life["family"], key=lambda x: x["kwh"])
        intent = "family"
        speech = f"这是行为归因，不是每人一块表。今日最显眼的是{top['name']}，大约 {top['kwh']} 度，{top['habit']}"
    elif any(k in text for k in ("几点", "谷电", "电价", "高峰还")):
        from app.services.life_service import get_life_os

        life = get_life_os(db, user_id)
        c = life["clock"]
        intent = "clock"
        speech = f"现在 {c['as_of']} 是{c['period_label']}，{c['price']} 元。{c['minutes_left']} 分钟后到{c['next_label']}。{c['advice']}"
        set_pending(db, user_id, "执行今晚节能方案", "高峰未结束")
    elif any(k in text for k in ("热不热", "天气", "外面")):
        from app.services.life_service import get_life_os

        life = get_life_os(db, user_id)
        intent = "weather"
        speech = life["weather"]["advice"] + f"您点头我就拧到{preferred}度。"
        set_pending(db, user_id, f"把空调调到{preferred}度", f"建议空调{preferred}℃")
    elif temp is not None:
        intent = "setpoint"
        device = _device_of(devices, "air_conditioner")
        if device:
            act(device, True, float(temp), f"空调{temp}℃")
            _set_scene(db, user_id, "日常")
            speech = f"得嘞，空调我给您拧到{temp}度了。客厅还凉快，高峰电费能少花点。"
        else:
            speech = "家里没找到空调，我没法拧。"
    elif dtype == "refrigerator" and off:
        intent = "reject"
        speech = "冰箱可不能关，菜要坏。您换个别的，空调热水器灯我都能办。"
    elif dtype and off:
        intent = "off"
        device = _device_of(devices, dtype)
        if device:
            act(device, False, None, f"关闭{device.name}")
            speech = f"得嘞，{device.name}我给它掐了。您歇着，电我盯着。"
        else:
            speech = "这台设备我没找着。"
    elif dtype and on:
        intent = "on"
        device = _device_of(devices, dtype)
        setpoint = float(preferred) if dtype == "air_conditioner" else None
        if device:
            act(device, True, setpoint, f"开启{device.name}")
            speech = f"开好了，{device.name}已经起来了。"
        else:
            speech = "这台设备我没找着。"
    else:
        from app.services.insight_service import chat_with_assistant

        intent = "chat"
        reply = chat_with_assistant(db, user_id, raw or text)
        core = reply.get("answer") or "我先看了看电。"
        speech = f"我跟您实在说，{core}您要是点头，我这就去拧开关。"
        if not mem.pending_cmd:
            set_pending(db, user_id, "执行今晚节能方案", "听完解释可以一键执行")

    log = ButlerLog(user_id=user_id, command=(raw or text)[:255], intent=intent, speech=for_voice(speech)[:512])
    db.add(log)
    db.commit()
    after = home_snapshot(db, user_id)
    return {
        "speech": log.speech,
        "intent": intent,
        "scene": after["scene"],
        "actions": actions,
        "saving_w": after["saving_w"],
        "saving_kwh_est": after["saving_kwh_est"],
        "saving_carbon": after["saving_carbon"],
        "baseline_power": after["baseline_power"],
        "current_power": after["current_power"],
        "devices": after["devices"],
        "logs": after["logs"],
        "pending_cmd": after["pending_cmd"],
        "pending_reason": after["pending_reason"],
        "preferred_ac": after["preferred_ac"],
        "quiet": after["quiet"],
        "brief": after["brief"],
        "skills": after["skills"],
        "suggestions": after["suggestions"],
        "clock": after.get("clock"),
    }
