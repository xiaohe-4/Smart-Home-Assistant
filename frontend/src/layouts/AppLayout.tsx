import { Button, ConfigProvider, Drawer, Layout, Menu, Select, Switch, Typography, message, theme } from "antd";
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
  MenuOutlined,
  QuestionCircleOutlined,
  ScheduleOutlined,
  ThunderboltOutlined,
} from "@ant-design/icons";
import zhCN from "antd/locale/zh_CN";
import DemoTour from "../components/DemoTour";
import ButlerDock from "../components/ButlerDock";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { appStore } from "../stores/appStore";

const { Sider, Header, Content } = Layout;

const items = [
  { key: "/", icon: <DashboardOutlined />, label: "总览" },
  { key: "/energy", icon: <BarChartOutlined />, label: "能耗分析" },
  { key: "/devices", icon: <AppstoreOutlined />, label: "家庭设备" },
  { key: "/prediction", icon: <LineChartOutlined />, label: "能耗预测" },
  { key: "/anomaly", icon: <AlertOutlined />, label: "异常" },
  { key: "/strategy", icon: <ThunderboltOutlined />, label: "节能建议" },
  { key: "/butler", icon: <CustomerServiceOutlined />, label: "管家宝强" },
  { key: "/life", icon: <ScheduleOutlined />, label: "生活系统" },
  { key: "/guide", icon: <QuestionCircleOutlined />, label: "使用说明" },
  { key: "/assistant", icon: <CommentOutlined />, label: "能源助手" },
  { key: "/profile", icon: <ExperimentOutlined />, label: "这户概况" },
  {
    key: "lab",
    icon: <FundOutlined />,
    label: "实验与数据",
    children: [
      { key: "/sources", icon: <DatabaseOutlined />, label: "数据来源" },
      { key: "/models", icon: <FundOutlined />, label: "模型实验" },
      { key: "/insights", icon: <CompassOutlined />, label: "用电对照" },
    ],
  },
];

export default function AppLayout() {
  const nav = useNavigate();
  const loc = useLocation();
  const [dark, setDark] = useState(() => localStorage.getItem("se-dark") === "1");
  const [userId, setUserId] = useState(appStore.userId);
  const [mute, setMute] = useState(() => localStorage.getItem("se-mute") === "1");
  const [narrow, setNarrow] = useState(() => window.innerWidth < 992);
  const [navOpen, setNavOpen] = useState(false);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem("se-dark", dark ? "1" : "0");
  }, [dark]);

  useEffect(() => {
    const onResize = () => setNarrow(window.innerWidth < 992);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  useEffect(() => {
    message.config({ top: 76, maxCount: 1, duration: 2.4 });
  }, []);

  const switchHome = (id: number) => {
    appStore.setUserId(id);
    setUserId(id);
  };

  const setMuteNow = (value: boolean) => {
    setMute(value);
    localStorage.setItem("se-mute", value ? "1" : "0");
  };

  const go = (key: string) => {
    if (!key.startsWith("/")) return;
    nav(key);
    setNavOpen(false);
  };

  const menu = (
    <Menu
      mode="inline"
      theme="dark"
      selectedKeys={[loc.pathname]}
      defaultOpenKeys={["lab"]}
      items={items}
      onClick={(e) => go(String(e.key))}
    />
  );

  const brand = (
    <div className="sider-brand">
      <img className="logo-mark" src="/art/logo.jpg?v=3" alt="" />
      <div>
        <div className="sider-name">智家能</div>
        <div className="sider-tag">今晚该关什么</div>
      </div>
    </div>
  );

  return (
    <ConfigProvider
      locale={zhCN}
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
            darkItemSelectedBg: "rgba(52, 211, 153, 0.22)",
            darkItemSelectedColor: "#ecfdf5",
            darkItemHoverBg: "rgba(255,255,255,0.06)",
            darkItemColor: "#d7ece2",
            itemBorderRadius: 10,
            itemHeight: 40,
            itemMarginInline: 8,
          },
        },
      }}
    >
      <Layout style={{ minHeight: "100vh" }}>
        {narrow ? (
          <Drawer
            placement="left"
            open={navOpen}
            onClose={() => setNavOpen(false)}
            width={268}
            closable={false}
            rootClassName="nav-drawer"
            styles={{ body: { padding: 0 } }}
          >
            {brand}
            {menu}
          </Drawer>
        ) : (
          <Sider className="app-sider" collapsible collapsedWidth={72} width={228} theme="dark">
            {brand}
            {menu}
          </Sider>
        )}
        <Layout>
          <Header className="app-header">
            <div className="header-left">
              {narrow ? (
                <Button type="text" className="nav-toggle" icon={<MenuOutlined />} aria-label="打开菜单" onClick={() => setNavOpen(true)} />
              ) : null}
              <span className="status-dot" />
              <Typography.Text className="header-home">
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
              <Button type="text" size="small" className="guide-link" icon={<QuestionCircleOutlined />} onClick={() => nav("/guide")}>
                <span className="guide-label">使用说明</span>
              </Button>
              <span className="header-tools">
                <span className="header-date">2026-08-19</span>
                <Switch size="small" checked={mute} onChange={setMuteNow} checkedChildren="静音" unCheckedChildren="语音" />
                <Switch size="small" checked={dark} onChange={setDark} checkedChildren="夜" unCheckedChildren="日" />
              </span>
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
