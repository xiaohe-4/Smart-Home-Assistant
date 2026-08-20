import { Button, Progress, Tag } from "antd";
import type { LifeOs } from "../types";

export default function TonightBoard({
  missions,
  challenge,
  compact,
  onRun,
}: {
  missions: LifeOs["missions"];
  challenge: LifeOs["challenge"] | undefined;
  compact?: boolean;
  onRun: (key: string, command: string) => void;
}) {
  const list = compact ? missions.slice(0, 3) : missions;
  const ch = challenge || { title: "今晚家庭挑战", goal: "", done: 0, target: 3, points: 0, badges: 0, label: "" };
  return (
    <div>
      <div className="challenge-bar">
        <div>
          <b>{ch.title}</b>
          <span>
            {ch.goal} · {ch.label} · {ch.points} 分
          </span>
        </div>
        <Progress percent={Math.min(100, (ch.done / Math.max(ch.target, 1)) * 100)} steps={ch.target} strokeColor="#16a34a" />
      </div>
      <div className={`mission-grid ${compact ? "compact" : ""}`}>
        {list.map((m) => (
          <div key={m.key} className={`mission-card ${m.done ? "done" : ""}`}>
            <div>
              <b>{m.title}</b> {m.done ? <Tag color="green">已完成</Tag> : <Tag>待办</Tag>}
              <div className="kpi-hint">{m.why}</div>
              <div className="kpi-hint">
                约 {m.saving_kwh} kWh / {m.saving_yuan} 元
              </div>
            </div>
            {m.done ? null : (
              <Button type="primary" size="small" onClick={() => onRun(m.key, m.command)}>
                让宝强去办
              </Button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
