import { useEffect, useMemo, useState } from "react";
import { Button, Card, Checkbox, Col, Input, Row, Tag } from "antd";
import { sourceApi } from "../api";
import ModalityStrip from "../components/ModalityStrip";
import type { SourceDegrade, SourceMap, SourceValidate } from "../types";

const SAMPLE: Record<string, Record<string, unknown>[]> = {
  energy: [{ timestamp: "2026-08-19 20:30:00", device_id: 1, power: 620, energy: 0.0517, voltage: 221, current: 2.8 }],
  environment: [{ timestamp: "2026-08-19 20:30:00", temperature: 27.4, humidity: 61, light: 180, co2: 980 }],
  behavior: [{ timestamp: "2026-08-19 20:30:00", occupancy: 4, location: "客厅", activity: "watching_tv" }],
  weather: [{ timestamp: "2026-08-19 20:30:00", temperature: 31.2, humidity: 58, weather: "晴热", wind_speed: 2.1 }],
};

export default function Sources() {
  const [data, setData] = useState<SourceMap | null>(null);
  const [drop, setDrop] = useState<string[]>([]);
  const [degrade, setDegrade] = useState<SourceDegrade | null>(null);
  const [modality, setModality] = useState("energy");
  const [jsonText, setJsonText] = useState(JSON.stringify(SAMPLE.energy, null, 2));
  const [result, setResult] = useState<SourceValidate | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    sourceApi.get().then(setData).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    sourceApi.degrade(drop).then(setDegrade);
  }, [drop]);

  const runValidate = async () => {
    let rows: Record<string, unknown>[] = [];
    try {
      const parsed = JSON.parse(jsonText);
      rows = Array.isArray(parsed) ? parsed : [parsed];
    } catch {
      setResult({ ok: false, detail: "JSON 无法解析", errors: [{ row: 0, field: "rows", error: "不是合法 JSON" }] });
      return;
    }
    setResult(await sourceApi.validate(modality, rows));
  };

  const options = useMemo(
    () => (data?.modalities || []).map((m) => ({ label: m.label, value: m.key })),
    [data],
  );

  const compare = data?.compare;

  return (
    <div>
      <h1 className="page-title">两套家庭对照</h1>
      <p className="page-sub">{data?.honesty}</p>
      <div className="honesty-note">{compare?.note || "当前是演示数据。另一套用来对照真实电表或公开数据。"}</div>
      {compare?.boundary?.length ? (
        <p className="page-sub">要注意：{compare.boundary.join(" ")}</p>
      ) : null}
      <Card title="对照表" style={{ margin: "12px 0 16px" }} loading={loading}>
        <table className="compare-table">
          <thead>
            <tr><th>项目</th><th>演示家庭</th><th>对照家庭</th></tr>
          </thead>
          <tbody>
            {(compare?.rows || []).map((row) => (
              <tr key={row.item}>
                <td>{row.item}</td>
                <td>{row.demo}</td>
                <td>{row.real}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
      {data?.load_identification_applicable === false ? (
        <div className="honesty-note">这一户只有总功率和插座分路，分不出具体家电，负荷识别用不上。</div>
      ) : null}
      {data ? <ModalityStrip items={data.modalities} percent={data.alignment.percent} clickable={false} /> : null}

      <Row gutter={16} style={{ margin: "16px 0" }}>
        <Col xs={24} md={8}>
          <Card loading={loading} title="当前家庭合同">
            <div className="kpi-value" style={{ fontSize: 22 }}>{data?.household.name}</div>
            <div className="kpi-hint">{data?.city} · {data?.season} · {data?.household.size} 人 · {data?.household.home_type}</div>
            <div style={{ marginTop: 8 }}>
              电价 峰 {data?.tariff.peak} / 平 {data?.tariff.flat} / 谷 {data?.tariff.valley} 元 · 每度电碳排放 {data?.tariff.carbon} kg
            </div>
            <Tag style={{ marginTop: 8 }}>{data?.mode === "demo" ? "演示：只检查，不保存" : "可以写入数据库"}</Tag>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card loading={loading} title="演示日对齐">
            <div className="kpi-value">{data?.alignment.percent ?? 0}<span className="kpi-suffix">%</span></div>
            <div className="kpi-hint">
              {data?.alignment.date} · {data?.alignment.interval_minutes} 分钟一点 · 四路同时有点 {data?.alignment.aligned}/{data?.alignment.points}
            </div>
            <div style={{ marginTop: 8 }}>{data?.alignment.note}</div>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card loading={loading} title="预测用到的特征">
            <div className="feature-chips">
              {(data?.forecast_features || []).map((f) => (
                <span key={f} className={`feature-chip ${degrade?.lost_features?.includes(f) ? "lost" : ""}`}>{f}</span>
              ))}
            </div>
            <div className="kpi-hint" style={{ marginTop: 8 }}>室外天气不参与预测。没有「人在不在家」时，相关规则会放宽，页面不会因此报错。</div>
          </Card>
        </Col>
      </Row>

      <div className="family-grid" style={{ marginBottom: 16 }}>
        {(data?.modalities || []).map((m) => (
          <div key={m.key} className="family-card">
            <b>{m.label}</b> <Tag color={m.active ? "green" : "default"}>{m.table}</Tag>
            <div className="kpi-hint">{m.rows.toLocaleString()} 行 · {m.start} → {m.end}</div>
            <div style={{ margin: "8px 0" }}>真实接入：{m.hardware}</div>
            <div className="kpi-hint">必填 {m.required.join("、")} · 用于 {m.used_by.join("、")}</div>
            <div style={{ marginTop: 8 }}>{m.note}</div>
          </div>
        ))}
      </div>

      <div className="two-col">
        <Card title="缺一路会怎样" extra="对照同一日数据，不改数据库">
          <Checkbox.Group options={options} value={drop} onChange={(v) => setDrop(v as string[])} />
          <div className="degrade-compare">
            <div>
              <b>现在</b>
              <div>功率和室温 {degrade?.before.power_vs_temperature ?? "--"}</div>
              <div>功率和在家人数 {degrade?.before.power_vs_occupancy ?? "--"}</div>
              <div>功率和室外温度 {degrade?.before.power_vs_outdoor ?? "--"}</div>
            </div>
            <div>
              <b>去掉后</b>
              <div>功率和室温 {degrade?.after.power_vs_temperature ?? "--"}</div>
              <div>功率和在家人数 {degrade?.after.power_vs_occupancy ?? "--"}</div>
              <div>功率和室外温度 {degrade?.after.power_vs_outdoor ?? "--"}</div>
            </div>
          </div>
          {(degrade?.broken || []).map((line) => (
            <div key={line} className="kpi-hint" style={{ marginTop: 6 }}>{line}</div>
          ))}
          <div className="kpi-hint" style={{ marginTop: 8 }}>{degrade?.note}</div>
        </Card>
        <Card title="换一户要做的三步">
          {(data?.portability || []).map((p) => (
            <div key={p.step} className="rule-row">
              <div>
                <b>{p.step}. {p.title}</b>
                <div className="kpi-hint">{p.detail}</div>
              </div>
            </div>
          ))}
          {(data?.limits || []).map((line) => (
            <div key={line} className="kpi-hint">{line}</div>
          ))}
        </Card>
      </div>
      <div style={{ height: 16 }} />
      <div className="two-col">
        <Card title="采集适配器">
          {(data?.adapters || []).map((a) => (
            <div key={a.id} className="health-row">
              <div>
                <b>{a.label}</b> <Tag color={a.active ? "green" : "blue"}>{a.active ? "正在用" : a.status}</Tag>
                <div className="kpi-hint">{a.how}</div>
              </div>
            </div>
          ))}
        </Card>
        <Card title="接入数据校验" extra="演示只检查字段，不写入数据库">
          <div style={{ marginBottom: 8 }}>
            {Object.keys(SAMPLE).map((key) => (
              <Button
                key={key}
                size="small"
                type={modality === key ? "primary" : "default"}
                style={{ marginRight: 6 }}
                onClick={() => {
                  setModality(key);
                  setJsonText(JSON.stringify(SAMPLE[key], null, 2));
                  setResult(null);
                }}
              >
                {key}
              </Button>
            ))}
          </div>
          <Input.TextArea value={jsonText} onChange={(e) => setJsonText(e.target.value)} rows={8} />
          <Button type="primary" style={{ marginTop: 8 }} onClick={() => void runValidate()}>校验这条记录</Button>
          {result ? (
            <div className={`ingest-result ${result.ok ? "ok" : "bad"}`}>
              {result.ok ? `通过 · ${result.rows} 行 · 演示模式不会写入` : result.detail || "未通过"}
              {(result.errors || []).map((e) => (
                <div key={`${e.row}-${e.field}`}>{e.field}: {e.error}</div>
              ))}
              <div className="kpi-hint">{result.note}</div>
            </div>
          ) : null}
        </Card>
      </div>
      <div style={{ height: 16 }} />
      <Card title="当前设备清单（移植时按户替换）">
        <div className="feature-chips">
          {(data?.devices || []).map((d) => (
            <span key={d.id} className="feature-chip">{d.name} · {d.rated_power}W</span>
          ))}
        </div>
      </Card>
    </div>
  );
}
