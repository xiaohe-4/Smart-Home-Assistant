import type { ReactNode } from "react";
import { Card } from "antd";

export default function KpiCard({
  label,
  value,
  suffix,
  hint,
  tone = "green",
  icon,
}: {
  label: string;
  value: ReactNode;
  suffix?: string;
  hint?: string;
  tone?: "green" | "gold" | "cyan" | "rose";
  icon?: ReactNode;
}) {
  return (
    <Card className={`kpi-card kpi-${tone}`} bordered={false}>
      <div className="kpi-top">
        <span className="kpi-label">{label}</span>
        {icon ? <span className="kpi-icon">{icon}</span> : null}
      </div>
      <div className="kpi-value">
        {value}
        {suffix ? <span className="kpi-suffix">{suffix}</span> : null}
      </div>
      {hint ? <div className="kpi-hint">{hint}</div> : null}
    </Card>
  );
}
