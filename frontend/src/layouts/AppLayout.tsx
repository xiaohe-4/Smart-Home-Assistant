import { Button, ConfigProvider, Layout, Menu, Select, Switch, Typography, theme } from "antd";
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
import { appStore } from "../stores/appStore";

const { Sider, Header, Content } = Layout;

const items = [
  { key: "/", icon: <DashboardOutlined />, label: "智能总览" },
  { key: "/energy", icon: <BarChartOutlined />, label: "能耗分析" },
  { key: "/devices", icon: <AppstoreOutlined />, label: "家庭设备" },
  { key: "/prediction", icon: <LineChartOutlined />, label: "能耗预测" },
  { key: "/anomaly", icon: <AlertOutlined />, label: "异常解释器" },
  { key: "/strategy", icon: <ThunderboltOutlined />, label: "AI 节能建议" },
  { key: "/butler", icon: <CustomerServiceOutlined />, label: "管家宝强" },
  { key: "/life", icon: <ScheduleOutlined />, label: "生活系统" },
  { key: "/guide", icon: <QuestionCircleOutlined />, label: "使用说明" },
  { key: "/assistant", icon: <CommentOutlined />, label: "能源助手" },
  { key: "/profile", icon: <ExperimentOutlined />, label: "家庭能源画像" },
  {
    key: "lab",
    icon: <FundOutlined />,
    label: "实验与数据",
    children: [
      { key: "/sources", icon: <DatabaseOutlined />, label: "数据来源" },
      { key: "/models", icon: <FundOutlined />, label: "模型实验" },
      { key: "/insights", icon: <CompassOutlined />, label: "智能洞察" },
    ],
  },
];

export default function AppLayout() {
  const nav = useNavigate();
  const loc = useLocation();
  const [dark, setDark] = useState(() => localStorage.getItem("se-dark") === "1");
  const [userId, setUserId] = useState(appStore.userId);
  const [mute, setMute] = useState(() => localStorage.getItem("se-mute") === "1");

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem("se-dark", dark ? "1" : "0");
  }, [dark]);

  useEffect(() => {
    localStorage.setItem("se-mute", mute ? "1" : "0");
  }, [mute]);

  const switchHome = (id: number) => {
    appStore.setUserId(id);
    setUserId(id);
  };

  return (
    <ConfigProvider
      theme={{
        algorithm: dark ? theme.darkAlgorithm : theme.defaultAlgorithm,
        token: {
          colorPrimary: "#16a34a",
          borderRadius: 12,
          fontFamily: '"Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif',
          colorText: dark ? "#e7f6ee" : "#123026",
        },
        components: {
          Card: { borderRadiusLG: 16 },
          Menu: {
            darkItemBg: "transparent",
            darkSubMenuItemBg: "transparent",
            darkItemSelectedBg: "rgba(52, 211, 153, 0.18)",
            darkItemHoverBg: "rgba(255,255,255,0.06)",
          },
        },
      }}
    >
      <Layout style={{ minHeight: "100vh" }}>
        <Sider className="app-sider" breakpoint="lg" collapsedWidth={64} width={228}>
          <div className="sider-brand">
            <div className="logo-mark">智</div>
            <div>
              <div className="sider-name">智家能</div>
              <div className="sider-tag">今晚该关什么</div>
            </div>
          </div>
          <Menu
            theme="dark"
            selectedKeys={[loc.pathname]}
            defaultOpenKeys={["lab"]}
            items={items}
            onClick={(e) => nav(e.key)}
          />
        </Sider>
        <Layout>
          <Header className="app-header">
            <div className="header-left">
              <span className="status-dot" />
              <Typography.Text>
                {userId === 2 ? "验证户 · 缺模态已降级" : "演示户 · 成都仿真四口"}
              </Typography.Text>
              <span className="header-chip">{userId === 2 ? "公开/真实对照" : "演示含仿真"}</span>
            </div>
            <div className="header-right">
              <Select
                size="small"
                className="home-switch"
                value={userId}
                onChange={switchHome}
                options={[
                  { value: 1, label: "演示户 · 仿真四口" },
                  { value: 2, label: "验证户 · 宿舍风格" },
                ]}
              />
              <Button type="text" size="small" icon={<QuestionCircleOutlined />} onClick={() => nav("/guide")}>
                使用说明
              </Button>
              <span className="header-date">2026-08-19</span>
              <Switch size="small" checked={mute} onChange={setMute} checkedChildren="静音" unCheckedChildren="语音" />
              <Switch size="small" checked={dark} onChange={setDark} checkedChildren="夜" unCheckedChildren="日" />
            </div>
          </Header>
          <Content className="app-content">
            <Outlet key={userId} />
          </Content>
          <DemoTour />
          <ButlerDock muted={mute} />
        </Layout>
      </Layout>
    </ConfigProvider>
  );
}
