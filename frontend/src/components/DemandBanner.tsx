import { Button, Progress, Tag } from "antd";
import type { LifeOs } from "../types";

export default function DemandBanner({
  demand,
  onAccept,
  onDecline,
}: {
  demand: LifeOs["demand"];
  onAccept: () => void;
  onDecline: () => void;
}) {
  const tone = demand.status === "accepted" ? "ok" : demand.status === "declined" ? "" : "warn";
  const statusText = demand.status === "accepted" ? "已应邀" : demand.status === "declined" ? "已回绝" : "待响应";
  return (
    <div className={`dr-banner ${tone}`}>
      <div>
        <div className="hero-kicker">{demand.title}</div>
        <b>
          {demand.window} 削峰 {demand.target_percent}% · {statusText}
        </b>
        <div>
          当前 {demand.current_w} W → 目标 {demand.target_w} W，示意奖励 {demand.reward_yuan} 元。{demand.note}
        </div>
        <Progress percent={Math.min(100, demand.progress)} size="small" strokeColor="#16a34a" style={{ maxWidth: 360, marginTop: 8 }} />
      </div>
      <div className="dr-actions">
        <Tag color={demand.status === "accepted" ? "green" : "gold"}>{statusText}</Tag>
        {demand.status !== "accepted" ? (
          <Button type="primary" onClick={onAccept}>
            应下邀约，让宝强去办
          </Button>
        ) : null}
        {demand.status === "pending" ? <Button onClick={onDecline}>这次先回绝</Button> : null}
      </div>
    </div>
  );
}
