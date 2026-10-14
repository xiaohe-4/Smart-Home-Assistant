import { useEffect, useState } from "react";
import { Card, Col, Progress, Row, Statistic, Table, Tag } from "antd";
import { useNavigate } from "react-router-dom";
import { anomalyApi, modelsApi } from "../api";
import ChartCard from "../components/ChartCard";
import { anomalyTypeLabel, severityColor } from "../utils/format";
import type { AnomalyItem, ModelLab } from "../types";

export default function Anomaly() {
  const nav = useNavigate();
  const [rows, setRows] = useState<AnomalyItem[]>([]);
  const [lab, setLab] = useState<ModelLab | null>(null);
  const [loading, setLoading] = useState(true);
  const [picked, setPicked] = useState<AnomalyItem | null>(null);

  useEffect(() => {
    Promise.allSettled([anomalyApi.list(), modelsApi.get()]).then(([list, models]) => {
      if (list.status === "fulfilled") {
        setRows(list.value);
        const night = list.value.find((r) => r.anomaly_type === "unusual_time") || list.value[0];
        setPicked(night || null);
      }
      if (models.status === "fulfilled") setLab(models.value);
    }).finally(() => setLoading(false));
  }, []);

  const option = {
    tooltip: { trigger: "item" },
    xAxis: { type: "value", name: "小时", min: 0, max: 24 },
    yAxis: { type: "value", name: "异常分" },
    series: [{
      type: "scatter",
      symbolSize: (v: number[]) => 8 + v[1] * 18,
      data: rows.map((r) => ({
        value: [new Date(r.timestamp).getHours() + new Date(r.timestamp).getMinutes() / 60, r.anomaly_score],
        name: r.device_name,
        itemStyle: { color: r.severity === "medium" || r.severity === "high" ? "#f97316" : "#16a34a" },
      })),
      markLine: {
        data: [{ xAxis: 3.25, label: { formatter: "03:17 热水器" } }],
        lineStyle: { color: "#e11d48" },
      },
    }],
  };

  const night = rows.filter((r) => new Date(r.timestamp).getHours() < 6).length;
  const anom = lab?.anomaly;

  return (
    <div>
      <h1 className="page-title">异常</h1>
      <p className="page-sub">
        凌晨用水、没人还在耗电、灯一直亮，按这几条规则判。模型只给一个分，F1 是 0.35，所以以规则为准。
        <a style={{ marginLeft: 8 }} onClick={() => nav("/models")}>看模型数字</a>
      </p>
      <div className="honesty-note">{anom?.honesty}</div>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={12} md={4}><Card loading={loading}><Statistic title="异常事件" value={rows.length} /></Card></Col>
        <Col xs={12} md={4}><Card loading={loading}><Statistic title="凌晨事件" value={night} /></Card></Col>
        <Col xs={12} md={4}><Card loading={loading}><Statistic title="Precision" value={anom?.precision ?? 0} precision={4} /></Card></Col>
        <Col xs={12} md={4}><Card loading={loading}><Statistic title="Recall" value={anom?.recall ?? 0} precision={4} /></Card></Col>
        <Col xs={12} md={4}><Card loading={loading}><Statistic title="F1" value={anom?.f1 ?? 0} precision={2} /></Card></Col>
        <Col xs={12} md={4}><Card loading={loading}><Statistic title="标注/检出" value={`${anom?.labeled ?? "--"} / ${anom?.detected ?? "--"}`} /></Card></Col>
      </Row>
      <div className="two-col">
        <ChartCard title="异常时空分布" loading={loading} empty={!rows.length} option={option} height={320} />
        <Card title={picked ? `${picked.timestamp.slice(11, 16)} ${picked.device_name || "家庭负荷"}` : "规则归因"} loading={loading}>
          <p>{picked?.description}</p>
          {(picked?.explain || []).map((item) => (
            <div key={item.feature} className="explain-row">
              <div className="explain-top">
                <b>{item.feature}</b>
                <span>{Math.round(item.weight * 100)}%</span>
              </div>
              <Progress percent={Math.round(item.weight * 100)} showInfo={false} strokeColor="#16a34a" />
              <div className="explain-note">{item.note}</div>
            </div>
          ))}
        </Card>
      </div>
      <div style={{ height: 16 }} />
      <Card>
        <Table
          loading={loading}
          rowKey="id"
          dataSource={rows}
          pagination={{ pageSize: 8 }}
          onRow={(record) => ({ onClick: () => setPicked(record) })}
          rowClassName={(record) => (picked?.id === record.id ? "picked-row" : "")}
          columns={[
            { title: "时间", dataIndex: "timestamp", width: 180 },
            { title: "设备", dataIndex: "device_name", render: (v: string) => v || "家庭负荷" },
            { title: "异常类型", dataIndex: "anomaly_type", render: (v: string) => anomalyTypeLabel(v) },
            { title: "严重程度", dataIndex: "severity", render: (v: string) => <Tag color={severityColor(v)}>{v}</Tag> },
            { title: "评分", dataIndex: "anomaly_score", render: (v: number) => v.toFixed(3) },
            { title: "建议", dataIndex: "description" },
          ]}
        />
      </Card>
    </div>
  );
}
