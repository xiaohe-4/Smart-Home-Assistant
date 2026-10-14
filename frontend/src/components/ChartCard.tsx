import { useEffect, useState, type ReactNode } from "react";
import { Card, Empty, Spin } from "antd";
import ReactECharts from "echarts-for-react";
import { themedOption } from "../utils/chart";

function useDark() {
  const [dark, setDark] = useState(() => document.documentElement.classList.contains("dark"));
  useEffect(() => {
    const obs = new MutationObserver(() => setDark(document.documentElement.classList.contains("dark")));
    obs.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
    return () => obs.disconnect();
  }, []);
  return dark;
}

export default function ChartCard({
  title,
  loading,
  empty,
  option,
  height = 320,
  extra,
}: {
  title?: string;
  loading?: boolean;
  empty?: boolean;
  option: Record<string, unknown>;
  height?: number;
  extra?: ReactNode;
}) {
  const dark = useDark();
  return (
    <Card title={title || undefined} extra={extra} styles={{ body: { minHeight: height } }}>
      {loading ? (
        <div className="chart-empty"><Spin /></div>
      ) : empty ? (
        <div className="chart-empty"><Empty description="暂无数据" /></div>
      ) : (
        <ReactECharts option={themedOption(option, dark)} style={{ height }} notMerge />
      )}
    </Card>
  );
}
