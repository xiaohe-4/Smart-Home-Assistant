from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class DeviceOut(ORMModel):
    id: int
    user_id: int
    name: str
    device_type: str
    rated_power: float
    status: str


class DeviceEnergyOut(BaseModel):
    id: int
    name: str
    device_type: str
    rated_power: float
    status: str
    today_energy: float
    share: float
    runtime_hours: float
    current_power: float
    baseline_power: float = 0
    controlled: bool = False
    setpoint: float | None = None
    actuator_note: str | None = None


class EnergyPoint(BaseModel):
    timestamp: datetime
    power: float
    energy: float


class EnergyTodayOut(BaseModel):
    date: str
    total_energy: float
    current_power: float
    peak_power: float
    peak_time: datetime | None
    compared_yesterday_percent: float | None
    compared_week_avg_percent: float | None
    series: list[EnergyPoint]


class EnergyHistoryOut(BaseModel):
    start: datetime
    end: datetime
    total_energy: float
    series: list[EnergyPoint]


class HourlyEnergyOut(BaseModel):
    date: str
    points: list[EnergyPoint]


class EnergySummaryOut(BaseModel):
    today_energy: float
    yesterday_energy: float
    week_avg_energy: float
    month_energy: float
    current_power: float
    peak_power: float
    main_device: str
    main_device_share: float


class PredictionPoint(BaseModel):
    timestamp: datetime
    predicted_power: float
    actual_power: float | None = None


class PredictionOut(BaseModel):
    horizon_hours: int
    model_name: str
    model_version: str
    metrics: dict[str, float]
    history: list[PredictionPoint]
    forecast: list[PredictionPoint]


class AnomalyFactor(BaseModel):
    feature: str
    weight: float
    note: str


class AnomalyOut(ORMModel):
    id: int
    user_id: int
    timestamp: datetime
    device_id: int | None
    anomaly_score: float
    anomaly_type: str
    description: str
    severity: str
    status: str
    device_name: str | None = None
    explain: list[AnomalyFactor] = Field(default_factory=list)


class StrategyOut(ORMModel):
    id: int
    user_id: int
    strategy_type: str
    title: str
    description: str
    estimated_saving_kwh: float
    estimated_saving_percent: float
    comfort_impact: str
    feasibility: float
    score: float


class SimulateRequest(BaseModel):
    strategy_ids: list[int] = Field(default_factory=list)


class HourlyOptPoint(BaseModel):
    hour: int
    label: str
    actual_power: float
    optimized_power: float
    actual_kwh: float
    optimized_kwh: float


class SimulateOut(BaseModel):
    before_kwh: float
    after_kwh: float
    saving_kwh: float
    saving_percent: float
    before_cost: float = 0
    after_cost: float = 0
    saving_cost: float = 0
    before_carbon: float = 0
    after_carbon: float = 0
    applied: list[StrategyOut]
    hourly: list[HourlyOptPoint] = Field(default_factory=list)


class ChatRequest(BaseModel):
    question: str = ""


class DeviceSavingOut(BaseModel):
    device_type: str
    device_name: str
    baseline_kwh: float
    optimized_kwh: float
    saving_kwh: float
    saving_percent: float


class ProfileOut(BaseModel):
    household_name: str
    household_size: int
    home_type: str
    city: str
    season: str
    today_energy: float
    yesterday_energy: float
    week_avg_energy: float
    month_energy: float
    peak_power: float
    peak_time: datetime | None
    main_device: str
    energy_score: float
    saving_potential_percent: float
    compared_yesterday_percent: float | None
    compared_week_avg_percent: float | None


class EnergyScoreOut(BaseModel):
    energy_score: float
    abnormal_penalty: float
    peak_penalty: float
    waste_penalty: float


class SavingPotentialOut(BaseModel):
    total_baseline_kwh: float
    total_optimized_kwh: float
    total_saving_kwh: float
    total_saving_percent: float
    devices: list[DeviceSavingOut]


class AssistantOut(BaseModel):
    summary: str
    today_energy: float
    main_device: str
    saving_potential: float
    anomaly: str | None


class ButlerCommand(BaseModel):
    text: str = ""
