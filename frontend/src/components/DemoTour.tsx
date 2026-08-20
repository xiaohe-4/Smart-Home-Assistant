import { useEffect, useRef, useState } from "react";
import { Button, Modal, Typography, Switch, Space } from "antd";
import { PlayCircleOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";

const STEPS = [
  { title: "第一幕 · 发现问题", path: "/", text: "点击「回放今日」，用电、电费和户型会跟着 24 小时走。今日用电约 18.73 kWh，先看评分和对标。" },
  { title: "第二幕 · 分析原因", path: "/energy", text: "空调约 41%，热水器约 22%，冰箱约 12%。橙色阴影是高峰电价。" },
  { title: "第三幕 · 异常诊断", path: "/anomaly", text: "03:17 热水器异常启动。右侧规则归因说明：时段不合理、占用低、功率偏离。" },
  { title: "第四幕 · 负荷预测", path: "/prediction", text: "XGBoost 给出未来 24 小时预测，绿色带宽是 RMSE 置信区间。" },
  { title: "第五幕 · 智能决策", path: "/strategy", text: "系统已预选 Top 策略：空调升温、热水器定时、高峰错峰。" },
  { title: "第六幕 · 模拟闭环", path: "/strategy", text: "自动执行模拟，对比节电、电费和碳排，形成完整闭环。" },
  { title: "第七幕 · 管家执行", path: "/butler", text: "宝强能听、能说、能拧开关，还能汇报和记偏好。点「汇报一下」再「点头去办」，或直接执行节能方案。" },
  { title: "第八幕 · 生活系统", path: "/life", text: "电价时钟、分人归因、负荷分解和自动化规则。高峰还剩多少分钟，一眼能看见。" },
  { title: "第九幕 · 今晚闭环", path: "/life", text: "电网削峰邀约、今晚任务、谷电预约和凌晨待机猎手。点应邀，宝强会去拧开关。" },
  { title: "第十幕 · 数据从哪来", path: "/sources", text: "电力、环境、行为、天气四路对齐。演示是仿真灌表；勾选缺模态看降级，校验接入合同。" },
  { title: "第十一幕 · 模型实验", path: "/models", text: "预测 R² 0.9525、MAPE 17.52%。负荷识别 0.9513 是有标签窗口分类，不是总表盲拆。异常 F1 0.35 主动展示。特征重要性可解释。" },
];

export default function DemoTour() {
  const nav = useNavigate();
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState(0);
  const [auto, setAuto] = useState(false);
  const timer = useRef<number | null>(null);

  useEffect(() => {
    if (!sessionStorage.getItem("se-tour-seen")) setOpen(true);
  }, []);

  const go = (index: number) => {
    const next = STEPS[index];
    if (!next) return;
    setStep(index);
    if (next.path === "/butler") sessionStorage.setItem("se-butler-cmd", "执行今晚节能方案");
    nav(next.path);
    if (next.path === "/strategy" && index === 5) {
      window.dispatchEvent(new Event("se-autosim"));
    }
  };

  const close = () => {
    sessionStorage.setItem("se-tour-seen", "1");
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
        if (cur >= STEPS.length - 1) {
          setAuto(false);
          return cur;
        }
        const nxt = cur + 1;
        if (STEPS[nxt].path === "/butler") sessionStorage.setItem("se-butler-cmd", "执行今晚节能方案");
        nav(STEPS[nxt].path);
        if (STEPS[nxt].path === "/strategy") window.dispatchEvent(new Event("se-autosim"));
        return nxt;
      });
    }, 4500);
    return () => {
      if (timer.current) window.clearInterval(timer.current);
    };
  }, [auto, open, nav]);

  return (
    <>
      <Button type="primary" icon={<PlayCircleOutlined />} className="tour-fab" onClick={() => { setStep(0); setOpen(true); nav("/"); }}>
        使用演示
      </Button>
      <Modal
        title={STEPS[step].title}
        open={open}
        onCancel={close}
        footer={[
          <Space key="auto"><span>自动播放</span><Switch checked={auto} onChange={setAuto} /></Space>,
          <Button key="skip" onClick={close}>跳过</Button>,
          step > 0 ? <Button key="prev" onClick={() => go(step - 1)}>上一步</Button> : null,
          step < STEPS.length - 1
            ? <Button key="next" type="primary" onClick={() => go(step + 1)}>下一幕</Button>
            : <Button key="done" type="primary" onClick={close}>完成演示</Button>,
        ]}
      >
        <Typography.Paragraph>{STEPS[step].text}</Typography.Paragraph>
        <Typography.Text type="secondary">{step + 1} / {STEPS.length} · 感知 → 诊断 → 决策 → 管家 → 生活系统 → 数据合同 → 模型实验</Typography.Text>
      </Modal>
    </>
  );
}
