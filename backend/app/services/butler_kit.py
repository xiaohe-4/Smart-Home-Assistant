from sqlalchemy.orm import Session

from app.models.actuator import ButlerMemory

SKILL_CATALOG = [
    {
        "group": "场景模式",
        "items": [
            {"title": "晚安", "cmd": "晚安", "desc": "关灯、电视、电脑，掐夜间加热，空调 26℃"},
            {"title": "起床", "cmd": "我起床了", "desc": "开灯，热水器早晨预热，空调按偏好"},
            {"title": "离家", "cmd": "我出门了", "desc": "非刚需全关，冰箱继续转"},
            {"title": "回家", "cmd": "我回来了", "desc": "开灯，空调迎接"},
            {"title": "午休", "cmd": "午休", "desc": "关电视关灯，空调 26℃"},
            {"title": "看电影", "cmd": "看电影", "desc": "开电视、关灯、空调 26℃"},
            {"title": "做饭", "cmd": "做饭", "desc": "开灯，厨房先照顾上"},
            {"title": "学习加班", "cmd": "我要学习", "desc": "开书房电脑和灯，关电视"},
            {"title": "待客", "cmd": "有客人", "desc": "空调 24℃，灯打开"},
            {"title": "只留冰箱", "cmd": "只留冰箱", "desc": "除冰箱外全部关掉"},
            {"title": "执行节能", "cmd": "执行今晚节能方案", "desc": "高峰方案：26℃、掐加热、关灯、电脑待机"},
            {"title": "恢复原样", "cmd": "恢复原样", "desc": "取消本次控制"},
        ],
    },
    {
        "group": "家电控制",
        "items": [
            {"title": "空调 26℃", "cmd": "把空调调到26度", "desc": "高峰最稳的设定"},
            {"title": "再热一点", "cmd": "调高一度", "desc": "设定温度 +1℃，更省电"},
            {"title": "再凉快", "cmd": "调低一度", "desc": "设定温度 -1℃"},
            {"title": "关热水器", "cmd": "关掉热水器", "desc": "处理凌晨异常加热"},
            {"title": "关灯", "cmd": "关掉灯", "desc": "非必要照明关掉"},
            {"title": "按我习惯", "cmd": "按我习惯调空调", "desc": "用记下的偏好温度"},
        ],
    },
    {
        "group": "问询汇报",
        "items": [
            {"title": "汇报家里", "cmd": "汇报一下", "desc": "功率、场景、电价、异常"},
            {"title": "今晚怎么办", "cmd": "今晚任务", "desc": "待办任务"},
            {"title": "谁在用电", "cmd": "谁在用电", "desc": "行为归因，不是每人一块表"},
            {"title": "高峰还多久", "cmd": "高峰还剩多久", "desc": "电价时钟"},
            {"title": "处理异常", "cmd": "处理热水器异常", "desc": "掐掉凌晨加热"},
            {"title": "你会干什么", "cmd": "你会干什么", "desc": "技能清单"},
        ],
    },
    {
        "group": "电网与记忆",
        "items": [
            {"title": "应下邀约", "cmd": "接受电网邀约", "desc": "按节能方案响应削峰"},
            {"title": "预约谷电洗衣", "cmd": "预约谷电洗衣", "desc": "约到 23:00"},
            {"title": "点头去办", "cmd": "点头", "desc": "执行我刚备下的那件事"},
            {"title": "免打扰", "cmd": "安静", "desc": "界面还在，暂时不朗读"},
        ],
    },
]

SCENE_PLANS = {
    "sleep": {
        "keys": ("晚安", "睡觉", "睡了", "夜安"),
        "scene": "晚安",
        "intent": "scene_sleep",
        "speech": "您歇着。灯、电视、电脑我关了，热水器夜间加热掐掉，空调拧到{ac}度。明早照常用。",
        "plan": [
            ("lighting", False, None, "关灯"),
            ("television", False, None, "关电视"),
            ("computer", False, None, "关电脑"),
            ("water_heater", False, None, "关热水器夜间加热"),
            ("air_conditioner", True, "pref", "空调偏好温度"),
        ],
    },
    "morning": {
        "keys": ("起床", "早安", "早上了", "起床了"),
        "scene": "起床",
        "intent": "scene_morning",
        "speech": "早。灯开了，热水器给您预热，空调{ac}度。别把早晨也开成高峰空调大战。",
        "plan": [
            ("lighting", True, None, "开灯"),
            ("water_heater", True, None, "早晨预热"),
            ("air_conditioner", True, "pref", "空调偏好温度"),
        ],
    },
    "away": {
        "keys": ("出门", "离家", "走了", "不在家"),
        "scene": "离家",
        "intent": "scene_away",
        "speech": "您出门我看着家。灯、电视、电脑、空调都关了，冰箱继续转，菜坏不了。",
        "plan": [
            ("lighting", False, None, "关灯"),
            ("television", False, None, "关电视"),
            ("computer", False, None, "关电脑"),
            ("air_conditioner", False, None, "关空调"),
            ("washing_machine", False, None, "停洗衣"),
        ],
    },
    "home": {
        "keys": ("回来了", "回家", "我到家"),
        "scene": "回家",
        "intent": "scene_home",
        "speech": "欢迎回家。灯开了，空调{ac}度，凉快够用，还不至于把高峰电费烧上去。",
        "plan": [
            ("air_conditioner", True, "pref", "空调迎接"),
            ("lighting", True, None, "开客厅灯"),
        ],
    },
    "nap": {
        "keys": ("午休", "眯一会", "眯一会儿"),
        "scene": "午休",
        "intent": "scene_nap",
        "speech": "您眯一会儿。电视和灯我关了，空调{ac}度，别睡成 24 度那档。",
        "plan": [
            ("television", False, None, "关电视"),
            ("lighting", False, None, "关灯"),
            ("air_conditioner", True, "pref", "空调偏好温度"),
        ],
    },
    "movie": {
        "keys": ("看电影", "观影", "放电影"),
        "scene": "观影",
        "intent": "scene_movie",
        "speech": "电视开了，灯关了，空调{ac}度。您看，电我盯着。",
        "plan": [
            ("television", True, None, "开电视"),
            ("lighting", False, None, "关灯看电影"),
            ("air_conditioner", True, "pref", "空调偏好温度"),
        ],
    },
    "cook": {
        "keys": ("做饭", "炒菜", "下厨", "煮饭"),
        "scene": "做饭",
        "intent": "scene_cook",
        "speech": "灯开了。厨房这阵子该亮着，冰箱别动，热水我先不乱关。",
        "plan": [
            ("lighting", True, None, "开灯做饭"),
        ],
    },
    "study": {
        "keys": ("学习", "加班", "写作业", "我要学习"),
        "scene": "学习",
        "intent": "scene_study",
        "speech": "书房电脑和灯开了，电视关了，空调{ac}度。您忙，高峰别把空调拧到 24。",
        "plan": [
            ("computer", True, None, "开电脑"),
            ("lighting", True, None, "开灯"),
            ("television", False, None, "关电视"),
            ("air_conditioner", True, "pref", "空调偏好温度"),
        ],
    },
    "guest": {
        "keys": ("有客人", "待客", "来人了", "客人来"),
        "scene": "待客",
        "intent": "scene_guest",
        "speech": "客人来了就先凉快。灯开了，空调 24 度。人走了再说回 26。",
        "plan": [
            ("lighting", True, None, "开灯待客"),
            ("air_conditioner", True, 24.0, "待客24℃"),
            ("television", True, None, "开电视"),
        ],
    },
}


def get_memory(db: Session, user_id: int) -> ButlerMemory:
    row = db.get(ButlerMemory, user_id)
    if row is None:
        row = ButlerMemory(user_id=user_id, pending_cmd="", pending_reason="", preferred_ac=26, quiet=False)
        db.add(row)
        db.flush()
    return row


def set_pending(db: Session, user_id: int, cmd: str, reason: str) -> None:
    mem = get_memory(db, user_id)
    mem.pending_cmd = (cmd or "")[:128]
    mem.pending_reason = (reason or "")[:255]


def clear_pending(db: Session, user_id: int) -> None:
    mem = get_memory(db, user_id)
    mem.pending_cmd = ""
    mem.pending_reason = ""


def resolve_setpoint(value, preferred: int) -> float | None:
    if value == "pref":
        return float(preferred)
    if value is None:
        return None
    return float(value)


def brief_home(snapshot: dict, clock: dict | None, anomaly: dict | None, mem: ButlerMemory) -> str:
    top = max(snapshot["devices"], key=lambda d: d["current_power"], default=None) if snapshot.get("devices") else None
    bits = [
        f"现在是{snapshot.get('scene') or '日常'}，全家大约 {snapshot.get('current_power') or 0:.0f} 瓦",
    ]
    if clock:
        bits.append(f"正赶上{clock['period_label']}，电价 {clock['price']} 元，再过 {clock['minutes_left']} 分钟就进{clock['next_label']}")
    if top:
        bits.append(f"这会儿最费电的是{top['name']}，大概 {top['current_power']} 瓦")
    if snapshot.get("saving_w"):
        bits.append(f"已经帮您压下 {snapshot['saving_w']} 瓦")
    if anomaly:
        bits.append("另外有个异常，" + (anomaly.get("description") or "")[:40])
    if mem.pending_cmd:
        bits.append("我备着" + (mem.pending_reason or mem.pending_cmd) + "，您点头我就去办")
    return "，".join(bits) + "。"


def suggestions(snapshot: dict, mem: ButlerMemory, clock: dict | None) -> list[dict]:
    items = []
    if mem.pending_cmd:
        items.append({"label": "点头去办", "cmd": "点头", "why": mem.pending_reason or mem.pending_cmd})
    if clock and clock.get("period") == "peak":
        items.append({"label": "执行节能", "cmd": "执行今晚节能方案", "why": "正赶上高峰"})
    items.append({"label": f"空调 {mem.preferred_ac}℃", "cmd": f"把空调调到{mem.preferred_ac}度", "why": "按您的习惯"})
    items.append({"label": "汇报家里", "cmd": "汇报一下", "why": "先听现状"})
    if snapshot.get("scene") != "晚安":
        items.append({"label": "晚安", "cmd": "晚安", "why": "夜深了可一键收工"})
    seen = set()
    uniq = []
    for item in items:
        if item["cmd"] in seen:
            continue
        seen.add(item["cmd"])
        uniq.append(item)
    return uniq[:5]
