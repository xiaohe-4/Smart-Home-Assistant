import { useEffect, useState } from "react";
import { Button, Card, Col, Progress, Row, Slider, Switch, Tag } from "antd";
import { useNavigate } from "react-router-dom";
import { lifeApi } from "../api";
import ChartCard from "../components/ChartCard";
import DemandBanner from "../components/DemandBanner";
import PriceClock from "../components/PriceClock";
import TonightBoard from "../components/TonightBoard";
import { chartBase } from "../utils/chart";
import type { LifeOs } from "../types";

const NILM_COLORS = ["#16a34a", "#0ea5e9", "#f59e0b", "#e11d48", "#8b5cf6", "#14b8a6", "#64748b", "#84cc16"];
const COMFORT = [
  { mode: "eco", label: "省电 26℃" },
  { mode: "balanced", label: "均衡 25℃" },
  { mode: "comfort", label: "清凉 24℃" },
];

export default function Life() {
  const nav = useNavigate();
  const [data, setData] = useState<LifeOs | null>(null);
  const [loading, setLoading] = useState(true);
  const [degree, setDegree] = useState(26);

  const apply = (next: LifeOs) => {
    if (!next?.clock) return;
    setData(next);
    window.dispatchEvent(new Event("se-home-update"));
  };

  useEffect(() => {
    lifeApi.get().then(setData).finally(() => setLoading(false));
  }, []);

  const toggle = async (key: string, armed: boolean) => {
    apply(await lifeApi.toggleRule(key, armed));
  };

  const runMission = async (key: string) => {
    apply(await lifeApi.mission(key, true, true));
  };

  const nilm = {
    ...chartBase,
    tooltip: { trigger: "axis" },
    legend: { type: "scroll" },
    xAxis: { type: "category", data: data?.nilm.hours || [] },
    yAxis: { type: "value", name: "kWh" },
    series: (data?.nilm.series || []).map((s, i) => ({
      name: s.name,
      type: "bar",
      stack: "nilm",
      color: NILM_COLORS[i % NILM_COLORS.length],
      data: s.data,
    })),
  };

  const ledger = {
    ...chartBase,
    legend: { data: ["电费", "碳排"] },
    xAxis: { type: "category", data: (data?.ledger || []).map((d) => d.date.slice(5)) },
    yAxis: [
      { type: "value", name: "元" },
      { type: "value", name: "kg", splitLine: { show: false } },
    ],
    series: [
      { name: "电费", type: "bar", color: "#f59e0b", data: (data?.ledger || []).map((d) => d.cost) },
      { name: "碳排", type: "line", yAxisIndex: 1, color: "#16a34a", data: (data?.ledger || []).map((d) => d.carbon) },
    ],
  };

  const shiftOpt = {
    ...chartBase,
    tooltip: { trigger: "axis" },
    legend: { data: ["高峰实测", "可迁到谷电"] },
    xAxis: { type: "category", data: (data?.shift.items || []).map((d) => d.name) },
    yAxis: { type: "value", name: "kWh" },
    series: [
      { name: "高峰实测", type: "bar", color: "#f59e0b", data: (data?.shift.items || []).map((d) => d.peak_kwh) },
      { name: "可迁到谷电", type: "bar", color: "#16a34a", data: (data?.shift.items || []).map((d) => d.movable_kwh) },
    ],
  };

  const tomorrowOpt = {
    ...chartBase,
    xAxis: { type: "category", data: (data?.tomorrow.points || []).map((d) => d.label) },
    yAxis: { type: "value", name: "W" },
    series: [{ name: "预测功率", type: "line", smooth: true, color: "#0ea5e9", data: (data?.tomorrow.points || []).map((d) => d.w) }],
  };

  const save = Number((data?.whatif.per_degree_kwh || 0) * (degree - 24)).toFixed(2);
  const noticeNav: Record<string, string> = {
    去执行节能: "/strategy",
    查看异常: "/anomaly",
    查看规则: "/life",
    叫管家: "/butler",
    打开管家: "/butler",
    应邀约: "/life",
  };

  return (
    <div>
      <h1 className="page-title">今天的安排</h1>
      <p className="page-sub">电价、今晚要办的事、电网邀约，按这户 30 天的数来。邀约里的奖励是示意，不是已经到账。</p>
      {data ? <PriceClock clock={data.clock} /> : null}
      {data?.demand ? (
        <DemandBanner
          demand={data.demand}
          onAccept={() => void lifeApi.demand("accept").then(apply)}
          onDecline={() => void lifeApi.demand("decline").then(apply)}
        />
      ) : null}

      <div className="notice-row">
        {(data?.notices || []).map((n) => (
          <button key={n.title} className={`notice-card ${n.level}`} onClick={() => nav(noticeNav[n.action] || "/life")}>
            <b>{n.title}</b>
            <div>{n.detail}</div>
          </button>
        ))}
      </div>

      <Card title="今晚要办的" extra={data ? `在家 ${data.occupancy} 人 · 高峰占比 ${data.tou?.peak_share ?? "--"}%` : null} style={{ marginBottom: 16 }} loading={loading}>
        {data ? <TonightBoard missions={data.missions} challenge={data.challenge} onRun={(key) => void runMission(key)} /> : null}
      </Card>

      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={24} md={8}>
          <Card loading={loading} title="近 30 日电费节奏">
            <div className="kpi-value">{data?.budget.month_cost ?? 0} <span className="kpi-suffix">元</span></div>
            <Progress percent={Math.min(100, data?.budget.pace_percent ?? 0)} strokeColor="#16a34a" />
            <div className="kpi-hint">近 7 日外推 {data?.budget.expected_cost ?? 0} 元 · {data?.budget.label}</div>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card loading={loading} title="天气、空调与舒适模式">
            <div>{data?.weather.advice}</div>
            <div style={{ marginTop: 12 }}>如果设到 {degree}℃，约再省 {save} kWh</div>
            <Slider min={24} max={28} value={degree} onChange={setDegree} marks={{ 24: "24", 26: "26", 28: "28" }} />
            <div className="kpi-hint">{data?.whatif.note}</div>
            <div style={{ margin: "8px 0" }}>
              {COMFORT.map((c) => (
                <Button
                  key={c.mode}
                  size="small"
                  type={data?.comfort.mode === c.mode ? "primary" : "default"}
                  style={{ marginRight: 6 }}
                  onClick={() => void lifeApi.comfort(c.mode, true).then(apply)}
                >
                  {c.label}
                </Button>
              ))}
            </div>
            <Button type="primary" size="small" onClick={() => { sessionStorage.setItem("se-butler-cmd", `把空调调到${degree}度`); nav("/butler"); }}>让宝强去拧</Button>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card loading={loading} title="节能勋章">
            <div className="badge-grid">
              {(data?.badges || []).map((b) => (
                <div key={b.id} className={`badge ${b.earned ? "on" : ""}`}>
                  <b>{b.earned ? "已点亮" : "未点亮"} · {b.title}</b>
                  <div>{b.how}</div>
                </div>
              ))}
            </div>
          </Card>
        </Col>
      </Row>

      <div className="two-col">
        <ChartCard title="高峰→谷电可迁移负荷" extra={data ? `约能少花 ${data.shift.saving_yuan} 元` : null} loading={loading} empty={!data?.shift.items.length} option={shiftOpt} height={280} />
        <Card title="谷电预约轨道" extra="23:00 电价 0.28 元">
          <div className="schedule-rail">
            <span>20:30 高峰</span>
            <span>22:00 平时</span>
            <span>23:00 谷电</span>
            <span>07:00 结束</span>
          </div>
          {(data?.schedule || []).map((s) => (
            <div key={s.key} className={`rule-row ${s.booked ? "fire" : ""}`}>
              <div>
                <b>{s.title}</b> {s.booked ? <Tag color="green">已约 {s.slot}</Tag> : <Tag>{s.slot} {s.period}</Tag>}
                <div className="kpi-hint">{s.hint} · 约 {s.saving_kwh} kWh / {s.saving_yuan} 元</div>
              </div>
              <Switch checked={s.booked} onChange={(v) => void lifeApi.schedule(s.key, v).then(apply)} />
            </div>
          ))}
        </Card>
      </div>
      <div style={{ height: 16 }} />
      <div className="two-col">
        <Card title="凌晨待机猎手" extra={data ? `${data.standby.window} · ${data.standby.wasted_kwh} kWh` : null}>
          <div className="kpi-hint" style={{ marginBottom: 8 }}>{data?.standby.note}</div>
          {(data?.standby.items || []).map((h) => (
            <div key={h.device_type} className="health-row">
              <div>
                <b>{h.name}</b> <Tag color={h.level === "alert" ? "red" : "gold"}>{h.level}</Tag>
                <div className="kpi-hint">{h.kwh} kWh · {h.cost} 元</div>
                <div>{h.hint}</div>
              </div>
            </div>
          ))}
        </Card>
        <Card title="答辩一页纸" className="defense-wrap">
          <div className="defense-card">
            <div className="hero-kicker">智家能 · 演示日 2026-08-19</div>
            <h3>{data?.defense.headline}</h3>
            <div className="defense-facts">
              {(data?.defense.facts || []).map((f) => (
                <div key={f.label}>
                  <span>{f.label}</span>
                  <b>{f.value}</b>
                </div>
              ))}
            </div>
            <p>{data?.defense.family_top}</p>
            <p>{data?.defense.closing}</p>
          </div>
        </Card>
      </div>
      <div style={{ height: 16 }} />
      <ChartCard title="模型看到的接下来几小时" extra={data?.tomorrow.model || null} loading={loading} empty={!data?.tomorrow.points.length} option={tomorrowOpt} height={240} />
      <p className="kpi-hint" style={{ margin: "8px 0 16px" }}>{data?.tomorrow.advice}</p>

      <ChartCard title="今日负荷分解（按设备实测，不是猜的）" loading={loading} empty={!data?.nilm.series.length} option={nilm} height={340} />
      <div style={{ height: 16 }} />
      <Card title="行为归因分账" extra="没有每人一块表，按活动/房间把可分负荷拆开，剩余作公共分摊">
        <div className="family-grid">
          {(data?.family || []).map((p) => (
            <div key={p.name} className="family-card">
              <b>{p.name}</b>
              <div className="kpi-value" style={{ fontSize: 22 }}>{p.kwh} kWh</div>
              <Tag>{p.share}%</Tag>
              <div className="kpi-hint">{p.role} · 专属 {p.direct_kwh} · 分摊 {p.shared_kwh}</div>
              <div style={{ marginTop: 6 }}>{p.habit}</div>
            </div>
          ))}
        </div>
      </Card>
      <div style={{ height: 16 }} />
      <div className="two-col">
        <Card title="自动化规则" extra="打开后，总览和管家会按当前时段判断是否触发">
          {(data?.rules || []).map((r) => (
            <div key={r.key} className={`rule-row ${r.firing ? "fire" : ""}`}>
              <div>
                <b>{r.title}</b> {r.firing ? <Tag color="gold">正在触发</Tag> : null}
                <div className="kpi-hint">当 {r.when} → {r.then}</div>
              </div>
              <Switch checked={r.armed} onChange={(v) => void toggle(r.key, v)} />
            </div>
          ))}
        </Card>
        <Card title="设备健康">
          {(data?.health || []).map((h) => (
            <div key={h.id} className="health-row">
              <div>
                <b>{h.name}</b> <Tag color={h.level === "alert" ? "red" : h.level === "watch" ? "gold" : "green"}>{h.level}</Tag>
                <div className="kpi-hint">今日 {h.today_energy} kWh · 运行 {h.runtime_hours} h · {h.status}</div>
                <div>{h.hint}</div>
              </div>
            </div>
          ))}
        </Card>
      </div>
      <div style={{ height: 16 }} />
      <ChartCard title="近 7 日电费与碳账本" loading={loading} empty={!data?.ledger.length} option={ledger} height={280} />
    </div>
  );
}
