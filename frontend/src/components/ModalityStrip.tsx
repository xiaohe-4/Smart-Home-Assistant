import { useNavigate } from "react-router-dom";
import type { SourceModality } from "../types";

export default function ModalityStrip({
  items,
  percent,
  clickable = true,
}: {
  items: SourceModality[];
  percent?: number;
  clickable?: boolean;
}) {
  const nav = useNavigate();
  if (!items.length) return null;
  return (
    <div className="modality-strip" onClick={clickable ? () => nav("/sources") : undefined} role={clickable ? "button" : undefined}>
      {items.map((m) => (
        <div key={m.key} className={`modality-pill ${m.active ? "on" : ""}`}>
          <b>{m.label}</b>
          <span>{m.active ? `${m.coverage}% 对齐` : "未接入"}</span>
        </div>
      ))}
      {percent != null ? <div className="modality-pill align">演示日四路对齐 {percent}%</div> : null}
    </div>
  );
}
