import { Button, Card, Collapse, Steps, Tag, Typography } from "antd";
import { useNavigate } from "react-router-dom";

const START = [
  { title: "先看今天的账", desc: "总览里把今天拖到 20:30。看电量、电费、哪台最耗电，再点「今晚怎么做」。", path: "/", label: "打开总览" },
  { title: "再看 03:17", desc: "异常页里是凌晨的热水器。模型 F1 只有 0.35，以规则为准。", path: "/anomaly", label: "看异常" },
  { title: "空调从 24 调到 26", desc: "看电费前后差。管家要点头才会去调。说关冰箱，会被拒绝。", path: "/strategy", label: "去执行" },
];

const PAGES = [
  { path: "/", title: "总览", use: "看今天用了多少、评分、现在什么电价。拖动回放，把一天过一遍。" },
  { path: "/energy", title: "能耗分析", use: "看哪台电器占比高，对照高峰时段。占比来自分路电表，不是把总表拆开。" },
  { path: "/devices", title: "家庭设备", use: "点某台设备看今日功率曲线，也可以让管家去调这台。" },
  { path: "/prediction", title: "能耗预测", use: "看今晚和明天会不会更高。绿色带是模型误差，不是保证线。" },
  { path: "/anomaly", title: "用电异常", use: "查不该开却开了的电器。点一条，看它为什么被列出来。" },
  { path: "/insights", title: "用电对照", use: "看峰谷电费和几项分数。舒适那一项按室温算，不是写死的。" },
  { path: "/strategy", title: "节能建议", use: "勾上建议，看节电、电费、碳排前后差多少。滑杆越右，改得越猛。" },
  { path: "/butler", title: "管家宝强", use: "直接说晚安、出门、空调 26 度。冰箱不会关。" },
  { path: "/life", title: "今日安排", use: "看现在是不是高峰、今晚要办的事、电网削峰邀约和谷电预约。" },
  { path: "/assistant", title: "能源助手", use: "问「为什么耗电」「电费多少」。它只解释已算好的结果。" },
  { path: "/sources", title: "数据来源", use: "查电从哪来、缺一路数据会怎样、怎样接到下一户。" },
  { path: "/models", title: "模型实验", use: "想核对预测差多少、异常漏了多少，来这里看存下来的数。" },
  { path: "/profile", title: "家庭概况", use: "看能效评分，以及每台设备还能省多少。" },
];

const SAY = [
  { cmd: "汇报一下", why: "先听家里现在怎样" },
  { cmd: "执行今晚节能方案", why: "高峰最常用的一键动作" },
  { cmd: "晚安", why: "关灯关电视，掐夜间加热" },
  { cmd: "我出门了", why: "别的关掉，冰箱继续转" },
  { cmd: "把空调调到26度", why: "夏天最稳的设定" },
  { cmd: "点头", why: "同意它刚备下的那件事" },
  { cmd: "接受电网邀约", why: "响应削峰，按节能方案执行" },
  { cmd: "恢复原样", why: "这次控制作废，回到日常" },
];

const FAQ = [
  {
    key: "demo",
    label: "这是我家的真实电表吗？",
    children: "当前展示的是成都四口之家的演示数据，日期锁在 2026-08-19 20:30。接入真实电表请打开「数据来源」，按合同校验后再换采集适配器。",
  },
  {
    key: "control",
    label: "我对管家说关灯，曲线为什么没变？",
    children: "管家改的是当前模拟开关和设定温度，方便看「如果现在这样做会怎样」。历史用电记录不会被改写，所以回放曲线仍是当天已经发生的电。",
  },
  {
    key: "fridge",
    label: "为什么不能关冰箱？",
    children: "食品安全底线。说「关掉冰箱」会被拒绝；「只留冰箱」会关掉其他电器，冰箱继续转。",
  },
  {
    key: "voice",
    label: "语音按钮没反应？",
    children: "语音只在本机 Chrome / Edge，并且地址必须是 http://127.0.0.1:5174/ 。用 localhost 的 IPv6 或远程访问时，浏览器往往不给麦克风。也可以直接打字。",
  },
  {
    key: "family",
    label: "爸爸、孩子各用了多少电准吗？",
    children: "那是按占用和房间习惯做的分摊，不是每人一块电表。只能当「谁比较显眼」看，不能当缴费依据。",
  },
  {
    key: "acc",
    label: "预测准不准，看哪个数？",
    children: "看 MAE、RMSE、MAPE 和 R²，外加昨天同时段、近 7 天同时段两条基线。不要把 100 减 MAPE 当成准确率。绿色带宽是误差范围。完整数字在「模型实验」。",
  },
  {
    key: "nilm",
    label: "系统能从总表看出哪台空调吗？",
    children: "演示里的设备占比来自分路计量。负荷识别模型做的是「已有分路标签的功率窗分类」，不是把一块总表盲拆成八台电器。",
  },
  {
    key: "tour",
    label: "右下角「3 分钟演示」和这页有什么区别？",
    children: "演示默认三幕：今天为什么贵、03:17、空调调到 26℃。打开「完整导览」才会走到其余页面。本页是文字说明书。",
  },
];

export default function Guide() {
  const nav = useNavigate();

  return (
    <div>
      <div className="scene-banner">
        <div>
          <h1 className="page-title">使用说明</h1>
          <p className="page-sub">先看今天用了多少、哪一笔不该开。右下角「3 分钟演示」带着走三幕，文字在这一页。</p>
        </div>
      </div>

      <Card className="guide-hero" style={{ marginBottom: 16 }}>
        <Tag color="green">家庭用户</Tag>
        <Tag>演示家庭 · 成都四口 · 2026-08-19 20:30</Tag>
        <Typography.Title level={4} style={{ marginTop: 12 }}>先看数，再决定要不要调</Typography.Title>
        <div className="guide-three">
          <div><b>今天的账</b><span>电量、电费，以及哪台占比高。</span></div>
          <div><b>03:17 热水器</b><span>不该开的会列出来，点开能看到原因。</span></div>
          <div><b>要关的话</b><span>去节能建议里勾，或叫宝强。冰箱不会关。</span></div>
        </div>
      </Card>

      <Card title="五分钟上手" extra={<Button type="link" onClick={() => nav("/")}>从总览开始</Button>} style={{ marginBottom: 16 }}>
        <Steps
          direction="vertical"
          items={START.map((s) => ({
            title: s.title,
            description: (
              <div className="guide-step">
                <span>{s.desc}</span>
                <Button size="small" onClick={() => nav(s.path)}>{s.label}</Button>
              </div>
            ),
          }))}
        />
      </Card>

      <h2 className="guide-h2">各页能做什么</h2>
      <div className="guide-map">
        {PAGES.map((p) => (
          <button key={p.path + p.title} className="guide-card" type="button" onClick={() => nav(p.path)}>
            <b>{p.title}</b>
            <span>{p.use}</span>
          </button>
        ))}
      </div>

      <div className="two-col" style={{ marginBottom: 16 }}>
        <Card title="管家宝强怎么喊">
          <div className="guide-butler">
            <img className="butler-portrait inline" src="/art/butler.jpg" alt="" />
            <p className="honesty-note">右下角随时可以叫它。它改的是现在的开关，改不了已经发生的用电。拿不准就先说「汇报一下」，再说「点头」。</p>
          </div>
          <div className="guide-say">
            {SAY.map((s) => (
              <div key={s.cmd}>
                <code>{s.cmd}</code>
                <span>{s.why}</span>
              </div>
            ))}
          </div>
          <Button type="primary" style={{ marginTop: 12 }} onClick={() => {
            sessionStorage.setItem("se-butler-cmd", "汇报一下");
            nav("/butler");
          }}>打开管家并先汇报</Button>
        </Card>
        <Card title="数字怎么读">
          <ul className="guide-list">
            <li><b>峰 / 平 / 谷</b>：演示电价 0.72 / 0.52 / 0.28 元。18:00–22:00 是高峰，能挪的事尽量挪走。</li>
            <li><b>能源评分</b>：越高越好，扣的是峰值、异常和浪费，不是全市排名。</li>
            <li><b>对照</b>：只和自家近 30 天比，没有编造的「全市平均」。</li>
            <li><b>预测</b>：只看 MAE、RMSE、MAPE、R²。不要把 100 减 MAPE 说成准确率。</li>
            <li><b>异常条数</b>：模型会多报，请看规则说明；不要把条数当成准确率。</li>
          </ul>
          <Button onClick={() => nav("/models")}>去模型实验看数字</Button>
        </Card>
      </div>

      <div className="honesty-note">
        请先知道：开关是模拟的，不会改已经发生的用电；冰箱不能关；今日安排里的「谁在用电」不是每人一块电表；各电器占比来自分路电表。语音只支持本机 Chrome 或 Edge，请用 http://127.0.0.1:5174/ 。
      </div>

      <Card title="常见问题">
        <Collapse items={FAQ} bordered={false} defaultActiveKey={["demo"]} />
      </Card>
    </div>
  );
}
