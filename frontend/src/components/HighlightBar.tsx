import { Card } from "antd";
import type { InsightsPayload } from "../types";

export default function HighlightBar({ items }: { items: NonNullable<InsightsPayload["showcase"]>["highlights"] }) {
  return (
    <div className="highlight-bar">
      {items.map((item) => (
        <Card key={item.title} className="highlight-card" bordered={false} size="small">
          <div className="highlight-tag">{item.tag}</div>
          <div className="highlight-title">{item.title}</div>
          <div className="highlight-detail">{item.detail}</div>
        </Card>
      ))}
    </div>
  );
}
