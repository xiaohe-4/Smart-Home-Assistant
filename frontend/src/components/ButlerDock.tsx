import { useCallback, useEffect, useState } from "react";
import { Button, Input, Space, Tag } from "antd";
import { AudioOutlined, CloseOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { butlerApi } from "../api";
import { canListen, listenOnce, speak } from "../hooks/useSpeech";
import type { ButlerReply, ButlerState } from "../types";

export default function ButlerDock({ muted = false }: { muted?: boolean }) {
  const nav = useNavigate();
  const [open, setOpen] = useState(false);
  const [text, setText] = useState("");
  const [listening, setListening] = useState(false);
  const [busy, setBusy] = useState(false);
  const [last, setLast] = useState<ButlerReply | null>(null);
  const [state, setState] = useState<ButlerState | null>(null);
  const [talking, setTalking] = useState(false);

  const load = () => butlerApi.state().then(setState);
  const silent = muted || localStorage.getItem("se-mute") === "1";

  const run = useCallback(async (command: string) => {
    const q = command.trim();
    if (!q) return;
    setBusy(true);
    try {
      const res = await butlerApi.command(q);
      setLast(res);
      setState(res);
      if (!res.quiet && localStorage.getItem("se-mute") !== "1") {
        setTalking(true);
        speak(res.speech, () => setTalking(false));
      }
      window.dispatchEvent(new Event("se-home-update"));
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    const openPanel = () => {
      setOpen(true);
      void load();
    };
    const auto = () => {
      setOpen(true);
      void run("执行今晚节能方案");
    };
    window.addEventListener("se-butler-open", openPanel);
    window.addEventListener("se-butler-eco", auto);
    return () => {
      window.removeEventListener("se-butler-open", openPanel);
      window.removeEventListener("se-butler-eco", auto);
    };
  }, [run]);

  const mic = () => {
    if (!canListen()) {
      nav("/butler");
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

  const chips = state?.suggestions?.length
    ? state.suggestions.map((s) => s.cmd)
    : ["汇报一下", "把空调调到26度", "执行今晚节能方案", "晚安"];

  return (
    <>
      <button className={`butler-fab ${talking ? "talking" : ""}`} onClick={() => { setOpen((v) => !v); if (!open) void load(); }} title="管家宝强">
        <img className="butler-face" src="/art/butler.jpg" alt="" />
        <span>管家宝强</span>
      </button>
      {open ? (
        <div className="butler-dock">
          <div className="butler-dock-top">
            <b>管家宝强 · {state?.scene || "日常"}</b>
            <Button type="text" size="small" icon={<CloseOutlined />} onClick={() => setOpen(false)} />
          </div>
          <img className={`butler-portrait ${talking ? "talking" : ""}`} src="/art/butler.jpg" alt="" />
          <p className="butler-speech">{last?.speech || state?.brief || "您歇着，开关我来拧。可以说：汇报一下。"}</p>
          {silent ? <p className="explain-note">语音已关，只显示文字。</p> : null}
          {state?.pending_cmd ? (
            <div className="pending-banner slim">
              备着 {state.pending_reason || state.pending_cmd}
              <Button type="primary" size="small" onClick={() => void run("点头")}>点头</Button>
            </div>
          ) : null}
          {last?.actions?.length ? (
            <div className="butler-actions">
              {last.actions.map((a) => (
                <Tag key={a.device_id} color="green">{a.action}</Tag>
              ))}
            </div>
          ) : null}
          <Space wrap>
            {chips.slice(0, 6).map((q) => (
              <Button key={q} size="small" onClick={() => void run(q)}>{q}</Button>
            ))}
          </Space>
          <Space.Compact style={{ width: "100%", marginTop: 10 }}>
            <Input value={text} onChange={(e) => setText(e.target.value)} onPressEnter={() => void run(text)} placeholder="宝强，我起床了" />
            <Button icon={<AudioOutlined />} type={listening ? "primary" : "default"} onClick={mic} />
            <Button type="primary" loading={busy} onClick={() => void run(text)}>去办</Button>
          </Space.Compact>
          <Button type="link" onClick={() => nav("/butler")}>打开管家</Button>
        </div>
      ) : null}
    </>
  );
}
