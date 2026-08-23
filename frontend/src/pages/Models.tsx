import { useEffect, useState } from "react";
import { Card, Col, Row, Statistic, Table, Tag, Typography } from "antd";
import { modelsApi } from "../api";
import ChartCard from "../components/ChartCard";
import { chartBase } from "../utils/chart";
import type { ModelLab } from "../types";

export default function Models() {
  const [lab, setLab] = useState<ModelLab | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    modelsApi.get().then(setLab).finally(() => setLoading(false));
  }, []);

  const fc = lab?.forecast;
  const load = lab?.load;
  const anom = lab?.anomaly;
  const st = lab?.strategy;
  const imp = fc?.feature_importance || [];
  const loadImp = load?.feature_importance || [];

  const forecastBar = {
    ...chartBase,
    tooltip: { trigger: "axis" },
    grid: { left: 120, right: 24, top: 16, bottom: 28 },
    xAxis: { type: "value", name: "重要性" },
    yAxis: { type: "category", data: [...imp].reverse().map((r) => r.label), axisLabel: { fontSize: 11 } },
    series: [{
      type: "bar",
      data: [...imp].reverse().map((r) => r.importance),
      itemStyle: { color: "#16a34a" },
    }],
  };

  const loadBar = {
    ...chartBase,
    tooltip: { trigger: "axis" },
    grid: { left: 110, right: 24, top: 16, bottom: 28 },
    xAxis: { type: "value" },
    yAxis: { type: "category", data: [...loadImp].reverse().map((r) => r.label) },
    series: [{ type: "bar", data: [...loadImp].reverse().map((r) => r.importance), itemStyle: { color: "#0d9488" } }],
  };

  const shareBar = {
    ...chartBase,
    xAxis: { type: "category", data: (st?.devices || []).map((d) => d.label) },
    yAxis: { type: "value", name: "%" },
    series: [{ type: "bar", data: (st?.devices || []).map((d) => d.share), itemStyle: { color: "#16a34a" } }],
  };

  return (
    <div>
      <h1 className="page-title">模型实验舱</h1>
      <p className="page-sub">只报 MAE / RMSE / MAPE / R²，并和昨天同时段、近 7 日同时段平均对照。异常 F1=0.35，上线以规则为准。</p>
      <div className="honesty-note">{lab?.honesty || "正在读取 models/metrics.json 与 joblib。"}</div>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={24} md={6}>
          <Card loading={loading}>
            <Statistic title="预测 R²" value={fc?.metrics?.R2 ?? 0} precision={4} />
            <div className="kpi-hint">{fc?.model_name} · MAPE {fc?.metrics?.MAPE ?? "--"}%</div>
          </Card>
        </Col>
        <Col xs={24} md={6}>
          <Card loading={loading}>
            <Statistic title="昨天同时段 MAPE" value={fc?.baselines?.yesterday?.MAPE ?? 0} precision={2} suffix="%" />
            <div className="kpi-hint">基线 A · 近 7 日同时段 {fc?.baselines?.weekmean?.MAPE ?? "--"}%</div>
          </Card>
        </Col>
        <Col xs={24} md={6}>
          <Card loading={loading}>
            <Statistic title="负荷识别 Accuracy" value={load?.accuracy ?? 0} precision={4} />
            <div className="kpi-hint">macro-F1 {load?.macro_f1 ?? "--"} · 有标签窗口分类</div>
          </Card>
        </Col>
        <Col xs={24} md={6}>
          <Card loading={loading}>
            <Statistic title="异常 F1" value={anom?.f1 ?? 0} precision={2} />
            <div className="kpi-hint">P {anom?.precision ?? "--"} / R {anom?.recall ?? "--"} · 标注 {anom?.labeled ?? "--"} / 检出 {anom?.detected ?? "--"}</div>
          </Card>
        </Col>
      </Row>

      <div className="two-col">
        <Card title="实验 1 · 能耗预测" extra={fc?.model_name}>
          <p className="honesty-note">{fc?.honesty}</p>
          <Row gutter={12}>
            <Col span={8}><Statistic title="MAE" value={fc?.metrics?.MAE ?? 0} precision={2} suffix="W" /></Col>
            <Col span={8}><Statistic title="RMSE" value={fc?.metrics?.RMSE ?? 0} precision={2} suffix="W" /></Col>
            <Col span={8}><Statistic title="样本" value={fc?.samples ?? 0} /></Col>
          </Row>
          <Typography.Paragraph type="secondary" style={{ marginTop: 12 }}>
            主特征 {fc?.features?.length || 0} 列。不在模型里：{(fc?.not_in_model || []).join("、") || "无"}。
          </Typography.Paragraph>
        </Card>
        <ChartCard title="XGBoost 特征重要性" loading={loading} empty={!imp.length} option={forecastBar} height={360} />
      </div>

      <div style={{ height: 16 }} />
      <div className="two-col">
        <Card title="实验 2 · 异常检测" extra="Isolation Forest + 规则">
          <p className="honesty-note">{anom?.honesty}</p>
          <Row gutter={12}>
            <Col span={8}><Statistic title="Precision" value={anom?.precision ?? 0} precision={4} /></Col>
            <Col span={8}><Statistic title="Recall" value={anom?.recall ?? 0} precision={4} /></Col>
            <Col span={8}><Statistic title="对照点数" value={anom?.labeled ?? 0} /></Col>
          </Row>
        </Card>
        <Card title="实验 3 · 负荷识别" extra={<Tag color="gold">不是总表 NILM</Tag>}>
          <p className="honesty-note">{load?.honesty}</p>
          <ChartCard title="窗口特征重要性" loading={loading} empty={!loadImp.length} option={loadBar} height={220} />
        </Card>
      </div>

      <div style={{ height: 16 }} />
      <Card title="负荷识别推理示例" extra={load?.live ? `抽检命中 ${load.live.hits}/${load.live.n}` : null} style={{ marginBottom: 16 }}>
        <p className="honesty-note">{load?.live?.note}</p>
        <Table
          size="small"
          rowKey="device_type"
          pagination={false}
          loading={loading}
          dataSource={load?.live?.samples || []}
          columns={[
            { title: "真实设备", dataIndex: "label" },
            { title: "模型输出", dataIndex: "pred_label" },
            { title: "起始小时", dataIndex: "start_hour" },
            { title: "窗内均功率", dataIndex: "mean_power" },
            {
              title: "命中",
              dataIndex: "hit",
              render: (v: boolean) => <Tag color={v ? "green" : "red"}>{v ? "是" : "否"}</Tag>,
            },
          ]}
        />
        {(load?.live?.confusions || []).length ? (
          <Typography.Paragraph type="secondary" style={{ marginTop: 12 }}>
            主要混淆：{load?.live?.confusions.map((c) => `${c.true}→${c.pred}（${c.count}）`).join("；")}
          </Typography.Paragraph>
        ) : null}
      </Card>

      <Card title="实验 4 · 今日负荷结构" extra={st?.top_strategy}>
        <p className="honesty-note">{st?.honesty}</p>
        <Statistic title="演示日用电" value={st?.today_energy ?? 0} precision={2} suffix="kWh" />
        <div style={{ height: 12 }} />
        <ChartCard title="分路电量占比（不是盲拆）" loading={loading} empty={!st?.devices.length} option={shareBar} height={260} />
      </Card>
    </div>
  );
}
