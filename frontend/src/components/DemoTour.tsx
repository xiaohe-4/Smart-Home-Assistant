import { useEffect, useRef, useState } from "react";
import { Button, Modal, Typography, Switch, Space } from "antd";
import { PlayCircleOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";

const CORE = [
  { title: "幕 1 · 为何贵", path: "/", text: "点「回放今日」，从早拉到 20:30。看今日电量、第一耗电设备和评分。口播：贵，主要贵在空调。" },
  { title: "幕 2 · 哪笔浪费", path: "/anomaly", text: "拉到 03:17 热水器启动。规则：时段不合理 + 占用低 + 功率偏离。必须说：模型 F1 只有 0.35，结论以规则为准，模型只打分。" },
  { title: "幕 3 · 今晚关哪一档", path: "/strategy", text: "执行空调 24→26℃，看电量/电费/削峰对比。再去管家点头执行，并点一次「关冰箱」被拒绝。现场是模拟控制。" },
];

const ADVANCED = [
  ...CORE,
  { title: "完整 · 能耗结构", path: "/energy", text: "空调约 41%，热水器约 22%。分路汇总，不是总表 NILM。" },
  { title: "完整 · 负荷预测", path: "/prediction", text: "只报 MAE / RMSE / MAPE / R²，和时间序列切分。不用 100-MAPE 当准确率。" },
  { title: "完整 · 生活系统", path: "/life", text: "评委追问页：电价时钟、电网邀约、谷电预约。演示默认不进。" },
  { title: "完整 · 数据对照", path: "/sources", text: "仿真户 vs 验证户。缺模态已降级。不把仿真 R² 当成真实家庭精度。" },
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
        if (steps[nxt].path === "/strategy") window.dispatchEvent(new Event("se-autosim"));
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
        title={steps[step]?.title}
        open={open}
        onCancel={close}
        footer={[
          <Space key="mode"><span>完整导览</span><Switch checked={advanced} onChange={(v) => { setAdvanced(v); setStep(0); }} /></Space>,
          <Space key="auto"><span>自动播放</span><Switch checked={auto} onChange={setAuto} /></Space>,
          <Button key="skip" onClick={close}>跳过</Button>,
          step > 0 ? <Button key="prev" onClick={() => go(step - 1)}>上一步</Button> : null,
          step < steps.length - 1
            ? <Button key="next" type="primary" onClick={() => go(step + 1)}>下一幕</Button>
            : <Button key="done" type="primary" onClick={close}>完成演示</Button>,
        ]}
      >
        <Typography.Paragraph>{steps[step]?.text}</Typography.Paragraph>
        <Typography.Text type="secondary">{step + 1} / {steps.length} · 为何贵 → 哪笔浪费 → 今晚关哪一档</Typography.Text>
      </Modal>
    </>
  );
}
