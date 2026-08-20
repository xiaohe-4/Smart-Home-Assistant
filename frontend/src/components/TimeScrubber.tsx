import { useEffect, useRef, useState } from "react";
import { Button, Slider, Tag } from "antd";
import { PauseCircleOutlined, PlayCircleOutlined } from "@ant-design/icons";

type Frame = {
  hour: number;
  label: string;
  power: number;
  occupancy: number;
  activity: string;
  location: string;
  temperature: number | null;
  period: string;
  price: number;
  action: string;
  brief?: string;
  alert?: boolean;
  optimized_power?: number;
};

export default function TimeScrubber({
  frames,
  hour,
  onChange,
}: {
  frames: Frame[];
  hour: number;
  onChange: (hour: number) => void;
}) {
  const [playing, setPlaying] = useState(false);
  const hourRef = useRef(hour);
  hourRef.current = hour;

  useEffect(() => {
    if (!playing) return;
    const timer = window.setInterval(() => {
      const next = hourRef.current >= 23 ? 0 : hourRef.current + 1;
      onChange(next);
      if (next === 20) setPlaying(false);
    }, 520);
    return () => window.clearInterval(timer);
  }, [playing, onChange]);

  const current = frames.find((f) => f.hour === hour) || frames[0];
  if (!current) return null;
  return (
    <div className="scrubber">
      <div className="scrubber-top">
        <Button
          type={playing ? "default" : "primary"}
          size="small"
          icon={playing ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
          onClick={() => setPlaying((v) => !v)}
        >
          {playing ? "暂停回放" : "回放今日"}
        </Button>
        <b>{current.label}</b>
        <Tag color={current.period === "peak" ? "gold" : current.period === "valley" ? "blue" : "green"}>
          {current.period === "peak" ? "高峰电价" : current.period === "valley" ? "谷段电价" : "平时电价"} {current.price} 元
        </Tag>
        {current.alert ? <Tag color="red">异常窗口</Tag> : null}
        <span>{(current.power / 1000).toFixed(2)} kW · {current.occupancy} 人 · {current.location} · {current.activity}</span>
      </div>
      <Slider min={0} max={23} value={hour} tooltip={{ formatter: (v) => `${String(v).padStart(2, "0")}:00` }} onChange={onChange} />
      <div className="scrubber-action">{current.brief || `调度建议：${current.action}`}</div>
    </div>
  );
}
