import { http } from "./http";
import type {
  AnomalyItem,
  AssistantData,
  DeviceItem,
  EnergyPoint,
  EnergySummary,
  EnergyToday,
  InsightsPayload,
  PredictionResult,
  ProfileData,
  SavingPotential,
  SimulateResult,
  StrategyItem,
  ButlerReply,
  ButlerState,
  LifeOs,
  SourceDegrade,
  SourceMap,
  SourceValidate,
  ModelLab,
} from "../types";

export const energyApi = {
  today: () => http.get<EnergyToday>("/energy/today").then((r) => r.data),
  summary: () => http.get<EnergySummary>("/energy/summary").then((r) => r.data),
  history: (days = 7) =>
    http.get<{ start: string; end: string; total_energy: number; series: EnergyPoint[] }>("/energy/history", {
      params: { days },
    }).then((r) => r.data),
  hourly: (date?: string) =>
    http.get<{ date: string; points: EnergyPoint[] }>("/energy/hourly", { params: { date } }).then((r) => r.data),
};

export const deviceApi = {
  list: () => http.get<DeviceItem[]>("/devices").then((r) => r.data),
  energy: (id: number) => http.get<EnergyPoint[]>(`/devices/${id}/energy`).then((r) => r.data),
};

export const predictionApi = {
  hour: () => http.get<PredictionResult>("/prediction/hour").then((r) => r.data),
  day: (hours = 24) => http.get<PredictionResult>("/prediction/day", { params: { hours } }).then((r) => r.data),
};

export const anomalyApi = {
  list: () => http.get<AnomalyItem[]>("/anomalies").then((r) => r.data),
  latest: () => http.get<AnomalyItem[]>("/anomalies/latest").then((r) => r.data),
};

export const strategyApi = {
  list: () => http.get<StrategyItem[]>("/strategies").then((r) => r.data),
  top: () => http.get<StrategyItem[]>("/strategies/top").then((r) => r.data),
  simulate: (strategyIds: number[]) =>
    http.post<SimulateResult>("/strategies/simulate", { strategy_ids: strategyIds }).then((r) => r.data),
};

export const profileApi = {
  get: () => http.get<ProfileData>("/profile").then((r) => r.data),
  score: () => http.get("/profile/energy-score").then((r) => r.data),
  potential: () => http.get<SavingPotential>("/profile/saving-potential").then((r) => r.data),
  assistant: () => http.get<AssistantData>("/profile/assistant").then((r) => r.data),
  experiments: () => http.get("/profile/experiments").then((r) => r.data),
};

export const insightApi = {
  get: () => http.get<InsightsPayload>("/insights").then((r) => r.data),
  correlation: () => http.get("/insights/correlation").then((r) => r.data),
  chat: (question: string) => http.post("/insights/chat", { question }).then((r) => r.data),
};

export const butlerApi = {
  state: () => http.get<ButlerState>("/butler/state").then((r) => r.data),
  command: (text: string) => http.post<ButlerReply>("/butler/command", { text }).then((r) => r.data),
};

export const lifeApi = {
  get: () => http.get<LifeOs>("/life").then((r) => r.data),
  toggleRule: (key: string, armed: boolean) => http.post<LifeOs>("/life/rules", { key, armed }).then((r) => r.data),
  mission: (key: string, done = true, execute = false) =>
    http.post<LifeOs>("/life/missions", { key, done, execute }).then((r) => r.data),
  demand: (action: string) => http.post<LifeOs>("/life/demand", { action }).then((r) => r.data),
  schedule: (task: string, booked = true) => http.post<LifeOs>("/life/schedule", { task, booked }).then((r) => r.data),
  comfort: (mode: string, execute = false) => http.post<LifeOs>("/life/comfort", { mode, execute }).then((r) => r.data),
};

export const sourceApi = {
  get: () => http.get<SourceMap>("/sources").then((r) => r.data),
  degrade: (drop: string[]) =>
    http.get<SourceDegrade>("/sources/degrade", { params: { drop: drop.join(",") } }).then((r) => r.data),
  validate: (modality: string, rows: Record<string, unknown>[]) =>
    http.post<SourceValidate>("/sources/validate", { modality, rows }).then((r) => r.data),
};

export const modelsApi = {
  get: () => http.get<ModelLab>("/models").then((r) => r.data),
};
