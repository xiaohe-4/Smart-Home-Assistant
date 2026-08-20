export const chartBase = {
  tooltip: { trigger: "axis", backgroundColor: "rgba(15, 31, 26, 0.92)", borderWidth: 0, textStyle: { color: "#e8f6ee" } },
  grid: { left: 52, right: 28, top: 36, bottom: 36 },
  textStyle: { color: "#5b7166" },
};

export const peakMarkArea = {
  silent: true,
  data: [
    [
      { xAxis: "18:00", itemStyle: { color: "rgba(245, 158, 11, 0.08)" } },
      { xAxis: "22:00" },
    ],
  ],
};
