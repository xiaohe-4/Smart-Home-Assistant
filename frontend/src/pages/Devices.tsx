import { useEffect, useState } from "react";
import { Button, Col, Progress, Row, Space, Tag } from "antd";
import { deviceApi, butlerApi } from "../api";
import ChartCard from "../components/ChartCard";
import { chartBase } from "../utils/chart";
import type { DeviceItem, EnergyPoint } from "../types";

export default function Devices() {
  const [devices, setDevices] = useState<DeviceItem[]>([]);
  const [selected, setSelected] = useState<DeviceItem | null>(null);
  const [series, setSeries] = useState<EnergyPoint[]>([]);
  const [loading, setLoading] = useState(true);

  const load = (keepId?: number) =>
    deviceApi.list().then((list) => {
      setDevices(list);
      const current = list.find((d) => d.id === keepId) || list[0] || null;
      setSelected(current);
      if (current) return deviceApi.energy(current.id).then(setSeries);
    });

  useEffect(() => {
    load().finally(() => setLoading(false));
    const refresh = () => void load(selected?.id);
    window.addEventListener("se-home-update", refresh);
    return () => window.removeEventListener("se-home-update", refresh);
  }, []);

  const control = async (text: string) => {
    await butlerApi.command(text);
    window.dispatchEvent(new Event("se-home-update"));
    await load(selected?.id);
  };

  const option = {
    ...chartBase,
    xAxis: { type: "category", data: series.map((p) => p.timestamp.slice(11, 16)) },
    yAxis: { type: "value", name: "W" },
    series: [{ type: "line", showSymbol: false, color: "#16a34a", areaStyle: { opacity: 0.12 }, data: series.map((p) => Number(p.power.toFixed(1))) }],
  };

  return (
    <div>
      <h1 className="page-title">家庭设备</h1>
      <p className="page-sub">每台设备都可以让管家宝强去关、去开、去调温。关闭是模拟执行，历史曲线仍保留今日实测。</p>
      <Row gutter={16}>
        <Col xs={24} lg={14}>
          <div className="device-grid">
            {devices.map((d) => (
              <div
                key={d.id}
                className={`device-tile ${selected?.id === d.id ? "active" : ""}`}
                onClick={() => { setSelected(d); deviceApi.energy(d.id).then(setSeries); }}
              >
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <b>{d.name}</b>
                  <Tag color={d.status === "运行" ? "green" : d.status === "关闭" ? "red" : "default"}>{d.status}</Tag>
                </div>
                <div style={{ margin: "10px 0 6px", fontSize: 22, fontWeight: 800 }}>{d.current_power} W</div>
                <div style={{ color: "#5f746a", fontSize: 12, marginBottom: 8 }}>今日 {d.today_energy} kWh · 运行 {d.runtime_hours} h</div>
                <Progress percent={d.share} size="small" strokeColor="#16a34a" />
                <Space style={{ marginTop: 8 }} onClick={(e) => e.stopPropagation()}>
                  <Button size="small" onClick={() => void control(`关闭${d.name}`)}>关闭</Button>
                  <Button size="small" onClick={() => void control(`打开${d.name}`)}>打开</Button>
                  {d.device_type === "air_conditioner" ? (
                    <Button size="small" onClick={() => void control("把空调调到26度")}>26℃</Button>
                  ) : null}
                </Space>
                {d.actuator_note ? <div className="explain-note">{d.actuator_note}</div> : null}
              </div>
            ))}
          </div>
        </Col>
        <Col xs={24} lg={10}>
          <ChartCard loading={loading} title={selected ? `${selected.name} 今日功率` : "设备功率"} empty={!series.length} option={option} />
        </Col>
      </Row>
    </div>
  );
}
