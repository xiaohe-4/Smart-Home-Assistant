import { useCallback, useEffect, useState } from "react";
import { Button, Card, Checkbox, Col, Row, Slider, Space, Statistic, Tag, Typography, message } from "antd";
import { useNavigate } from "react-router-dom";
import { strategyApi, insightApi } from "../api";
import ChartCard from "../components/ChartCard";
import type { InsightsPayload, SimulateResult, StrategyItem } from "../types";
import { fulfilled } from "../utils/async";

export default function Strategy() {
  const nav = useNavigate();
  const [items, setItems] = useState<StrategyItem[]>([]);
  const [selected, setSelected] = useState<number[]>([]);
  const [raw, setRaw] = useState<SimulateResult | null>(null);
  const [sim, setSim] = useState<SimulateResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [comfort, setComfort] = useState(70);
  const [dispatch, setDispatch] = useState<NonNullable<InsightsPayload["showcase"]>["dispatch"]>([]);

  const applyComfort = useCallback((result: SimulateResult, factor: number): SimulateResult => ({
    ...result,
    after_kwh: Number((result.before_kwh - result.saving_kwh * factor).toFixed(3)),
    saving_kwh: Number((result.saving_kwh * factor).toFixed(3)),
    saving_percent: Number((result.saving_percent * factor).toFixed(2)),
    after_cost: Number((result.before_cost - result.saving_cost * factor).toFixed(2)),
    saving_cost: Number((result.saving_cost * factor).toFixed(2)),
    after_carbon: Number((result.before_carbon - (result.before_carbon - result.after_carbon) * factor).toFixed(3)),
    hourly: (result.hourly || []).map((h) => ({
      ...h,
      optimized_power: Number((h.actual_power - (h.actual_power - h.optimized_power) * factor).toFixed(1)),
      optimized_kwh: Number((h.actual_kwh - (h.actual_kwh - h.optimized_kwh) * factor).toFixed(3)),
    })),
  }), []);

  const runSim = useCallback(async (ids?: number[], quiet = false) => {
    const result = await strategyApi.simulate(ids || selected);
    setRaw(result);
    setSim(applyComfort(result, comfort / 100));
    if (!quiet) message.success("已完成多目标节能模拟");
  }, [selected, comfort, applyComfort]);

  useEffect(() => {
    if (raw) setSim(applyComfort(raw, comfort / 100));
  }, [comfort, raw, applyComfort]);

  useEffect(() => {
    let cancelled = false;
    Promise.allSettled([strategyApi.list(), insightApi.get()]).then(async ([listRes, insightsRes]) => {
      const list = fulfilled(listRes, [] as StrategyItem[]);
      const insights = fulfilled(insightsRes, null as InsightsPayload | null);
      if (cancelled) return;
      setItems(list);
      const autosim = sessionStorage.getItem("se-autosim") === "1";
      if (autosim) sessionStorage.removeItem("se-autosim");
      const preferred = list.find((item) => /空调|26/.test(`${item.title} ${item.description}`));
      const ids = autosim && preferred ? [preferred.id] : list.slice(0, 3).map((i) => i.id);
      setSelected(ids);
      setDispatch(insights?.showcase?.dispatch || []);
      if (ids.length) {
        try {
          const result = await strategyApi.simulate(ids);
          if (!cancelled) {
            setRaw(result);
            setSim(applyComfort(result, 0.7));
          }
        } catch {
          /* 列表仍可展示 */
        }
      }
    }).finally(() => {
      if (!cancelled) setLoading(false);
    });
    return () => { cancelled = true; };
  }, [applyComfort]);

  useEffect(() => {
    const handler = () => {
      sessionStorage.removeItem("se-autosim");
      void runSim();
    };
    window.addEventListener("se-autosim", handler);
    return () => window.removeEventListener("se-autosim", handler);
  }, [runSim]);

  const option = {
    tooltip: { trigger: "axis" },
    xAxis: { type: "category", data: ["用电 kWh", "电费 元", "碳排 kg"] },
    yAxis: { type: "value" },
    legend: { data: ["优化前", "优化后"] },
    series: [
      { name: "优化前", type: "bar", color: "#94a3b8", data: sim ? [sim.before_kwh, sim.before_cost, sim.before_carbon] : [] },
      { name: "优化后", type: "bar", color: "#16a34a", data: sim ? [sim.after_kwh, sim.after_cost, sim.after_carbon] : [] },
    ],
  };

  const hourlyOption = {
    tooltip: { trigger: "axis" },
    legend: { data: ["优化前", "优化后"] },
    xAxis: { type: "category", data: (sim?.hourly || []).map((h) => h.label) },
    yAxis: { type: "value", name: "W" },
    series: [
      { name: "优化前", type: "line", color: "#94a3b8", data: (sim?.hourly || []).map((h) => h.actual_power) },
      { name: "优化后", type: "line", color: "#16a34a", areaStyle: { opacity: 0.12 }, data: (sim?.hourly || []).map((h) => h.optimized_power) },
    ],
  };

  return (
    <div>
      <h1 className="page-title">节能建议</h1>
      <p className="page-sub">空调从 24℃ 调到 26℃，按这户今天的空调电量估，不是全市平均。不接真实插座。滑杆只是把算出的节电放大或缩小。</p>
      <Row gutter={16}>
        <Col xs={24} lg={14}>
          <Card loading={loading} extra={
            <Space>
              <Button onClick={() => { sessionStorage.setItem("se-butler-cmd", "执行今晚节能方案"); nav("/butler"); }}>让宝强去执行</Button>
              <Button type="primary" disabled={!selected.length} onClick={() => runSim()}>模拟优化</Button>
            </Space>
          }>
            <div className="comfort-row">
              <span>舒适优先</span>
              <Slider min={40} max={100} value={comfort} onChange={setComfort} />
              <span>节能优先 {comfort}%</span>
            </div>
            <Checkbox.Group value={selected} onChange={(v) => setSelected(v as number[])} style={{ width: "100%" }}>
              {items.map((item) => (
                <Card key={item.id} size="small" style={{ marginBottom: 12 }}>
                  <Checkbox value={item.id}><b>{item.title}</b></Checkbox>
                  <div className="strategy-copy">{item.description}</div>
                  <Tag color="green">节约 {item.estimated_saving_percent.toFixed(1)}%</Tag>
                  <Tag>可行性 {(item.feasibility * 100).toFixed(0)}%</Tag>
                  <Tag>舒适度 {item.comfort_impact}</Tag>
                  <Tag>评分 {item.score}</Tag>
                </Card>
              ))}
            </Checkbox.Group>
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card title="优化效果" style={{ marginBottom: 16 }}>
            {sim ? (
              <>
                <Statistic title="节约比例" value={sim.saving_percent} precision={2} suffix="%" />
                <Typography.Paragraph style={{ margin: "12px 0" }}>
                  用电 {sim.before_kwh.toFixed(2)} → {sim.after_kwh.toFixed(2)} kWh ·
                  电费 {sim.before_cost.toFixed(2)} → {sim.after_cost.toFixed(2)} 元 ·
                  碳排 {sim.before_carbon.toFixed(2)} → {sim.after_carbon.toFixed(2)} kg
                </Typography.Paragraph>
                <ChartCard title="" empty={false} option={option} height={220} />
                <div style={{ height: 12 }} />
                <ChartCard title="24h 削峰填谷" empty={!sim.hourly?.length} option={hourlyOption} height={220} />
              </>
            ) : (
              <Typography.Text type="secondary">正在加载 Top 策略模拟；也可手动勾选后点“模拟优化”。</Typography.Text>
            )}
          </Card>
          <Card title="24h 调度指令">
            {(dispatch || []).map((d) => (
              <div key={d.label} className="dispatch-item" style={{ marginBottom: 8 }}>
                <b>{d.label}</b> {d.action}
                <div className="explain-note">{d.reason}</div>
              </div>
            ))}
          </Card>
        </Col>
      </Row>
    </div>
  );
}
