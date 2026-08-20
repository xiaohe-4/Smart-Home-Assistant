import { useEffect, useState } from "react";
import { Button, Card, Col, Input, Progress, Row, Space, Tag } from "antd";
import { AudioOutlined } from "@ant-design/icons";
import { butlerApi } from "../api";
import FloorPlan from "../components/FloorPlan";
import { canListen, listenOnce, speak } from "../hooks/useSpeech";
import type { ButlerReply, ButlerState } from "../types";

export default function Butler() {
  const [state, setState] = useState<ButlerState | null>(null);
  const [text, setText] = useState("汇报一下");
  const [listening, setListening] = useState(false);
  const [busy, setBusy] = useState(false);
  const [last, setLast] = useState<ButlerReply | null>(null);
  const [talking, setTalking] = useState(false);

  const load = () => butlerApi.state().then(setState);

  useEffect(() => {
    void load();
    const queued = sessionStorage.getItem("se-butler-cmd");
    if (queued) {
      sessionStorage.removeItem("se-butler-cmd");
      void run(queued);
    }
    const onUpdate = () => void load();
    window.addEventListener("se-home-update", onUpdate);
    return () => window.removeEventListener("se-home-update", onUpdate);
  }, []);

  const apply = (res: ButlerReply) => {
    setLast(res);
    setState(res);
    if (!res.quiet) {
      setTalking(true);
      speak(res.speech, () => setTalking(false));
    }
    window.dispatchEvent(new Event("se-home-update"));
  };

  const run = async (command: string) => {
    const q = command.trim();
    if (!q) return;
    setBusy(true);
    try {
      apply(await butlerApi.command(q));
    } finally {
      setBusy(false);
    }
  };

  const mic = () => {
    if (!canListen()) {
      setLast({
        ...(state as ButlerReply),
        speech: "这浏览器不让我听。您打字也行，说：汇报一下。",
        intent: "chat",
        actions: [],
      });
      return;
    }
    setListening(true);
    listenOnce((said, final) => {
      if (said) setText(said);
      if (final) {
        setListening(false);
        if (said) void run(said);
      }
    });
  };

  const rooms = [
    { name: "客厅", types: ["air_conditioner", "television", "other"] },
    { name: "书房", types: ["computer"] },
    { name: "厨房", types: ["refrigerator"] },
    { name: "卫生间", types: ["water_heater", "washing_machine"] },
    { name: "全屋", types: ["lighting"] },
  ].map((room) => {
    const hit = (state?.devices || []).filter((d) => room.types.includes(d.device_type));
    const running = hit.filter((d) => d.status === "运行");
    return {
      name: room.name,
      energy: Number(hit.reduce((s, d) => s + d.today_energy, 0).toFixed(2)),
      running: running.map((d) => d.name),
      active: running.length > 0,
    };
  });

  return (
    <div>
      <h1 className="page-title">管家宝强</h1>
      <p className="page-sub">能听、能说、能拧开关、能汇报、能记住偏好。控制是家庭侧模拟，节能量按功率差估到午夜。</p>
      <Row gutter={16}>
        <Col xs={24} lg={10}>
          <Card>
            <div className={`butler-stage ${talking ? "talking" : ""}`}>
              <div className="butler-avatar lg">
                <div className="butler-cap" />
                <div className="butler-head">
                  <div className="butler-eye" />
                  <div className="butler-eye" />
                  <div className={`butler-mouth ${talking ? "on" : ""}`} />
                </div>
                <div className="butler-body">智家能管家</div>
              </div>
              <div>
                <div className="hero-kicker">
                  {state?.scene || "日常"} · 偏好 {state?.preferred_ac ?? 26}℃ {state?.quiet ? "· 免打扰" : ""}
                </div>
                <p className="butler-speech big">{last?.speech || state?.brief || "您先歇着。说汇报一下，我把家里过一遍。"}</p>
              </div>
            </div>
            {state?.pending_cmd ? (
              <div className="pending-banner">
                备着：{state.pending_reason || state.pending_cmd}
                <Button type="primary" size="small" onClick={() => void run("点头")}>点头去办</Button>
              </div>
            ) : null}
            <div className="suggest-row">
              {(state?.suggestions || []).map((s) => (
                <button key={s.cmd} className="command-chip" onClick={() => void run(s.cmd)} title={s.why}>{s.label}</button>
              ))}
            </div>
            <Space.Compact style={{ width: "100%", marginTop: 8 }}>
              <Input value={text} onChange={(e) => setText(e.target.value)} onPressEnter={() => void run(text)} placeholder="例如：宝强，我起床了" />
              <Button icon={<AudioOutlined />} type={listening ? "primary" : "default"} onClick={mic}>{listening ? "在听" : "说话"}</Button>
              <Button type="primary" loading={busy} onClick={() => void run(text)}>去办</Button>
            </Space.Compact>
            <div className="page-sub" style={{ marginTop: 8 }}>语音需 Chrome / Edge。系统会优先用更自然的中文声线，数字按口语来读。也可以点技能，或者说：点头、调高一度、有客人。</div>
          </Card>
          {(state?.skills || []).map((group) => (
            <Card key={group.group} title={group.group} size="small" style={{ marginTop: 12 }}>
              <div className="skill-grid">
                {group.items.map((item) => (
                  <button key={item.cmd} className="skill-btn" onClick={() => void run(item.cmd)}>
                    <b>{item.title}</b>
                    <span>{item.desc}</span>
                  </button>
                ))}
              </div>
            </Card>
          ))}
        </Col>
        <Col xs={24} lg={14}>
          <Card title="家电执行看板" extra={`功率 ${((state?.current_power || 0) / 1000).toFixed(2)} kW`}>
            <Row gutter={12} style={{ marginBottom: 12 }}>
              <Col span={8}><b>{state?.saving_w ?? 0}</b> W 已压下来</Col>
              <Col span={8}><b>{state?.saving_kwh_est ?? 0}</b> kWh 估到午夜</Col>
              <Col span={8}><b>{state?.saving_carbon ?? 0}</b> kg 碳</Col>
            </Row>
            <FloorPlan rooms={rooms} />
            <div className="device-grid" style={{ marginTop: 16 }}>
              {(state?.devices || []).map((d) => (
                <div key={d.id} className={`device-tile ${d.status === "关闭" ? "" : "active"}`}>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <b>{d.name}</b>
                    <Tag color={d.status === "运行" ? "green" : d.status === "关闭" ? "red" : "default"}>{d.status}</Tag>
                  </div>
                  <div style={{ margin: "8px 0", fontSize: 20, fontWeight: 800 }}>{d.current_power} W</div>
                  <Progress percent={d.share} size="small" strokeColor="#16a34a" />
                  <Space wrap style={{ marginTop: 8 }}>
                    <Button size="small" onClick={() => void run(`关闭${d.name}`)}>关闭</Button>
                    <Button size="small" onClick={() => void run(`打开${d.name}`)}>打开</Button>
                    {d.device_type === "air_conditioner" ? (
                      <>
                        <Button size="small" onClick={() => void run("调高一度")}>热+1℃</Button>
                        <Button size="small" onClick={() => void run("调低一度")}>冷-1℃</Button>
                        <Button size="small" onClick={() => void run("按我习惯调空调")}>{state?.preferred_ac ?? 26}℃</Button>
                      </>
                    ) : null}
                  </Space>
                  {d.actuator_note ? <div className="explain-note">{d.actuator_note}</div> : null}
                </div>
              ))}
            </div>
          </Card>
          <Card title="管家日志" style={{ marginTop: 16 }}>
            {(state?.logs || []).map((log, i) => (
              <div key={`${log.created_at}-${i}`} className="assistant-bubble">
                <Tag>{log.intent}</Tag> {log.command}
                <div style={{ marginTop: 6 }}>{log.speech}</div>
              </div>
            ))}
          </Card>
        </Col>
      </Row>
    </div>
  );
}
