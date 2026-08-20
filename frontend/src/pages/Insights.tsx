import { useEffect, useState } from "react";
import { Card, Col, Row, Statistic, Tag } from "antd";
import { insightApi } from "../api";
import ChartCard from "../components/ChartCard";
import { chartBase } from "../utils/chart";
import type { InsightsPayload } from "../types";

export default function Insights() {
  const [data, setData] = useState<InsightsPayload | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    insightApi.get().then(setData).finally(() => setLoading(false));
  }, []);

  const r = data?.radar;
  const radar = {
    radar: {
      indicator: [
        { name: "能效", max: 100 },
        { name: "错峰", max: 100 },
        { name: "舒适", max: 100 },
        { name: "异常控制", max: 100 },
        { name: "潜力释放", max: 100 },
      ],
    },
    series: [{
      type: "radar",
      color: "#16a34a",
      areaStyle: { opacity: 0.18 },
      data: [{
        value: [
          r?.efficiency ?? data?.energy_score.energy_score ?? 0,
          r?.offpeak ?? Math.max(0, 100 - (data?.tou.peak_share ?? 0)),
          r?.comfort ?? 0,
          r?.anomaly_control ?? 0,
          r?.potential ?? Math.min(100, (data?.saving_potential ?? 0) * 6),
        ],
      }],
    }],
  };

  const bill = {
    ...chartBase,
    xAxis: { type: "category", data: ["高峰", "平时", "谷时"] },
    yAxis: { type: "value", name: "元" },
    series: [{
      type: "bar",
      data: [
        { value: data?.tou.peak_cost ?? 0, itemStyle: { color: "#f59e0b" } },
        { value: data?.tou.flat_cost ?? 0, itemStyle: { color: "#16a34a" } },
        { value: data?.tou.valley_cost ?? 0, itemStyle: { color: "#0ea5e9" } },
      ],
    }],
  };

  const sankeyOption = {
    tooltip: { trigger: "item" },
    series: [{
      type: "sankey",
      data: [{ name: "电网" }, ...((data?.showcase?.sankey.links || []).map((l) => ({ name: l.target })))],
      links: data?.showcase?.sankey.links || [],
      lineStyle: { color: "gradient", curveness: 0.5 },
    }],
  };
  const heatOption = {
    tooltip: { position: "top" },
    visualMap: { min: 14, max: 22, orient: "horizontal", left: "center", inRange: { color: ["#dcfce7", "#16a34a", "#14532d"] } },
    calendar: { range: ["2026-07-21", "2026-08-19"], cellSize: [22, 22], left: 40, right: 20 },
    series: [{
      type: "heatmap",
      coordinateSystem: "calendar",
      data: (data?.showcase?.heatmap || []).map((d) => [d.date, d.energy]),
    }],
  };

  return (
    <div>
      <h1 className="page-title">智能洞察</h1>
      <p className="page-sub">从相关性和电价结构中找出浪费点，而不是只看总电量。</p>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={12} md={6}><Card loading={loading}><Statistic title="功率-室温相关" value={data?.correlation.power_vs_temperature ?? 0} precision={2} /></Card></Col>
        <Col xs={12} md={6}><Card loading={loading}><Statistic title="功率-占用相关" value={data?.correlation.power_vs_occupancy ?? 0} precision={2} /></Card></Col>
        <Col xs={12} md={6}><Card loading={loading}><Statistic title="今日碳排" value={data?.carbon_kg ?? 0} precision={2} suffix="kg" /></Card></Col>
        <Col xs={12} md={6}><Card loading={loading}><Statistic title="近30日百分位" value={data?.showcase?.benchmark?.percentile ?? 0} precision={1} suffix="%" /></Card></Col>
      </Row>
      {data?.showcase?.benchmark ? (
        <Card size="small" style={{ marginBottom: 16 }}>
          今日 {data.showcase.benchmark.today_kwh} kWh，{data.showcase.benchmark.label}（中位 {data.showcase.benchmark.month_median_kwh} kWh）。高峰占比 {data.showcase.benchmark.peak_share}%。
        </Card>
      ) : null}
      <div className="two-col">
        <ChartCard title="家庭能源健康雷达" loading={loading} empty={!data} option={radar} />
        <ChartCard title="分时电费" loading={loading} empty={!data} option={bill} />
      </div>
      {data?.radar?.notes ? (
        <p className="honesty-note" style={{ marginTop: 12 }}>
          舒适维：{data.radar.notes.comfort}。异常控制：{data.radar.notes.anomaly_control}。
        </p>
      ) : null}
      <div style={{ height: 16 }} />
      <ChartCard title="近 30 日用电热力" loading={loading} empty={!data?.showcase?.heatmap.length} option={heatOption} height={220} />
      <div style={{ height: 16 }} />
      <ChartCard title="设备能量桑基" loading={loading} empty={!data?.showcase?.sankey.links.length} option={sankeyOption} height={360} />
      <div style={{ height: 16 }} />
      <Card title="决策洞察">
        {(data?.insights || []).map((item) => (
          <div key={item.title} className="assistant-bubble">
            <Tag color={item.level === "alert" ? "red" : item.level === "warn" ? "gold" : "green"}>{item.level}</Tag>
            <b> {item.title}</b>
            <div style={{ marginTop: 6 }}>{item.detail}</div>
          </div>
        ))}
      </Card>
    </div>
  );
}
