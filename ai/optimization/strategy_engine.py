from dataclasses import dataclass


DEVICE_CN = {
    "air_conditioner": "空调",
    "refrigerator": "冰箱",
    "water_heater": "热水器",
    "washing_machine": "洗衣机",
    "television": "电视",
    "lighting": "照明",
    "computer": "电脑",
    "other": "其他",
}


@dataclass
class StrategyCandidate:
    strategy_type: str
    title: str
    description: str
    estimated_saving_kwh: float
    estimated_saving_percent: float
    comfort_impact: str
    feasibility: float
    user_acceptance: float
    comfort_penalty: float
    problem: str
    cause: str
    suggestion: str
    user_impact: str

    @property
    def score(self) -> float:
        return round(
            self.estimated_saving_kwh * 10 * self.feasibility * self.user_acceptance
            - self.comfort_penalty,
            2,
        )


def build_strategies(
    today_energy: float,
    device_energy: dict[str, float],
    indoor_temp: float,
    anomaly_night_heater: bool,
) -> list[StrategyCandidate]:
    ac = device_energy.get("air_conditioner", 0.0)
    heater = device_energy.get("water_heater", 0.0)
    lighting = device_energy.get("lighting", 0.0)
    computer = device_energy.get("computer", 0.0)
    tv = device_energy.get("television", 0.0)
    other = device_energy.get("other", 0.0)

    ac_saving = ac * 0.20
    heater_saving = heater * 0.15 + (0.35 if anomaly_night_heater else 0.0)
    lighting_saving = lighting * 0.25
    peak_saving = (computer + tv + other) * 0.18

    items = [
        StrategyCandidate(
            strategy_type="ac_setpoint",
            title="空调温度从 24℃ 调整到 26℃",
            description=(
                f"问题：今日空调耗电 {ac:.2f} kWh，是家庭第一大负荷。\n"
                f"原因：室内均温约 {indoor_temp:.1f}℃，空调长时间维持 24℃ 制冷。\n"
                "建议：将设定温度提高到 26℃，并在无人时段提高至 27℃。\n"
                f"预计收益：节约 {ac_saving:.2f} kWh/天（约 {ac_saving / max(today_energy, 0.01) * 100:.1f}%）。\n"
                "用户影响：体感略暖，睡眠和客厅活动仍可接受。"
            ),
            estimated_saving_kwh=round(ac_saving, 3),
            estimated_saving_percent=round(ac_saving / max(today_energy, 0.01) * 100, 2),
            comfort_impact="轻微",
            feasibility=0.92,
            user_acceptance=0.88,
            comfort_penalty=1.2,
            problem=f"空调耗电 {ac:.2f} kWh，占比偏高",
            cause="设定温度偏低且运行时间过长",
            suggestion="设定温度 24℃ → 26℃，无人房间关闭送风",
            user_impact="体感温度上升约 1-2℃",
        ),
        StrategyCandidate(
            strategy_type="water_heater_schedule",
            title="热水器由全天待机改为定时运行",
            description=(
                f"问题：热水器今日耗电 {heater:.2f} kWh，并存在凌晨异常启动风险。\n"
                "原因：设备长时间处于加热/待机，且出现与作息不符的夜间运行。\n"
                "建议：仅在 06:30-08:00 与 18:00-22:00 加热，关闭凌晨定时。\n"
                f"预计收益：节约 {heater_saving:.2f} kWh/天。\n"
                "用户影响：早晚热水仍可用，需避免凌晨洗浴。"
            ),
            estimated_saving_kwh=round(heater_saving, 3),
            estimated_saving_percent=round(heater_saving / max(today_energy, 0.01) * 100, 2),
            comfort_impact="较低",
            feasibility=0.9,
            user_acceptance=0.86,
            comfort_penalty=0.8,
            problem="热水器待机与异常夜间启动造成浪费",
            cause="全天加热策略与家庭作息不匹配",
            suggestion="改为早晚定时加热，关闭 23:00-06:00 加热",
            user_impact="非高峰时段可能需要短暂等待热水",
        ),
        StrategyCandidate(
            strategy_type="away_lighting",
            title="离家后关闭非必要照明",
            description=(
                f"问题：照明今日耗电 {lighting:.2f} kWh，部分时段无人仍保持开启。\n"
                "原因：离家/睡眠后未及时关灯。\n"
                "建议：根据占用状态自动关闭客厅与过道灯光。\n"
                f"预计收益：节约 {lighting_saving:.2f} kWh/天。\n"
                "用户影响：几乎不影响舒适度。"
            ),
            estimated_saving_kwh=round(lighting_saving, 3),
            estimated_saving_percent=round(lighting_saving / max(today_energy, 0.01) * 100, 2),
            comfort_impact="极低",
            feasibility=0.95,
            user_acceptance=0.93,
            comfort_penalty=0.2,
            problem="无人时段照明仍在耗电",
            cause="行为习惯导致灯具忘记关闭",
            suggestion="离家和睡眠后关闭非必要照明",
            user_impact="几乎无感知",
        ),
        StrategyCandidate(
            strategy_type="peak_shift",
            title="高峰时段减少非必要高功率设备运行",
            description=(
                "问题：18:00-21:00 家庭负荷叠加，峰值功率偏高。\n"
                "原因：空调、热水器、洗衣、电脑在晚高峰同时运行。\n"
                "建议：洗衣机避开 19:00-21:00，电脑待机关闭，错峰使用。\n"
                f"预计收益：节约 {peak_saving:.2f} kWh/天，并降低峰值。\n"
                "用户影响：需要小幅调整家电使用时间。"
            ),
            estimated_saving_kwh=round(peak_saving, 3),
            estimated_saving_percent=round(peak_saving / max(today_energy, 0.01) * 100, 2),
            comfort_impact="较低",
            feasibility=0.84,
            user_acceptance=0.8,
            comfort_penalty=1.0,
            problem="晚高峰多设备叠加",
            cause="高功率家电集中在同一时段启动",
            suggestion="错峰使用洗衣机、电脑等非刚需设备",
            user_impact="需要调整部分家务时间",
        ),
    ]
    items.sort(key=lambda x: x.score, reverse=True)
    return items


def simulate_savings(
    today_energy: float,
    device_energy: dict[str, float],
    selected_types: list[str],
    anomaly_night_heater: bool,
) -> dict:
    remaining = dict(device_energy)
    if "ac_setpoint" in selected_types:
        remaining["air_conditioner"] = remaining.get("air_conditioner", 0.0) * 0.80
    if "water_heater_schedule" in selected_types:
        cut = remaining.get("water_heater", 0.0) * 0.15 + (0.35 if anomaly_night_heater else 0.0)
        remaining["water_heater"] = max(0.0, remaining.get("water_heater", 0.0) - cut)
    if "away_lighting" in selected_types:
        remaining["lighting"] = remaining.get("lighting", 0.0) * 0.75
    if "peak_shift" in selected_types:
        for key in ("computer", "television", "other", "washing_machine"):
            remaining[key] = remaining.get(key, 0.0) * 0.90

    after = sum(remaining.values())
    # 多策略叠加存在交叉，避免简单加总高估
    overlap = 1.0
    if len(selected_types) >= 3:
        overlap = 0.88
    elif len(selected_types) == 2:
        overlap = 0.94
    saving = max(0.0, (today_energy - after) * overlap)
    after_adj = today_energy - saving
    return {
        "before_kwh": round(today_energy, 3),
        "after_kwh": round(after_adj, 3),
        "saving_kwh": round(saving, 3),
        "saving_percent": round(saving / max(today_energy, 0.01) * 100, 2),
    }


def device_saving_table(device_energy: dict[str, float], device_names: dict[str, str]) -> list[dict]:
    rows = []
    factors = {
        "air_conditioner": 0.20,
        "water_heater": 0.18,
        "lighting": 0.25,
        "computer": 0.12,
        "television": 0.10,
        "washing_machine": 0.08,
        "refrigerator": 0.04,
        "other": 0.10,
    }
    for dtype, baseline in device_energy.items():
        factor = factors.get(dtype, 0.08)
        saving = baseline * factor
        optimized = baseline - saving
        rows.append(
            {
                "device_type": dtype,
                "device_name": device_names.get(dtype, DEVICE_CN.get(dtype, dtype)),
                "baseline_kwh": round(baseline, 3),
                "optimized_kwh": round(optimized, 3),
                "saving_kwh": round(saving, 3),
                "saving_percent": round(saving / max(baseline, 0.01) * 100, 2),
            }
        )
    rows.sort(key=lambda x: x["saving_kwh"], reverse=True)
    return rows
