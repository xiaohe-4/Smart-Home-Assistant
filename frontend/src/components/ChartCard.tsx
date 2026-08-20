import type { ReactNode } from "react";
import { Card, Empty, Spin } from "antd";
import ReactECharts from "echarts-for-react";

export default function ChartCard({
  title,
  loading,
  empty,
  option,
  height = 320,
  extra,
}: {
  title: string;
  loading?: boolean;
  empty?: boolean;
  option: Record<string, unknown>;
  height?: number;
  extra?: ReactNode;
}) {
  return (
    <Card title={title} extra={extra} styles={{ body: { minHeight: height } }}>
      {loading ? (
        <div className="chart-empty"><Spin /></div>
      ) : empty ? (
        <div className="chart-empty"><Empty description="暂无数据" /></div>
      ) : (
        <ReactECharts option={option} style={{ height }} notMerge />
      )}
    </Card>
  );
}
