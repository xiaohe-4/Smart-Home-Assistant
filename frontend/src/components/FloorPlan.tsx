import type { InsightsPayload } from "../types";

export default function FloorPlan({ rooms, location }: { rooms: NonNullable<InsightsPayload["showcase"]>["rooms"]; location?: string }) {
  return (
    <div className="floorplan">
      <div className={`room room-living ${location === "客厅" ? "here" : ""} ${rooms.find((r) => r.name === "客厅")?.active ? "on" : ""}`}>
        <div className="room-name">客厅</div>
        <div className="room-kwh">{rooms.find((r) => r.name === "客厅")?.energy ?? 0} kWh</div>
        <div className="room-run">{rooms.find((r) => r.name === "客厅")?.running.join(" · ") || "待机"}</div>
      </div>
      <div className="floor-right">
        <div className={`room room-study ${location === "书房" ? "here" : ""} ${rooms.find((r) => r.name === "书房")?.active ? "on" : ""}`}>
          <div className="room-name">书房</div>
          <div className="room-kwh">{rooms.find((r) => r.name === "书房")?.energy ?? 0} kWh</div>
        </div>
        <div className={`room room-kitchen ${location === "餐厅" || location === "厨房" ? "here" : ""} ${rooms.find((r) => r.name === "厨房")?.active ? "on" : ""}`}>
          <div className="room-name">厨房</div>
          <div className="room-kwh">{rooms.find((r) => r.name === "厨房")?.energy ?? 0} kWh</div>
        </div>
        <div className={`room room-bed ${location === "卧室" ? "here" : ""}`}>
          <div className="room-name">卧室</div>
          <div className="room-kwh">睡眠区</div>
        </div>
        <div className={`room room-bath ${location === "卫生间" ? "here" : ""} ${rooms.find((r) => r.name === "卫生间")?.active ? "on" : ""}`}>
          <div className="room-name">卫生间</div>
          <div className="room-kwh">{rooms.find((r) => r.name === "卫生间")?.energy ?? 0} kWh</div>
        </div>
      </div>
    </div>
  );
}
