import { Button, Card, Collapse, Steps, Tag, Typography } from "antd";
import { useNavigate } from "react-router-dom";

const START = [
  { title: "看今天花了多少", desc: "总览上的用电、电费、碳排和能源评分，就是这户今天的账单摘要。", path: "/", label: "打开总览" },
  { title: "拖时间轴回放", desc: "把滑杆拖到 03:00 看凌晨，再拖回 20:30 看晚高峰。户型和功率会跟着走。", path: "/", label: "去回放" },
  { title: "看谁在耗电", desc: "能耗页按设备拆开。空调大约四成，橙色阴影是高峰电价。", path: "/energy", label: "看能耗" },
  { title: "看异常原因", desc: "点 03:17 那条热水器记录，右侧是规则说明，不是黑盒报警。", path: "/anomaly", label: "看异常" },
  { title: "让管家去办", desc: "对右下角宝强说「执行今晚节能方案」，或先点「汇报一下」再「点头」。", path: "/butler", label: "叫管家" },
];

const PAGES = [
  { path: "/", title: "智能总览", use: "看今日用电、评分、电价时钟和今晚任务。拖动回放，把一天过一遍。" },
  { path: "/energy", title: "能耗分析", use: "看哪台电器占比高，对照高峰时段。占比来自分路电表，不是把总表拆开。" },
  { path: "/devices", title: "家庭设备", use: "点某台设备看今日功率曲线，也可以让管家去拧这台。" },
  { path: "/prediction", title: "能耗预测", use: "看今晚和明天会不会更高。绿色带宽是模型误差，不是保证线。" },
  { path: "/anomaly", title: "异常检测", use: "查不该开却开了的电器。点一条看「为什么算异常」。" },
  { path: "/insights", title: "智能洞察", use: "看电费峰谷结构和能源健康雷达。舒适维按室温计算，不是写死的分数。" },
  { path: "/strategy", title: "AI 节能建议", use: "勾选建议，看节电、电费、碳排前后对比。滑杆越往右越激进。" },
  { path: "/butler", title: "管家宝强", use: "用白话下指令：晚安、出门、空调 26 度。冰箱不会被关掉。" },
  { path: "/life", title: "生活系统", use: "看现在是不是高峰、今晚任务、电网削峰邀约和谷电预约。" },
  { path: "/assistant", title: "能源助手", use: "问「为什么耗电」「电费多少」。它只解释已算好的结果。" },
  { path: "/sources", title: "数据来源", use: "查电从哪来、缺一路数据会怎样、怎样接到下一户。" },
  { path: "/models", title: "模型实验", use: "想核对预测准不准、异常漏报多少，来这里看落盘指标。" },
  { path: "/profile", title: "家庭能源画像", use: "看这户的能效分和每台设备还能省多少。" },
];

const SAY = [
  { cmd: "汇报一下", why: "先听家里现在怎样" },
  { cmd: "执行今晚节能方案", why: "高峰最常用的一键动作" },
  { cmd: "晚安", why: "关灯关电视，掐夜间加热" },
  { cmd: "我出门了", why: "非刚需关掉，冰箱继续转" },
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
    label: "预测准确率 82% 是分类算对了吗？",
    children: "不是。那是 100% 减去平均百分比误差（MAPE）。绿色带宽才是误差有多大。想看完整实验请打开「模型实验」。",
  },
  {
    key: "nilm",
    label: "系统能从总表看出哪台空调吗？",
    children: "演示里的设备占比来自分路计量。负荷识别模型做的是「已有分路标签的功率窗分类」，不是把一块总表盲拆成八台电器。",
  },
  {
    key: "tour",
    label: "右下角「使用演示」和这页有什么区别？",
    children: "使用演示是十一幕自动导览，带你把系统过一遍。本页是文字说明书：先看懂数字，再决定要不要让管家去拧。",
  },
];

export default function Guide() {
  const nav = useNavigate();

  return (
    <div>
      <h1 className="page-title">使用说明</h1>
      <p className="page-sub">给住在这套系统里的人看：今天电花在哪、哪里浪费、今晚让管家做什么。右下角「使用演示」是带练导览，文字说明请从这里上手。</p>

      <Card className="guide-hero" style={{ marginBottom: 16 }}>
        <Tag color="green">家庭用户</Tag>
        <Tag>演示户 · 成都四口 · 2026-08-19 20:30</Tag>
        <Typography.Title level={4} style={{ marginTop: 12 }}>智家能帮您做三件事</Typography.Title>
        <div className="guide-three">
          <div><b>1. 看懂</b><span>今天用了多少度、高峰贵在哪、哪台电器占比高。</span></div>
          <div><b>2. 查清</b><span>凌晨热水器、低占用仍开着的灯，都能追到原因。</span></div>
          <div><b>3. 去办</b><span>勾选节能建议，或对管家说一句话，让它去拧开关。</span></div>
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
          <p className="honesty-note">右下角随时可唤。它能听、能说、能改当前设定，但不会改已经发生的用电历史。不确定时先说「汇报一下」，再「点头」。</p>
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
            <li><b>对标</b>：只和这户近 30 天比，没有编造的「全市平均」。</li>
            <li><b>预测准确率</b>：100 减去百分比误差，不是「猜对了几台电器」。</li>
            <li><b>异常条数</b>：模型会多报，请看规则说明；不要把条数当成准确率。</li>
          </ul>
          <Button onClick={() => nav("/models")}>去模型实验舱核对</Button>
        </Card>
      </div>

      <div className="honesty-note">
        请先知道：当前开关是模拟执行；冰箱拒绝关闭；生活系统里的「谁在用电」不是每人一块表；设备占比来自分路计量。语音仅本机 Chromium 且请使用 http://127.0.0.1:5174/ 。
      </div>

      <Card title="常见问题">
        <Collapse items={FAQ} bordered={false} defaultActiveKey={["demo"]} />
      </Card>
    </div>
  );
}
