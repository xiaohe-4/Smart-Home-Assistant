export const chartBase = {
  tooltip: { trigger: "axis", backgroundColor: "rgba(15, 31, 26, 0.92)", borderWidth: 0, textStyle: { color: "#e8f6ee" } },
  grid: { left: 52, right: 36, top: 52, bottom: 32 },
  textStyle: { color: "#5b7166" },
};

function paintAxis(axis: unknown, color: string, split: string): unknown {
  if (!axis) return axis;
  if (Array.isArray(axis)) return axis.map((item) => paintAxis(item, color, split));
  if (typeof axis !== "object") return axis;
  const current = axis as Record<string, unknown>;
  const splitLine = (current.splitLine && typeof current.splitLine === "object" ? current.splitLine : {}) as Record<string, unknown>;
  return {
    ...current,
    axisLabel: { color, ...(current.axisLabel as object | undefined) },
    nameTextStyle: { color, ...(current.nameTextStyle as object | undefined) },
    splitLine: {
      ...splitLine,
      lineStyle: { color: split, ...(splitLine.lineStyle as object | undefined) },
    },
  };
}

export function themedOption(option: Record<string, unknown>, dark: boolean) {
  const color = dark ? "#c5ddd2" : "#5b7166";
  const split = dark ? "rgba(231, 246, 238, 0.1)" : "rgba(15, 61, 46, 0.08)";
  const next: Record<string, unknown> = {
    ...option,
    backgroundColor: "transparent",
    textStyle: { color, ...(option.textStyle as object | undefined) },
  };
  if (option.xAxis) next.xAxis = paintAxis(option.xAxis, color, split);
  if (option.yAxis) next.yAxis = paintAxis(option.yAxis, color, split);
  const paintLegend = (legend: unknown) => {
    if (!legend || typeof legend !== "object") return legend;
    const item = legend as Record<string, unknown>;
    return { ...item, textStyle: { color, ...(item.textStyle as object | undefined) } };
  };
  if (Array.isArray(option.legend)) next.legend = option.legend.map(paintLegend);
  else if (option.legend) next.legend = paintLegend(option.legend);
  if (Array.isArray(option.series)) {
    next.series = option.series.map((series) => {
      if (!series || typeof series !== "object") return series;
      const item = series as Record<string, unknown>;
      if (item.type !== "sankey") return series;
      return { ...item, label: { color, ...(item.label as object | undefined) } };
    });
  }
  return next;
}

export const peakMarkArea = {
  silent: true,
  data: [
    [
      { xAxis: "18:00", itemStyle: { color: "rgba(245, 158, 11, 0.08)" } },
      { xAxis: "22:00" },
    ],
  ],
};
