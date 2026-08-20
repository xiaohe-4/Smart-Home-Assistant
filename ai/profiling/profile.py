from datetime import datetime


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def energy_efficiency_score(
    today_energy: float,
    week_avg_energy: float,
    anomaly_count: int,
    peak_power: float,
    waste_kwh: float,
) -> dict[str, float]:
    abnormal_penalty = min(18.0, anomaly_count * 3.5)
    peak_penalty = 0.0
    if peak_power > 4500:
        peak_penalty = min(15.0, (peak_power - 4500) / 200)
    elif peak_power > 3500:
        peak_penalty = min(8.0, (peak_power - 3500) / 250)

    waste_penalty = min(20.0, waste_kwh / max(today_energy, 0.1) * 100 * 0.6)
    baseline_penalty = 0.0
    if week_avg_energy > 0 and today_energy > week_avg_energy * 1.15:
        baseline_penalty = min(8.0, (today_energy / week_avg_energy - 1.15) * 40)

    score = 100 - abnormal_penalty - peak_penalty - waste_penalty - baseline_penalty
    return {
        "energy_score": round(clamp(score), 1),
        "abnormal_penalty": round(abnormal_penalty, 2),
        "peak_penalty": round(peak_penalty, 2),
        "waste_penalty": round(waste_penalty, 2),
    }


def portrait_summary(
    today_energy: float,
    yesterday_energy: float,
    week_avg: float,
    month_energy: float,
    peak_power: float,
    peak_time: datetime | None,
    main_device: str,
    score: float,
    saving_potential: float,
) -> dict:
    vs_yesterday = None
    vs_week = None
    if yesterday_energy > 0:
        vs_yesterday = round((today_energy - yesterday_energy) / yesterday_energy * 100, 1)
    if week_avg > 0:
        vs_week = round((today_energy - week_avg) / week_avg * 100, 1)
    return {
        "today_energy": round(today_energy, 2),
        "yesterday_energy": round(yesterday_energy, 2),
        "week_avg_energy": round(week_avg, 2),
        "month_energy": round(month_energy, 2),
        "peak_power": round(peak_power, 1),
        "peak_time": peak_time,
        "main_device": main_device,
        "energy_score": score,
        "saving_potential_percent": round(saving_potential, 2),
        "compared_yesterday_percent": vs_yesterday,
        "compared_week_avg_percent": vs_week,
    }
