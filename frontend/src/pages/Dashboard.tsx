import { useEffect, useMemo, useState } from "react";
import { Card, List, Tag, Typography } from "antd";
import { ThunderboltOutlined, DashboardOutlined, AlertOutlined, CloudOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { anomalyApi, insightApi, lifeApi, predictionApi, sourceApi } from "../api";
import { fulfilled } from "../utils/async";
import ChartCard from "../components/ChartCard";
import DemandBanner from "../components/DemandBanner";
import FloorPlan from "../components/FloorPlan";
import HighlightBar from "../components/HighlightBar";
import KpiCard from "../components/KpiCard";
import ModalityStrip from "../components/ModalityStrip";
import PriceClock from "../components/PriceClock";
import TimeScrubber from "../components/TimeScrubber";
import TonightBoard from "../components/TonightBoard";
import { chartBase } from "../utils/chart";
import { anomalyTypeLabel, severityColor } from "../utils/format";
import type { AnomalyItem, InsightsPayload, LifeOs, PredictionResult, SourceMap } from "../types";

const COMMANDS = [
  { q: "为什么我家耗电？", path: "/assistant" },
  { q: "03:17 发生了什么？", path: "/anomaly" },
  { q: "叫宝强去执行节能", path: "/butler" },
  { q: "现在是不是高峰？", path: "/life" },
  { q: "应下电网削峰邀约", path: "/life" },
  { q: "数据从哪来？", path: "/sources" },
  { q: "预测准不准？", path: "/models" },
  { q: "怎么用这套系统？", path: "/guide" },
];

export default function Dashboard() {
  const nav = useNavigate();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<InsightsPayload | null>(null);
  const [pred, setPred] = useState<PredictionResult | null>(null);
  const [anomalies, setAnomalies] = useState<AnomalyItem[]>([]);
  const [life, setLife] = useState<LifeOs | null>(null);
  const [sources, setSources] = useState<SourceMap | null>(null);
  const [hour, setHour] = useState(20);

  useEffect(() => {
    Promise.allSettled([insightApi.get(), predictionApi.day(6), anomalyApi.latest(), lifeApi.get(), sourceApi.get()])
      .then(([insights, pr, a, lf, src]) => {
        setData(fulfilled(insights, null));
        setPred(fulfilled(pr, null));
        setAnomalies(fulfilled(a, []));
        setLife(fulfilled(lf, null));
        setSources(fulfilled(src, null));
      })
      .finally(() => setLoading(false));
  }, []);

  const timeline = data?.timeline || [];
  const showcase = data?.showcase;
  const replay = showcase?.replay || [];
  const now = replay.find((f) => f.hour === hour) || replay.find((f) => f.hour === 20);
  const optByHour = useMemo(() => {
    const map: Record<number, number> = {};
    replay.forEach((p) => {
      if (p.optimized_power != null) map[p.hour] = p.optimized_power;
    });
    (showcase?.optimized_curve || []).forEach((p) => {
      map[p.hour] = p.optimized;
    });
    return map;
  }, [showcase?.optimized_curve, replay]);

  const lineOption = {
    ...chartBase,
    legend: { data: ["家庭功率", "优化后功率", "占用人数"] },
    xAxis: { type: "category", data: timeline.map((p) => p.timestamp.slice(11, 16)), boundaryGap: false },
    yAxis: [
      { type: "value", name: "W" },
      { type: "value", name: "人", min: 0, max: 4, splitLine: { show: false } },
    ],
    series: [
      {
        name: "家庭功率",
        type: "line",
        smooth: true,
        showSymbol: false,
        areaStyle: { opacity: 0.16 },
        color: "#16a34a",
        markArea: {
          silent: true,
          data: [[{ xAxis: "18:00", itemStyle: { color: "rgba(245,158,11,0.08)" } }, { xAxis: "22:00" }]],
        },
        markLine: {
          symbol: "none",
          label: { formatter: now?.label || "" },
          data: [{ xAxis: `${String(hour).padStart(2, "0")}:00` }],
        },
        data: timeline.map((p) => p.power),
      },
      {
        name: "优化后功率",
        type: "line",
        smooth: true,
        showSymbol: false,
        color: "#0ea5e9",
        lineStyle: { type: "dashed" },
        data: timeline.map((p) => {
          const h = Number(p.timestamp.slice(11, 13));
          return optByHour[h] ?? p.power;
        }),
      },
      {
        name: "占用人数",
        type: "line",
        yAxisIndex: 1,
        smooth: true,
        showSymbol: false,
        color: "#94a3b8",
        data: timeline.map((p) => p.occupancy),
      },
    ],
  };

  const sankeyOption = {
    tooltip: { trigger: "item" },
    series: [{
      type: "sankey",
      emphasis: { focus: "adjacency" },
      lineStyle: { color: "gradient", curveness: 0.5 },
      data: [
        { name: "电网" },
        ...((showcase?.sankey.links || []).map((l) => ({ name: l.target }))),
      ],
      links: showcase?.sankey.links || [],
    }],
  };

  const predOption = {
    ...chartBase,
    xAxis: {
      type: "category",
      data: [
        ...(pred?.history || []).slice(-12).map((p) => p.timestamp.slice(11, 16)),
        ...(pred?.forecast || []).map((p) => p.timestamp.slice(11, 16)),
      ],
    },
    yAxis: { type: "value", name: "W" },
    series: [
      {
        name: "历史",
        type: "line",
        color: "#94a3b8",
        data: [...(pred?.history || []).slice(-12).map((p) => p.actual_power), ...Array(pred?.forecast.length || 0).fill(null)],
      },
      {
        name: "预测",
        type: "line",
        color: "#16a34a",
        data: [...Array(Math.min(12, pred?.history.length || 0)).fill(null), ...(pred?.forecast || []).map((p) => Number(p.predicted_power.toFixed(1)))],
      },
    ],
  };

  const bench = showcase?.benchmark;
  const ask = (q: string, path: string) => {
    if (path === "/butler") sessionStorage.setItem("se-butler-cmd", "执行今晚节能方案");
    else if (path !== "/models" && path !== "/guide") sessionStorage.setItem("se-ask", q);
    nav(path);
  };

  return (
    <div className="page-shell">
      <div className="hero-banner">
        <div className="hero-copy-wrap">
          <div className="hero-kicker">智家能 · 今晚该关什么</div>
          <h1 className="hero-title">给家庭一张「该关什么」的执行单</h1>
          <p className="hero-copy">电表只告诉你这个月多少度。这里回答：为什么贵、哪笔是浪费、今晚关哪一档。</p>
          <div className="hero-actions">
            <button className="tonight-cta" onClick={() => { sessionStorage.setItem("se-autosim", "1"); nav("/strategy"); window.dispatchEvent(new Event("se-autosim")); }}>今晚怎么做</button>
            <button className="hero-ghost" onClick={() => nav("/anomaly")}>看 03:17 异常</button>
          </div>
        </div>
        <div className="hero-stats">
          <div className="hero-stat">
            <span>今日用电</span>
            <b>{(now?.energy_so_far ?? data?.stats.today_energy ?? 0).toFixed(2)}<em>kWh</em></b>
          </div>
          <div className="hero-stat">
            <span>截至此时电费</span>
            <b>{now?.cost_so_far ?? data?.tou.total_cost ?? 0}<em>元</em></b>
          </div>
          <div className="hero-stat">
            <span>第一耗电设备</span>
            <b className="hero-device">{data?.stats.main_device || "空调"}<em>{data?.stats.main_device_share ?? 0}%</em></b>
          </div>
        </div>
      </div>

      {now?.alert ? (
        <div className="alert-strip">检测到 {now.label} 异常窗口：热水器非常规启动，可到异常页查看规则归因。</div>
      ) : null}

      <div className="replay-block">
        <ChartCard title="今日功率 · 实际 / 优化 / 占用" loading={loading} empty={!timeline.length} option={lineOption} height={300} extra="橙色带是高峰" />
        <Card className="scrubber-card">
          <TimeScrubber frames={replay} hour={hour} onChange={setHour} />
        </Card>
      </div>

      <div className="kpi-row">
        <KpiCard label="能源评分" value={data?.energy_score.energy_score ?? 0} suffix="/100" hint={`节能潜力 ${data?.saving_potential ?? 0}%`} tone="cyan" icon={<DashboardOutlined />} />
        <KpiCard label="当前功率" value={((now?.power ?? data?.twin.current_power ?? 0) / 1000).toFixed(2)} suffix="kW" hint={`${now?.occupancy ?? data?.twin.occupancy ?? 0} 人在家 · ${now?.temperature ?? data?.twin.indoor_temp ?? "--"}℃`} tone="rose" icon={<AlertOutlined />} />
        <KpiCard label="夜间用电" value={showcase?.equivalents.night_kwh ?? 0} suffix="kWh" hint={`低占用浪费 ${showcase?.equivalents.away_kwh ?? 0} kWh`} icon={<ThunderboltOutlined />} />
        <KpiCard label="近 30 日对标" value={bench?.percentile ?? "--"} suffix={bench ? "百分位" : ""} hint={bench ? `今日 ${bench.today_kwh} kWh ${bench.label}` : `碳排 ${showcase?.equivalents.tree_days ?? 0} 棵树·日`} tone="gold" icon={<CloudOutlined />} />
      </div>

      {life ? <PriceClock clock={life.clock} /> : null}
      {life?.demand ? (
        <DemandBanner
          demand={life.demand}
          onAccept={() => void lifeApi.demand("accept").then((lf) => { setLife(lf); window.dispatchEvent(new Event("se-home-update")); })}
          onDecline={() => void lifeApi.demand("decline").then(setLife)}
        />
      ) : null}
      {sources ? <ModalityStrip items={sources.modalities} percent={sources.alignment.percent} /> : null}
      <HighlightBar items={showcase?.highlights || []} />

      <div className="command-row">
        {COMMANDS.map((item) => (
          <button key={item.q} className="command-chip" onClick={() => ask(item.q, item.path)}>{item.q}</button>
        ))}
      </div>

      {life ? (
        <Card title="今晚作战计划" extra={<a onClick={() => nav("/life")}>打开生活系统</a>} style={{ marginBottom: 16 }}>
          <TonightBoard
            compact
            missions={life.missions || []}
            challenge={life.challenge}
            onRun={(key) => void lifeApi.mission(key, true, true).then((lf) => { setLife(lf); window.dispatchEvent(new Event("se-home-update")); })}
          />
        </Card>
      ) : null}

      <div style={{ height: 16 }} />
      <div className="two-col">
        <Card title="家庭空间孪生" extra={<span className="live-pill">{now?.location || data?.twin.location} · {now?.activity || data?.twin.activity}</span>}>
          <FloorPlan rooms={showcase?.rooms || []} location={now?.location || data?.twin.location} />
        </Card>
        <ChartCard title="今日能量流向" loading={loading} empty={!showcase?.sankey.links.length} option={sankeyOption} height={360} />
      </div>

      <div style={{ height: 16 }} />
      <Card title="智能调度清单" extra="按峰谷电价与占用实时生成">
        <div className="dispatch-grid">
          {(showcase?.dispatch || []).map((item) => (
            <div key={item.label} className={`dispatch-item ${item.hour === hour ? "now" : ""}`}>
              <b>{item.label}</b>
              <div>{item.action}</div>
              <span>{item.reason}</span>
            </div>
          ))}
        </div>
      </Card>
      <div style={{ height: 16 }} />
      <Card title="今日能源叙事">
        <div className="story-line">
          {(showcase?.story || []).map((item) => (
            <div key={item.time} className="story-node">
              <div className="story-time">{item.time}</div>
              <div className="story-title">{item.title}</div>
              <div className="story-detail">{item.detail}</div>
            </div>
          ))}
        </div>
      </Card>

      <div style={{ height: 16 }} />
      <div className="two-col">
        <ChartCard title="未来 6 小时预测" extra={pred?.metrics?.MAPE ? `MAPE ${pred.metrics.MAPE}%` : null} loading={loading} empty={!pred?.forecast?.length} option={predOption} />
        <Card title="AI 决策简报" extra={<a onClick={() => nav("/assistant")}>打开助手</a>}>
          <Typography.Paragraph className="assistant-bubble">{now?.brief || data?.assistant.summary || "正在生成解读..."}</Typography.Paragraph>
          <List
            loading={loading}
            dataSource={data?.insights || []}
            renderItem={(item) => (
              <List.Item>
                <List.Item.Meta
                  title={<span>{item.title} <Tag color={item.level === "alert" ? "red" : item.level === "warn" ? "gold" : "green"}>{item.level}</Tag></span>}
                  description={item.detail}
                />
              </List.Item>
            )}
          />
        </Card>
      </div>

      <div style={{ height: 16 }} />
      <div className="two-col">
        <Card title="最新异常">
          <List
            loading={loading}
            dataSource={anomalies}
            locale={{ emptyText: "暂无异常" }}
            renderItem={(item) => (
              <List.Item>
                <List.Item.Meta
                  title={<span>{item.timestamp.slice(11, 16)} {item.device_name} <Tag color={severityColor(item.severity)}>{anomalyTypeLabel(item.anomaly_type)}</Tag></span>}
                  description={item.description}
                />
              </List.Item>
            )}
          />
        </Card>
        <Card title="Top 节能策略" extra={<a onClick={() => nav("/strategy")}>去模拟</a>}>
          <List
            dataSource={data?.top_strategies || []}
            renderItem={(item, idx) => (
              <List.Item>
                <List.Item.Meta
                  title={`${idx + 1}. ${item.title}`}
                  description={`预计节约 ${item.estimated_saving_percent.toFixed(1)}% · 舒适度 ${item.comfort_impact}`}
                />
              </List.Item>
            )}
          />
        </Card>
      </div>
    </div>
  );
}
