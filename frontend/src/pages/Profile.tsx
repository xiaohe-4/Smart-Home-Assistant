import { useEffect, useState } from "react";
import { Card, Col, Progress, Row, Statistic, Table, Typography } from "antd";
import { useNavigate } from "react-router-dom";
import { insightApi, modelsApi, profileApi } from "../api";
import ChartCard from "../components/ChartCard";
import type { InsightsPayload, ModelLab, ProfileData, SavingPotential } from "../types";
import { fulfilled } from "../utils/async";

export default function Profile() {
  const nav = useNavigate();
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [potential, setPotential] = useState<SavingPotential | null>(null);
  const [insights, setInsights] = useState<InsightsPayload | null>(null);
  const [lab, setLab] = useState<ModelLab | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.allSettled([profileApi.get(), profileApi.potential(), insightApi.get(), modelsApi.get()])
      .then(([p, s, i, m]) => {
        setProfile(fulfilled(p, null));
        setPotential(fulfilled(s, null));
        setInsights(fulfilled(i, null));
        setLab(fulfilled(m, null));
      })
      .finally(() => setLoading(false));
  }, []);

  const option = {
    tooltip: { trigger: "axis" },
    xAxis: { type: "category", data: (potential?.devices || []).map((d) => d.device_name) },
    yAxis: { type: "value", name: "kWh" },
    legend: { data: ["当前", "优化后"] },
    series: [
      { name: "当前", type: "bar", color: "#94a3b8", data: (potential?.devices || []).map((d) => d.baseline_kwh) },
      { name: "优化后", type: "bar", color: "#16a34a", data: (potential?.devices || []).map((d) => d.optimized_kwh) },
    ],
  };

  return (
    <div>
      <h1 className="page-title">这户概况</h1>
      <p className="page-sub">{profile ? `${profile.city} · ${profile.season} · ${profile.household_name}` : "加载中"}</p>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={24} md={8}>
          <Card loading={loading}>
            <Statistic title="能源效率" value={profile?.energy_score ?? 0} suffix="/100" />
            <Progress percent={profile?.energy_score ?? 0} strokeColor="#16a34a" />
          </Card>
        </Col>
        <Col xs={12} md={8}><Card loading={loading}><Statistic title="今日用电" value={profile?.today_energy ?? 0} precision={2} suffix="kWh" /></Card></Col>
        <Col xs={12} md={8}><Card loading={loading}><Statistic title="本月累计" value={profile?.month_energy ?? 0} precision={1} suffix="kWh" /></Card></Col>
      </Row>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={8}><Card><Statistic title="较昨日" value={profile?.compared_yesterday_percent ?? 0} precision={1} suffix="%" /></Card></Col>
        <Col span={8}><Card><Statistic title="今日电费" value={insights?.tou.total_cost ?? 0} precision={2} suffix="元" /></Card></Col>
        <Col span={8}><Card><Statistic title="今日碳排" value={insights?.carbon_kg ?? 0} precision={2} suffix="kg" /></Card></Col>
      </Row>
      <Card title="这户现在怎样" extra={<a onClick={() => nav("/models")}>模型实验</a>} style={{ marginBottom: 16 }}>
        <Typography.Paragraph>{insights?.assistant.summary}</Typography.Paragraph>
        {lab?.forecast.metrics?.R2 != null ? (
          <Typography.Paragraph type="secondary">
            预测 R² {lab.forecast.metrics.R2} · 负荷识别 {lab.load.accuracy}（有标签窗口，不是 NILM）· 异常 F1 {lab.anomaly.f1}
          </Typography.Paragraph>
        ) : null}
      </Card>
      <ChartCard title="分设备优化空间" loading={loading} empty={!potential?.devices.length} option={option} />
      <div style={{ height: 16 }} />
      <Card title="分设备节能潜力">
        <Table
          rowKey="device_type"
          dataSource={potential?.devices || []}
          pagination={false}
          columns={[
            { title: "设备", dataIndex: "device_name" },
            { title: "当前 (kWh)", dataIndex: "baseline_kwh" },
            { title: "优化后 (kWh)", dataIndex: "optimized_kwh" },
            { title: "潜在节约 (kWh)", dataIndex: "saving_kwh" },
            { title: "节约比例 (%)", dataIndex: "saving_percent" },
          ]}
        />
      </Card>
    </div>
  );
}
