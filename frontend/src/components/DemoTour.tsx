import { useEffect, useRef, useState } from "react";
import { Button, Modal, Typography, Switch, Space } from "antd";
import { PlayCircleOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";

const CORE = [
  { title: "今天为什么贵", path: "/", text: "点「回放今日」，从早拉到 20:30。看今日电量、第一耗电设备和评分。贵，主要贵在空调。" },
  { title: "03:17 那笔", path: "/anomaly", text: "拉到 03:17 热水器启动。时段不合理，家里人少，功率也偏了。模型 F1 只有 0.35，以规则为准，模型只打分。" },
  { title: "空调调到 26 度", path: "/strategy", text: "把空调从 24℃ 调到 26℃，看电量、电费和削峰。再到管家那里点头。说一次关冰箱，会被拒绝。开关是模拟的。" },
];

const ADVANCED = [
  ...CORE,
  { title: "完整 · 能耗结构", path: "/energy", text: "空调约 41%，热水器约 22%。这是分路电表加总，不是从一块总表里拆出来的。" },
  { title: "完整 · 负荷预测", path: "/prediction", text: "只看 MAE、RMSE、MAPE、R²，以及按时间切开的验证。不要把 100 减 MAPE 当成准确率。" },
  { title: "完整 · 今日安排", path: "/life", text: "电价时段、电网邀约、谷电预约。3 分钟演示默认不进这一页。" },
  { title: "完整 · 数据对照", path: "/sources", text: "演示家庭和对照家庭。对照家庭缺人和天气，缺的部分不硬算。仿真的 R² 不能当成真实家庭的精度。" },
  { title: "完整 · 模型实验", path: "/models", text: "基线对照 + 仿真/真实 MAPE。异常 F1=0.35 主动展示。" },
];

export default function DemoTour() {
  const nav = useNavigate();
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState(0);
  const [auto, setAuto] = useState(false);
  const [advanced, setAdvanced] = useState(false);
  const timer = useRef<number | null>(null);
  const steps = advanced ? ADVANCED : CORE;

  const go = (index: number) => {
    const next = steps[index];
    if (!next) return;
    setStep(index);
    if (next.path === "/butler") sessionStorage.setItem("se-butler-cmd", "执行今晚节能方案");
    if (next.path === "/strategy") sessionStorage.setItem("se-autosim", "1");
    nav(next.path);
    if (next.path === "/strategy") window.dispatchEvent(new Event("se-autosim"));
  };

  const close = () => {
    setOpen(false);
    setAuto(false);
  };

  useEffect(() => {
    if (!auto || !open) {
      if (timer.current) window.clearInterval(timer.current);
      return;
    }
    timer.current = window.setInterval(() => {
      setStep((cur) => {
        if (cur >= steps.length - 1) {
          setAuto(false);
          return cur;
        }
        const nxt = cur + 1;
        nav(steps[nxt].path);
        if (steps[nxt].path === "/strategy") {
          sessionStorage.setItem("se-autosim", "1");
          window.dispatchEvent(new Event("se-autosim"));
        }
        return nxt;
      });
    }, 8000);
    return () => {
      if (timer.current) window.clearInterval(timer.current);
    };
  }, [auto, open, nav, steps]);

  return (
    <>
      <Button type="primary" icon={<PlayCircleOutlined />} className="tour-fab" onClick={() => { setStep(0); setAdvanced(false); setOpen(true); nav("/"); }}>
        3 分钟演示
      </Button>
      <Modal
        className="tour-modal"
        title={steps[step]?.title}
        open={open}
        onCancel={close}
        footer={[
          <Space key="mode"><span>完整导览</span><Switch checked={advanced} onChange={(v) => { setAdvanced(v); setStep(0); }} /></Space>,
          <Space key="auto"><span>自动播放</span><Switch checked={auto} onChange={setAuto} /></Space>,
          <Button key="skip" onClick={close}>跳过</Button>,
          step > 0 ? <Button key="prev" onClick={() => go(step - 1)}>上一步</Button> : null,
          step < steps.length - 1
            ? <Button key="next" type="primary" onClick={() => go(step + 1)}>下一步</Button>
            : <Button key="done" type="primary" onClick={close}>完成演示</Button>,
        ]}
      >
        <Typography.Paragraph>{steps[step]?.text}</Typography.Paragraph>
        <Typography.Text type="secondary">{step + 1} / {steps.length}</Typography.Text>
      </Modal>
    </>
  );
}
