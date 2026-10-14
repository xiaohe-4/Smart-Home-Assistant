import { useEffect, useState } from "react";
import { Button, Card, Input, Space, Typography } from "antd";
import { insightApi } from "../api";

const presets = ["为什么我家耗电？", "哪些地方在浪费？", "我应该怎么节能？", "今天电费多少？", "碳排放怎么样？", "今天比近 30 日中位高吗？", "有没有电网削峰邀约？", "凌晨谁在偷电？", "数据从哪来？能移植吗？", "预测准不准？", "负荷识别是 NILM 吗？", "怎么用这套系统？"];

export default function Assistant() {
  const [question, setQuestion] = useState("为什么我家耗电？");
  const [messages, setMessages] = useState<Array<{ role: "user" | "ai"; text: string }>>([
    { role: "ai", text: "我是智家能能源助手。我会用家庭电力、环境、占用和策略计算结果回答，不编造指标。" },
  ]);
  const [loading, setLoading] = useState(false);

  const ask = async (q: string) => {
    const text = q.trim();
    if (!text) return;
    setMessages((prev) => [...prev, { role: "user", text }]);
    setLoading(true);
    try {
      const res = await insightApi.chat(text);
      setMessages((prev) => [...prev, { role: "ai", text: res.answer }]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const queued = sessionStorage.getItem("se-ask");
    if (queued) {
      sessionStorage.removeItem("se-ask");
      setQuestion(queued);
      void ask(queued);
    }
  }, []);

  return (
    <div>
      <h1 className="page-title">能源助手</h1>
      <p className="page-sub">问为什么耗电、电费多少。数字是算好的，这里只是把它说出来。</p>
      <Card>
        <Space wrap style={{ marginBottom: 16 }}>
          {presets.map((p) => (
            <Button key={p} onClick={() => { setQuestion(p); ask(p); }}>{p}</Button>
          ))}
        </Space>
        <div style={{ minHeight: 280 }}>
          {messages.map((m, i) => (
            <div key={i} className={m.role === "ai" ? "assistant-bubble" : "user-bubble"}>{m.text}</div>
          ))}
        </div>
        <Space.Compact style={{ width: "100%", marginTop: 12 }}>
          <Input value={question} onChange={(e) => setQuestion(e.target.value)} onPressEnter={() => ask(question)} placeholder="例如：今晚高峰会不会更高？" />
          <Button type="primary" loading={loading} onClick={() => ask(question)}>发送</Button>
        </Space.Compact>
        <Typography.Text type="secondary">助手只解释已计算的结果，不会替代 XGBoost / Isolation Forest。</Typography.Text>
      </Card>
    </div>
  );
}
