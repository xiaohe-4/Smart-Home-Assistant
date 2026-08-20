import type { LifeClock } from "../types";

export default function PriceClock({ clock }: { clock: LifeClock }) {
  const tone = clock.period === "peak" ? "peak" : clock.period === "valley" ? "valley" : "flat";
  return (
    <div className={`price-clock ${tone}`}>
      <div>
        <div className="hero-kicker">{clock.as_of} · 当前电价</div>
        <div className="clock-price">{clock.period_label} {clock.price} 元/kWh</div>
      </div>
      <div className="clock-next">
        {clock.minutes_left} 分钟后切到{clock.next_label}（{clock.next_at}）
        <div>{clock.advice}</div>
      </div>
    </div>
  );
}
