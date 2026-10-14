export function formatKwh(value?: number | null, digits = 2) {
  if (value === undefined || value === null || Number.isNaN(value)) return "--";
  return `${value.toFixed(digits)} kWh`;
}

export function formatKw(value?: number | null) {
  if (value === undefined || value === null || Number.isNaN(value)) return "--";
  return `${(value / 1000).toFixed(2)} kW`;
}

export function formatPercent(value?: number | null) {
  if (value === undefined || value === null || Number.isNaN(value)) return "--";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(1)}%`;
}

export function severityColor(severity: string) {
  if (severity === "critical") return "red";
  if (severity === "high") return "volcano";
  if (severity === "medium") return "gold";
  return "green";
}

export function activityLabel(activity?: string | null) {
  const map: Record<string, string> = {
    sleeping: "睡觉",
    cooking: "做饭",
    leaving_home: "出门",
    resting: "休息",
    working: "工作",
    watching_tv: "看电视",
    returning_home: "回家",
    unknown: "活动不明",
  };
  if (!activity) return "待机";
  return map[activity] || activity;
}

export function severityLabel(severity: string) {
  const map: Record<string, string> = {
    critical: "严重",
    high: "高",
    medium: "中",
    low: "低",
  };
  return map[severity] || severity;
}

export function anomalyTypeLabel(type: string) {
  const map: Record<string, string> = {
    unusual_time: "异常时段启动",
    high_power: "异常高功率",
    long_running: "长时间运行",
    habit_deviation: "习惯偏离",
  };
  return map[type] || type;
}
