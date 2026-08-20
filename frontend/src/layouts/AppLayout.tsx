import { Button, ConfigProvider, Layout, Menu, Switch, Typography, theme } from "antd";
import {
  AlertOutlined,
  AppstoreOutlined,
  BarChartOutlined,
  CommentOutlined,
  CompassOutlined,
  CustomerServiceOutlined,
  DashboardOutlined,
  DatabaseOutlined,
  ExperimentOutlined,
  FundOutlined,
  LineChartOutlined,
  QuestionCircleOutlined,
  ScheduleOutlined,
  ThunderboltOutlined,
} from "@ant-design/icons";
import DemoTour from "../components/DemoTour";
import ButlerDock from "../components/ButlerDock";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";

const { Sider, Header, Content } = Layout;

const items = [
  { key: "/", icon: <DashboardOutlined />, label: "智能总览" },
  { key: "/energy", icon: <BarChartOutlined />, label: "能耗分析" },
  { key: "/devices", icon: <AppstoreOutlined />, label: "家庭设备" },
  { key: "/prediction", icon: <LineChartOutlined />, label: "能耗预测" },
  { key: "/models", icon: <FundOutlined />, label: "模型实验" },
  { key: "/anomaly", icon: <AlertOutlined />, label: "异常检测" },
  { key: "/insights", icon: <CompassOutlined />, label: "智能洞察" },
  { key: "/strategy", icon: <ThunderboltOutlined />, label: "AI 节能建议" },
  { key: "/butler", icon: <CustomerServiceOutlined />, label: "管家宝强" },
  { key: "/life", icon: <ScheduleOutlined />, label: "生活系统" },
  { key: "/sources", icon: <DatabaseOutlined />, label: "数据来源" },
  { key: "/assistant", icon: <CommentOutlined />, label: "能源助手" },
  { key: "/guide", icon: <QuestionCircleOutlined />, label: "使用说明" },
  { key: "/profile", icon: <ExperimentOutlined />, label: "家庭能源画像" },
];

export default function AppLayout() {
  const nav = useNavigate();
  const loc = useLocation();
  const [dark, setDark] = useState(() => localStorage.getItem("se-dark") === "1");

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem("se-dark", dark ? "1" : "0");
  }, [dark]);

  return (
    <ConfigProvider
      theme={{
        algorithm: dark ? theme.darkAlgorithm : theme.defaultAlgorithm,
        token: { colorPrimary: "#16a34a", borderRadius: 10 },
      }}
    >
      <Layout style={{ minHeight: "100vh" }}>
        <Sider className="app-sider" breakpoint="lg" collapsedWidth={64} width={232}>
          <div style={{ display: "flex", gap: 10, alignItems: "center", padding: "22px 16px 14px" }}>
            <div className="logo-mark">智</div>
            <div>
              <div style={{ color: "#fff", fontWeight: 800, fontSize: 18 }}>智家能</div>
              <div style={{ color: "#9eccb8", fontSize: 12 }}>多模态能源决策引擎</div>
            </div>
          </div>
          <Menu theme="dark" selectedKeys={[loc.pathname]} items={items} onClick={(e) => nav(e.key)} />
        </Sider>
        <Layout>
          <Header className="app-header">
            <Typography.Text>
              <span className="status-dot" />
              AI 引擎在线 · 成都四口之家 · 多模态仿真灌入标准表
            </Typography.Text>
            <span className="live-pill">
              <Button type="link" size="small" icon={<QuestionCircleOutlined />} onClick={() => nav("/guide")} style={{ padding: 0, marginRight: 8 }}>
                使用说明
              </Button>
              演示日 2026-08-19
              <Switch size="small" checked={dark} onChange={setDark} checkedChildren="夜" unCheckedChildren="日" style={{ marginLeft: 8 }} />
            </span>
          </Header>
          <Content style={{ margin: 20 }}>
            <Outlet />
          </Content>
          <DemoTour />
          <ButlerDock />
        </Layout>
      </Layout>
    </ConfigProvider>
  );
}
