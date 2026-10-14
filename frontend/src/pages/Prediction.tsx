import { useEffect, useState } from "react";
import { Card, Col, Radio, Row, Statistic } from "antd";
import { useNavigate } from "react-router-dom";
import { modelsApi, predictionApi } from "../api";
import ChartCard from "../components/ChartCard";
import type { ModelLab, PredictionResult } from "../types";

export default function Prediction() {
  const nav = useNavigate();
  const [data, setData] = useState<PredictionResult | null>(null);
  const [lab, setLab] = useState<ModelLab | null>(null);
  const [hours, setHours] = useState(24);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.allSettled([predictionApi.day(hours), modelsApi.get()]).then(([pred, models]) => {
      if (pred.status === "fulfilled") setData(pred.value);
      if (models.status === "fulfilled") setLab(models.value);
    }).finally(() => setLoading(false));
  }, [hours]);

  const rmse = data?.metrics?.RMSE ?? 0;
  const hist = data?.history || [];
  const forecast = data?.forecast || [];
  const lower = forecast.map((p) => Math.max(0, p.predicted_power - rmse));
  const span = forecast.map((p, i) => Math.max(0, p.predicted_power + rmse - lower[i]));
  const histPad = Array(hist.length).fill(null);
  const option = {
    tooltip: { trigger: "axis" },
    legend: { data: ["历史真实值", "未来预测值", "RMSE 置信带"] },
    xAxis: {
      type: "category",
      data: [...hist.map((p) => p.timestamp.slice(5, 16)), ...forecast.map((p) => p.timestamp.slice(5, 16))],
    },
    yAxis: { type: "value", name: "W" },
    series: [
      {
        name: "区间下限",
        type: "line",
        symbol: "none",
        stack: "conf",
        lineStyle: { opacity: 0 },
        tooltip: { show: false },
        data: [...histPad, ...lower.map((v) => Number(v.toFixed(1)))],
      },
      {
        name: "RMSE 置信带",
        type: "line",
        symbol: "none",
        stack: "conf",
        lineStyle: { opacity: 0 },
        areaStyle: { color: "rgba(22,163,74,0.18)" },
        data: [...histPad, ...span.map((v) => Number(v.toFixed(1)))],
      },
      {
        name: "历史真实值",
        type: "line",
        color: "#64748b",
        data: [...hist.map((p) => p.actual_power), ...Array(forecast.length).fill(null)],
      },
      {
        name: "未来预测值",
        type: "line",
        color: "#16a34a",
        z: 3,
        data: [...Array(hist.length).fill(null), ...forecast.map((p) => Number(p.predicted_power.toFixed(1)))],
      },
    ],
  };

  const imp = (lab?.forecast.feature_importance || []).slice(0, 10);
  const importanceOption = {
    tooltip: { trigger: "axis" },
    grid: { left: 110, right: 24, top: 16, bottom: 24 },
    xAxis: { type: "value" },
    yAxis: { type: "category", data: [...imp].reverse().map((r) => r.label), axisLabel: { fontSize: 11 } },
    series: [{ type: "bar", data: [...imp].reverse().map((r) => r.importance), itemStyle: { color: "#16a34a" } }],
  };

  return (
    <div>
      <h1 className="page-title">能耗预测</h1>
      <p className="page-sub">
        绿带是按 RMSE 画的误差，不是保证能落在里面。指标是 MAE、RMSE、MAPE、R²，不把 100 减 MAPE 写成准确率。
        <a style={{ marginLeft: 8 }} onClick={() => nav("/models")}>看模型数字</a>
      </p>
      <Radio.Group value={hours} onChange={(e) => setHours(e.target.value)} style={{ marginBottom: 16 }}>
        <Radio.Button value={6}>未来 6 小时</Radio.Button>
        <Radio.Button value={24}>未来 24 小时</Radio.Button>
      </Radio.Group>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={12} md={4}><Card loading={loading}><Statistic title="模型" value={data?.model_name || "--"} /></Card></Col>
        <Col xs={12} md={4}><Card loading={loading}><Statistic title="MAE" value={data?.metrics?.MAE ?? 0} precision={2} suffix="W" /></Card></Col>
        <Col xs={12} md={4}><Card loading={loading}><Statistic title="RMSE" value={rmse} precision={2} suffix="W" /></Card></Col>
        <Col xs={12} md={4}><Card loading={loading}><Statistic title="MAPE" value={data?.metrics?.MAPE ?? 0} precision={2} suffix="%" /></Card></Col>
        <Col xs={12} md={4}><Card loading={loading}><Statistic title="R²" value={data?.metrics?.R2 ?? 0} precision={4} /></Card></Col>
        <Col xs={12} md={4}><Card loading={loading}><Statistic title="样本" value={lab?.forecast.samples ?? 0} /></Card></Col>
      </Row>
      <div className="honesty-note">{lab?.forecast.honesty || "指标来自 models/metrics.json，不编造。"}</div>
      <ChartCard title="历史真实值 + 预测 + RMSE 置信区间" loading={loading} empty={!forecast.length} option={option} height={420} />
      <div style={{ height: 16 }} />
      <ChartCard title="特征重要性（不含室外天气）" loading={loading} empty={!imp.length} option={importanceOption} height={320} />
    </div>
  );
}
