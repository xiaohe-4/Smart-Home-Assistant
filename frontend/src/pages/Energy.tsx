import { useEffect, useState } from "react";
import { Card, Col, Radio, Row, Statistic, Table } from "antd";
import { deviceApi, energyApi, insightApi } from "../api";
import ChartCard from "../components/ChartCard";
import { chartBase } from "../utils/chart";
import type { DeviceItem, EnergyPoint, InsightsPayload } from "../types";
import { fulfilled } from "../utils/async";

export default function Energy() {
  const [days, setDays] = useState(7);
  const [history, setHistory] = useState<EnergyPoint[]>([]);
  const [hourly, setHourly] = useState<EnergyPoint[]>([]);
  const [devices, setDevices] = useState<DeviceItem[]>([]);
  const [insights, setInsights] = useState<InsightsPayload | null>(null);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.allSettled([energyApi.history(days), energyApi.hourly(), deviceApi.list(), insightApi.get()])
      .then(([h, hour, d, ins]) => {
        const hist = fulfilled(h, { series: [] as EnergyPoint[], total_energy: 0, start: "", end: "" });
        const hourData = fulfilled(hour, { date: "", points: [] as EnergyPoint[] });
        setHistory(hist.series);
        setTotal(hist.total_energy);
        setHourly(hourData.points);
        setDevices(fulfilled(d, []));
        setInsights(fulfilled(ins, null));
      })
      .finally(() => setLoading(false));
  }, [days]);

  const histOption = {
    ...chartBase,
    xAxis: { type: "category", data: history.map((p) => (days >= 7 ? p.timestamp.slice(5, 10) : p.timestamp.slice(11, 16))) },
    yAxis: { type: "value", name: "kWh" },
    series: [{ type: "bar", color: "#16a34a", barWidth: 18, data: history.map((p) => Number(p.energy.toFixed(3))) }],
  };
  const hourOption = {
    ...chartBase,
    legend: { data: ["实际功率", "优化功率"] },
    xAxis: { type: "category", data: hourly.map((p) => p.timestamp.slice(11, 16)) },
    yAxis: { type: "value", name: "W" },
    series: [{
      name: "实际功率",
      type: "line",
      smooth: true,
      color: "#0f766e",
      areaStyle: { opacity: 0.12 },
      markArea: { silent: true, data: [[{ xAxis: "18:00", itemStyle: { color: "rgba(245,158,11,0.10)" } }, { xAxis: "22:00" }]] },
      data: hourly.map((p) => Number(p.power.toFixed(1))),
    }, {
      name: "优化功率",
      type: "line",
      smooth: true,
      color: "#16a34a",
      lineStyle: { type: "dashed" },
      data: hourly.map((p) => {
        const h = Number(p.timestamp.slice(11, 13));
        const hit = insights?.showcase?.optimized_curve?.find((c) => c.hour === h);
        return hit ? hit.optimized : Number(p.power.toFixed(1));
      }),
    }],
  };
  const corr = insights?.correlation.hourly || [];
  const corrOption = {
    ...chartBase,
    legend: { data: ["功率", "室内温度", "占用"] },
    xAxis: { type: "category", data: corr.map((p) => p.timestamp.slice(11, 16)) },
    yAxis: [
      { type: "value", name: "W" },
      { type: "value", name: "℃ / 人", splitLine: { show: false } },
    ],
    series: [
      { name: "功率", type: "bar", color: "#86efac", data: corr.map((p) => p.power) },
      { name: "室内温度", type: "line", yAxisIndex: 1, color: "#f59e0b", data: corr.map((p) => p.temperature) },
      { name: "占用", type: "line", yAxisIndex: 1, color: "#0ea5e9", data: corr.map((p) => p.occupancy) },
    ],
  };

  return (
    <div>
      <h1 className="page-title">能耗分析</h1>
      <p className="page-sub">电量、峰谷、室温和家里有没有人，按同一天对齐着看。占比是分路电表加出来的，不是从总表里拆的。</p>
      <Radio.Group value={days} onChange={(e) => setDays(e.target.value)} style={{ marginBottom: 16 }}>
        <Radio.Button value={1}>日</Radio.Button>
        <Radio.Button value={7}>周</Radio.Button>
        <Radio.Button value={30}>月</Radio.Button>
      </Radio.Group>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={12} md={6}><Card><Statistic title="区间用电" value={total} precision={2} suffix="kWh" /></Card></Col>
        <Col xs={12} md={6}><Card><Statistic title="今日电费" value={insights?.tou.total_cost ?? 0} precision={2} suffix="元" /></Card></Col>
        <Col xs={12} md={6}><Card><Statistic title="高峰占比" value={insights?.tou.peak_share ?? 0} precision={1} suffix="%" /></Card></Col>
        <Col xs={12} md={6}><Card><Statistic title="功率-占用相关" value={insights?.correlation.power_vs_occupancy ?? 0} precision={2} /></Card></Col>
      </Row>
      <ChartCard title="历史能耗" loading={loading} empty={!history.length} option={histOption} />
      <div style={{ height: 16 }} />
      <ChartCard title="今日分时功率（虚线为按节能潜力分配后的优化曲线）" loading={loading} empty={!hourly.length} option={hourOption} />
      <div style={{ height: 16 }} />
      <ChartCard title="环境 / 行为关联" loading={loading} empty={!corr.length} option={corrOption} />
      <div style={{ height: 16 }} />
      <Card title="设备能耗分解">
        <Table
          rowKey="id"
          dataSource={devices}
          pagination={false}
          columns={[
            { title: "设备", dataIndex: "name" },
            { title: "今日耗电 (kWh)", dataIndex: "today_energy" },
            { title: "占比 (%)", dataIndex: "share" },
            { title: "运行时长 (h)", dataIndex: "runtime_hours" },
          ]}
        />
      </Card>
    </div>
  );
}
