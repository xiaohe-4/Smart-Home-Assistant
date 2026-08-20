export interface EnergyPoint {
  timestamp: string;
  power: number;
  energy: number;
}

export interface EnergyToday {
  date: string;
  total_energy: number;
  current_power: number;
  peak_power: number;
  peak_time: string | null;
  compared_yesterday_percent: number | null;
  compared_week_avg_percent: number | null;
  series: EnergyPoint[];
}

export interface EnergySummary {
  today_energy: number;
  yesterday_energy: number;
  week_avg_energy: number;
  month_energy: number;
  current_power: number;
  peak_power: number;
  main_device: string;
  main_device_share: number;
}

export interface DeviceItem {
  id: number;
  name: string;
  device_type: string;
  rated_power: number;
  status: string;
  today_energy: number;
  share: number;
  runtime_hours: number;
  current_power: number;
  baseline_power?: number;
  controlled?: boolean;
  setpoint?: number | null;
  actuator_note?: string | null;
}

export interface PredictionPoint {
  timestamp: string;
  predicted_power: number;
  actual_power: number | null;
}

export interface PredictionResult {
  horizon_hours: number;
  model_name: string;
  model_version: string;
  metrics: Record<string, number>;
  history: PredictionPoint[];
  forecast: PredictionPoint[];
}

export interface AnomalyItem {
  id: number;
  timestamp: string;
  device_id: number | null;
  anomaly_score: number;
  anomaly_type: string;
  description: string;
  severity: string;
  status: string;
  device_name: string | null;
  explain?: Array<{ feature: string; weight: number; note: string }>;
}

export interface StrategyItem {
  id: number;
  strategy_type: string;
  title: string;
  description: string;
  estimated_saving_kwh: number;
  estimated_saving_percent: number;
  comfort_impact: string;
  feasibility: number;
  score: number;
}

export interface SimulateResult {
  before_kwh: number;
  after_kwh: number;
  saving_kwh: number;
  saving_percent: number;
  before_cost: number;
  after_cost: number;
  saving_cost: number;
  before_carbon: number;
  after_carbon: number;
  applied: StrategyItem[];
  hourly?: Array<{
    hour: number;
    label: string;
    actual_power: number;
    optimized_power: number;
    actual_kwh: number;
    optimized_kwh: number;
  }>;
}

export interface ProfileData {
  household_name: string;
  household_size: number;
  home_type: string;
  city: string;
  season: string;
  today_energy: number;
  yesterday_energy: number;
  week_avg_energy: number;
  month_energy: number;
  peak_power: number;
  peak_time: string | null;
  main_device: string;
  energy_score: number;
  saving_potential_percent: number;
  compared_yesterday_percent: number | null;
  compared_week_avg_percent: number | null;
}

export interface SavingPotential {
  total_baseline_kwh: number;
  total_optimized_kwh: number;
  total_saving_kwh: number;
  total_saving_percent: number;
  devices: Array<{
    device_type: string;
    device_name: string;
    baseline_kwh: number;
    optimized_kwh: number;
    saving_kwh: number;
    saving_percent: number;
  }>;
}

export interface AssistantData {
  summary: string;
  today_energy: number;
  main_device: string;
  saving_potential: number;
  anomaly: string | null;
}

export interface InsightItem {
  level: "info" | "warn" | "alert" | "ok";
  title: string;
  detail: string;
}

export interface TwinData {
  as_of: string | null;
  occupancy: number;
  activity: string;
  location: string;
  indoor_temp: number | null;
  humidity: number | null;
  co2: number | null;
  weather: string | null;
  outdoor_temp: number | null;
  current_power: number;
  running_devices: DeviceItem[];
}

export interface TimelinePoint {
  timestamp: string;
  power: number;
  energy: number;
  occupancy: number;
  temperature: number | null;
  period: string;
}

export interface InsightsPayload {
  stats: EnergySummary & {
    date: string;
    compared_yesterday_percent: number | null;
    compared_week_avg_percent: number | null;
    today_energy: number;
  };
  tou: {
    peak_kwh: number;
    flat_kwh: number;
    valley_kwh: number;
    peak_cost: number;
    flat_cost: number;
    valley_cost: number;
    total_cost: number;
    avg_price: number;
    peak_share: number;
  };
  carbon_kg: number;
  month_carbon_kg: number;
  energy_score: { energy_score: number };
  saving_potential: number;
  insights: InsightItem[];
  correlation: {
    power_vs_temperature: number;
    power_vs_occupancy: number;
    power_vs_outdoor: number;
    hourly: Array<{
      timestamp: string;
      power: number;
      energy: number;
      temperature: number | null;
      occupancy: number | null;
      outdoor_temp: number | null;
    }>;
  };
  twin: TwinData;
  timeline: TimelinePoint[];
  top_strategies: Array<{
    id: number;
    title: string;
    estimated_saving_percent: number;
    comfort_impact: string;
    score: number;
  }>;
  radar?: {
    efficiency: number;
    offpeak: number;
    comfort: number;
    anomaly_control: number;
    potential: number;
    notes?: Record<string, string>;
  };
  profile: ProfileData;
  assistant: AssistantData;
  showcase?: {
    highlights: Array<{ tag: string; title: string; detail: string }>;
    story: Array<{ time: string; title: string; detail: string }>;
    heatmap: Array<{ date: string; energy: number }>;
    sankey: { links: Array<{ source: string; target: string; value: number }> };
    rooms: Array<{ name: string; energy: number; running: string[]; active: boolean }>;
    equivalents: {
      carbon_kg: number;
      car_km: number;
      tree_days: number;
      night_kwh: number;
      away_kwh: number;
      score: number;
    };
    questions: Array<{ q: string; a: string }>;
    replay?: Array<{
      hour: number;
      label: string;
      power: number;
      occupancy: number;
      activity: string;
      location: string;
      temperature: number | null;
      period: string;
      price: number;
      action: string;
      optimized_power?: number;
      energy_so_far?: number;
      cost_so_far?: number;
      carbon_so_far?: number;
      brief?: string;
      alert?: boolean;
      energy?: number;
    }>;
    dispatch?: Array<{
      hour: number;
      label: string;
      action: string;
      power: number;
      period: string;
      reason: string;
    }>;
    optimized_curve?: Array<{ hour: number; label: string; actual: number; optimized: number }>;
    benchmark?: {
      today_kwh: number;
      month_median_kwh: number;
      vs_median_percent: number;
      percentile: number;
      label: string;
      peak_share: number;
      carbon_kg: number;
    };
  };
}

export interface ButlerAction {
  device_id: number;
  name: string;
  device_type: string;
  action: string;
  before_power: number;
  after_power: number;
}

export interface ButlerSkillItem {
  title: string;
  cmd: string;
  desc: string;
}

export interface ButlerState {
  scene: string;
  baseline_power: number;
  current_power: number;
  saving_w: number;
  saving_kwh_est: number;
  saving_carbon: number;
  devices: DeviceItem[];
  logs: Array<{ command: string; intent: string; speech: string; created_at: string }>;
  pending_cmd?: string;
  pending_reason?: string;
  preferred_ac?: number;
  quiet?: boolean;
  brief?: string;
  skills?: Array<{ group: string; items: ButlerSkillItem[] }>;
  suggestions?: Array<{ label: string; cmd: string; why: string }>;
  clock?: LifeClock;
}

export interface ButlerReply extends ButlerState {
  speech: string;
  intent: string;
  actions: ButlerAction[];
}

export interface LifeClock {
  as_of: string;
  period: string;
  period_label: string;
  price: number;
  next_period: string;
  next_label: string;
  next_at: string;
  minutes_left: number;
  advice: string;
}

export interface LifeOs {
  clock: LifeClock;
  budget: {
    month_kwh: number;
    month_cost: number;
    expected_cost: number;
    pace_percent: number;
    label: string;
    avg_price: number;
  };
  nilm: { hours: string[]; series: Array<{ name: string; data: number[] }> };
  family: Array<{ name: string; role: string; direct_kwh: number; shared_kwh: number; kwh: number; habit: string; share: number }>;
  health: Array<{ id: number; name: string; device_type: string; runtime_hours: number; today_energy: number; status: string; level: string; hint: string }>;
  weather: { indoor: number | null; outdoor: number | null; weather: string | null; delta: number | null; advice: string };
  rules: Array<{ key: string; title: string; when: string; then: string; armed: boolean; firing: boolean }>;
  notices: Array<{ level: string; title: string; detail: string; action: string }>;
  badges: Array<{ id: string; title: string; how: string; earned: boolean }>;
  ledger: Array<{ date: string; kwh: number; cost: number; carbon: number }>;
  whatif: { ac_kwh: number; per_degree_kwh: number; note: string };
  occupancy: number;
  missions: Array<{
    key: string;
    title: string;
    why: string;
    command: string;
    kind: string;
    done: boolean;
    saving_kwh: number;
    saving_yuan: number;
  }>;
  demand: {
    id: string;
    title: string;
    window: string;
    target_percent: number;
    current_w: number;
    target_w: number;
    cut_w: number;
    reward_yuan: number;
    status: string;
    progress: number;
    note: string;
  };
  shift: {
    peak_kwh: number;
    movable_kwh: number;
    saving_yuan: number;
    saving_carbon: number;
    price_gap: number;
    note: string;
    items: Array<{ device_type: string; name: string; peak_kwh: number; ratio: number; movable_kwh: number; saving_yuan: number }>;
  };
  standby: {
    window: string;
    wasted_kwh: number;
    wasted_yuan: number;
    note: string;
    items: Array<{ device_type: string; name: string; kwh: number; cost: number; level: string; hint: string }>;
  };
  schedule: Array<{
    key: string;
    title: string;
    slot: string;
    period: string;
    saving_kwh: number;
    saving_yuan: number;
    booked: boolean;
    hint: string;
  }>;
  tomorrow: {
    ready: boolean;
    model?: string;
    r2?: number | null;
    peak?: { hour: number; label: string; w: number } | null;
    tonight_peak?: { hour: number; label: string; w: number } | null;
    advice: string;
    points: Array<{ hour: number; label: string; w: number }>;
  };
  defense: {
    headline: string;
    facts: Array<{ label: string; value: string }>;
    family_top: string | null;
    closing: string;
  };
  challenge: { title: string; goal: string; done: number; target: number; points: number; badges: number; label: string };
  comfort: { mode: string; label: string; ac: number; hint: string; command: string };
  tou: { peak_kwh: number; peak_share: number; total_cost: number };
}

export interface SourceModality {
  key: string;
  label: string;
  table: string;
  hardware: string;
  fields: string[];
  required: string[];
  used_by: string[];
  note: string;
  rows: number;
  start: string | null;
  end: string | null;
  coverage: number;
  active: boolean;
}

export interface SourceMap {
  mode: string;
  city: string;
  season: string;
  household: { id: number; name: string; size: number; home_type: string };
  tariff: { peak: number; flat: number; valley: number; carbon: number };
  devices: Array<{ id: number; name: string; device_type: string; rated_power: number }>;
  modalities: SourceModality[];
  alignment: {
    date: string;
    points: number;
    aligned: number;
    percent: number;
    interval_minutes: number;
    missing: Record<string, number>;
    note: string;
  };
  forecast_features: string[];
  adapters: Array<{ id: string; label: string; status: string; how: string; writes: string[]; active: boolean }>;
  portability: Array<{ step: number; title: string; detail: string }>;
  limits: string[];
  honesty: string;
}

export interface SourceDegrade {
  dropped: string[];
  before: Record<string, number>;
  after: Record<string, number>;
  kept_features: string[];
  lost_features: string[];
  broken: string[];
  note: string;
}

export interface SourceValidate {
  ok: boolean;
  modality?: string;
  rows?: number;
  checked?: number;
  errors?: Array<{ row: number; field: string; error: string }>;
  would_write?: boolean;
  mode?: string;
  note?: string;
  detail?: string;
  contract?: { required: string[]; fields: string[]; hardware: string };
}

export interface ModelImportance {
  feature: string;
  label: string;
  importance: number;
}

export interface ModelLab {
  generated_at?: string;
  source: string;
  honesty: string;
  forecast: {
    available: boolean;
    model_name: string;
    model_version?: string;
    samples?: number;
    metrics: Record<string, number>;
    features: string[];
    feature_importance: ModelImportance[];
    not_in_model: string[];
    honesty: string;
  };
  anomaly: {
    available: boolean;
    model_name: string;
    samples?: number;
    precision?: number;
    recall?: number;
    f1?: number;
    labeled?: number;
    detected?: number;
    honesty: string;
  };
  load: {
    available: boolean;
    model_name: string;
    accuracy?: number;
    macro_f1?: number;
    samples?: number;
    not_nilm: boolean;
    feature_importance: ModelImportance[];
    honesty: string;
    live: {
      samples: Array<{
        device_type: string;
        label: string;
        pred: string;
        pred_label: string;
        hit: boolean;
        mean_power: number;
        peak_power: number;
        start_hour: number;
      }>;
      hits: number;
      n: number;
      confusions: Array<{ true: string; pred: string; count: number }>;
      note: string;
    };
  };
  strategy: {
    today_energy?: number;
    top_strategy?: string;
    anomaly_night_heater?: boolean;
    devices: Array<{ device_type: string; label: string; kwh: number; share: number }>;
    honesty: string;
  };
}
