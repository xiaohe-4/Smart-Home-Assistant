# 「智家能」技术实现说明书

> 项目名称：**智家能——基于多模态家庭数据分析的 AI 能源管理与节能决策系统**
>
> 文档用途：**直接交给 Cursor 作为项目开发规格说明书**
>
> 开发目标：在 **10 天内完成一个可运行、可演示、可答辩的 MVP**。优先保证核心闭环完整，不追求过度复杂的硬件和模型。

---

# 1. 项目定位

## 1.1 项目目标

构建一个面向普通家庭的 AI 能源管理系统，通过融合：

- 家庭电力时序数据
- 家庭环境数据
- 家庭设备状态数据
- 家庭成员行为/活动数据
- 时间、天气等外部数据

实现：

1. 家庭实时能耗监测
2. 家庭能源数据可视化
3. 家庭能源画像
4. 家庭能耗预测
5. 异常能耗检测
6. 家电能耗分析
7. 家庭节能潜力评估
8. AI 节能策略推荐
9. 节能效果模拟

核心产品闭环：

```text
多模态数据采集
      ↓
数据清洗与融合
      ↓
家庭能源状态建模
      ↓
能耗分析
      ↓
能耗预测 + 异常检测
      ↓
节能潜力评估
      ↓
AI 节能决策
      ↓
用户执行
      ↓
节能效果反馈
      ↓
形成新的家庭能源画像
```

---

# 2. MVP 原则

## 2.1 10 天开发原则

必须遵守：

- 优先实现完整业务闭环
- 优先保证系统可以启动
- 优先保证前端可以演示
- 优先保证核心算法有真实输出
- 数据允许使用高质量模拟数据
- 模型可以使用成熟机器学习算法
- 不要求自研大模型
- 不要求自研智能电表
- 不要求真正控制家庭电器
- 不要求复杂 IoT 硬件
- 不要为了“多模态”强行增加硬件

## 2.2 必须完成的功能

### P0 核心功能

- [ ] 家庭能耗数据生成/导入
- [ ] 数据库存储
- [ ] 实时/历史能耗曲线
- [ ] 今日/本月能耗统计
- [ ] 家庭能源画像
- [ ] 能耗预测
- [ ] 异常能耗检测
- [ ] 节能潜力分析
- [ ] AI 节能建议
- [ ] Web 可视化 Dashboard

### P1 增强功能

- [ ] 家电能耗分解
- [ ] 环境数据关联分析
- [ ] 用户行为数据关联
- [ ] 节能策略模拟
- [ ] 节能前后效果对比
- [ ] AI 能源助手

### P2 暂缓功能

- [ ] 真正智能电表
- [ ] MQTT
- [ ] 智能插座硬件
- [ ] 手机原生 App
- [ ] 自动控制真实家电
- [ ] 复杂强化学习
- [ ] 大模型微调
- [ ] Transformer 从零训练

---

# 3. 系统总体架构

```text
┌──────────────────────────────────────────────────────┐
│                    智家能 Web 前端                   │
│ React + TypeScript + ECharts                         │
└──────────────────────┬───────────────────────────────┘
                       │ REST API
                       ▼
┌──────────────────────────────────────────────────────┐
│                    FastAPI 后端                       │
├──────────────────────────────────────────────────────┤
│ 用户服务 │ 能耗服务 │ 预测服务 │ 异常检测 │ 策略服务 │
└──────────────────────┬───────────────────────────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
     PostgreSQL      AI Engine     Data Pipeline
          │            │            │
          │       ┌────┼────┐       │
          │       ▼    ▼    ▼       │
          │    XGBoost IForest NILM │
          │                         │
          └────────────┬────────────┘
                       ▼
                  数据分析结果
```

---

# 4. 推荐技术栈

## 4.1 前端

- React
- TypeScript
- Vite
- ECharts
- Axios
- Ant Design 或 Tailwind CSS

推荐：

```text
React + TypeScript + Vite + ECharts + Ant Design
```

## 4.2 后端

- Python 3.11+
- FastAPI
- Pydantic
- SQLAlchemy
- Uvicorn

## 4.3 AI / 数据分析

- NumPy
- Pandas
- Scikit-learn
- XGBoost
- PyTorch（仅在需要时使用）

核心模型：

```text
能耗预测：XGBoost
异常检测：Isolation Forest
设备能耗识别：规则 + Random Forest/XGBoost
节能策略：规则引擎 + 优化评分
```

## 4.4 数据库

优先：

```text
PostgreSQL
```

如果开发初期部署困难：

```text
SQLite
```

但代码必须通过 ORM 设计，方便后续切换 PostgreSQL。

## 4.5 部署

开发阶段：

```text
Frontend: localhost:5173
Backend: localhost:8000
Database: localhost:5432
```

最终可选：

```text
Docker Compose
```

---

# 5. 项目目录

建议 Cursor 严格按照以下结构创建：

```text
smart-energy/
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── layouts/
│   │   ├── pages/
│   │   │   ├── Dashboard/
│   │   │   ├── Energy/
│   │   │   ├── Devices/
│   │   │   ├── Prediction/
│   │   │   ├── Anomaly/
│   │   │   ├── Strategy/
│   │   │   └── Profile/
│   │   ├── hooks/
│   │   ├── stores/
│   │   ├── types/
│   │   └── utils/
│   ├── package.json
│   └── vite.config.ts
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── database.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── api/
│   │   │   ├── energy.py
│   │   │   ├── devices.py
│   │   │   ├── prediction.py
│   │   │   ├── anomaly.py
│   │   │   ├── strategy.py
│   │   │   └── profile.py
│   │   ├── services/
│   │   └── utils/
│   └── requirements.txt
│
├── ai/
│   ├── forecasting/
│   │   ├── train.py
│   │   ├── predict.py
│   │   └── model.py
│   ├── anomaly_detection/
│   │   ├── train.py
│   │   └── detector.py
│   ├── load_identification/
│   │   └── classifier.py
│   ├── profiling/
│   │   └── profile.py
│   └── optimization/
│       └── strategy_engine.py
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── demo/
│
├── scripts/
│   ├── generate_demo_data.py
│   ├── init_db.py
│   └── train_models.py
│
├── models/
│
├── tests/
│
├── docs/
│
├── docker-compose.yml
├── README.md
└── .env.example
```

---

# 6. 数据模型

## 6.1 users

```text
id
name
household_size
home_type
created_at
```

## 6.2 devices

```text
id
user_id
name
device_type
rated_power
status
created_at
```

设备类型：

```text
air_conditioner
refrigerator
water_heater
washing_machine
television
lighting
computer
other
```

## 6.3 energy_records

```text
id
user_id
device_id
timestamp
power
voltage
current
energy
```

说明：

- power：当前功率，单位 W
- voltage：电压，单位 V
- current：电流，单位 A
- energy：累计/区间耗电量，单位 kWh

## 6.4 environment_records

```text
id
user_id
timestamp
temperature
humidity
light
co2
```

## 6.5 behavior_records

```text
id
user_id
timestamp
location
occupancy
activity
```

activity 示例：

```text
sleeping
working
cooking
watching_tv
leaving_home
returning_home
resting
```

## 6.6 weather_records

```text
id
timestamp
temperature
humidity
weather
wind_speed
```

## 6.7 predictions

```text
id
user_id
timestamp
horizon
predicted_power
actual_power
model_name
model_version
```

## 6.8 anomalies

```text
id
user_id
timestamp
device_id
anomaly_score
anomaly_type
description
severity
status
```

severity：

```text
low
medium
high
critical
```

## 6.9 strategies

```text
id
user_id
strategy_type
title
description
estimated_saving_kwh
estimated_saving_percent
comfort_impact
feasibility
score
created_at
```

---

# 7. 多模态数据设计

“多模态”不强制等于图像、音频、文本。

本项目 MVP 中将家庭数据分为：

## 模态 A：电力时序

```text
功率
电压
电流
设备状态
时间
```

## 模态 B：环境

```text
室内温度
湿度
光照
CO₂
室外温度
天气
```

## 模态 C：行为

```text
是否有人
所在房间
活动类型
回家/离家
睡眠
工作
```

## 模态 D：外部因素

```text
日期
星期
小时
季节
天气
电价
```

最终特征：

```text
X =
[
  power_history,
  temperature,
  humidity,
  occupancy,
  hour,
  weekday,
  weather,
  device_state
]
```

---

# 8. Demo 数据生成

由于 10 天时间限制，必须提供高质量模拟数据。

脚本：

```text
scripts/generate_demo_data.py
```

要求生成至少：

```text
30 天
5 分钟粒度
1 个家庭
8 类家电
环境数据
行为数据
天气数据
```

理论数据量：

```text
30 × 24 × 12 = 8640 个时间点
```

每个时间点包含：

- 总功率
- 各设备功率
- 温度
- 湿度
- 人员状态
- 时间特征

---

# 9. 数据生成规则

模拟数据不能完全随机。

必须体现真实家庭规律。

例如空调：

```text
夏季
白天温度高
18:00-23:30 使用概率高
室内温度越高，功率越高
```

冰箱：

```text
全天工作
周期性启停
```

热水器：

```text
06:30-08:00
18:00-22:00
概率较高
```

洗衣机：

```text
19:00-22:00
使用概率较高
```

照明：

```text
06:30-07:30
18:00-23:30
使用概率较高
```

电视：

```text
19:00-23:00
```

电脑：

```text
08:00-18:00
或者19:00-23:00
```

同时人为植入：

```text
异常高耗电
异常设备启动
异常长时间运行
```

用于异常检测 Demo。

---

# 10. 能耗预测模块

## 10.1 目标

预测：

```text
未来 1 小时
未来 6 小时
未来 24 小时
```

优先实现：

```text
未来 1 小时
```

## 10.2 特征

使用：

```text
lag_1
lag_2
lag_3
lag_6
lag_12
lag_24

rolling_mean_1h
rolling_mean_3h
rolling_mean_6h
rolling_mean_24h

temperature
humidity
occupancy

hour
weekday
is_weekend
```

## 10.3 模型

第一版本：

```text
XGBoostRegressor
```

如果 XGBoost 环境存在问题：

```text
RandomForestRegressor
```

## 10.4 评价指标

必须输出：

```text
MAE
RMSE
MAPE
R²
```

前端展示：

```text
预测准确率
MAE
RMSE
```

注意：

不要伪造实验指标。

所有指标必须来自真实运行结果。

---

# 11. 异常检测模块

## 11.1 目标

发现：

- 异常高功率
- 异常时间用电
- 设备长时间运行
- 与历史习惯不一致的用电

## 11.2 模型

使用：

```text
IsolationForest
```

输入：

```text
power
rolling_mean
rolling_std
hour
weekday
temperature
occupancy
```

输出：

```text
anomaly_score
```

转换为：

```text
normal
low
medium
high
```

## 11.3 示例

如果发现：

```text
03:17
water_heater
1200W
```

且家庭过去30天凌晨从未使用热水器：

系统生成：

```text
异常类型：
异常时段启动

严重程度：
medium

建议：
检查热水器是否存在待机/定时启动行为。
```

---

# 12. 家电能耗识别

MVP 可以不做复杂 NILM。

优先采用：

```text
规则 + 功率特征 + RandomForest
```

特征：

```text
平均功率
峰值功率
运行时间
功率波动
启动时间
周期特征
```

设备类别：

```text
空调
冰箱
热水器
洗衣机
电视
照明
电脑
其他
```

最终输出：

```text
设备
今日耗电
占比
运行时间
```

---

# 13. 家庭能源画像

每日自动生成。

指标：

```text
今日用电
昨日用电
本周平均
本月累计
最高功率
峰值时间
主要耗能设备
能源效率
节能潜力
```

能源效率评分：

```text
energy_score =
100
- abnormal_penalty
- peak_penalty
- waste_penalty
```

最终限制：

```text
0 <= score <= 100
```

示例：

```text
能源效率：82/100
今日用电：18.42 kWh
较昨日：-12.4%
较7日平均：+3.2%
主要耗能：空调
节能潜力：8.7%
```

---

# 14. 节能潜力评估

针对每一个设备计算：

```text
saving_potential =
baseline_energy - optimized_energy
```

例如：

```text
空调
当前：
10.2 kWh/day

优化后：
8.7 kWh/day

潜在节约：
1.5 kWh/day
```

全家庭：

```text
total_saving =
Σ device_saving
```

---

# 15. AI 节能决策引擎

## 15.1 原则

不要简单输出：

> “请节约用电。”

必须输出：

```text
问题
+
原因
+
建议
+
预计收益
+
用户影响
```

## 15.2 策略示例

### 策略 A

```text
空调温度从 24℃ → 26℃
```

### 策略 B

```text
热水器从全天待机 → 定时运行
```

### 策略 C

```text
离家后关闭非必要照明
```

### 策略 D

```text
高峰时段减少非必要高功率设备运行
```

---

# 16. 策略评分算法

每个策略：

```text
score =
saving_benefit
× feasibility
× user_acceptance
- comfort_penalty
```

其中：

```text
saving_benefit：预计节能收益
feasibility：执行难度
user_acceptance：用户接受度
comfort_penalty：舒适度影响
```

最终排序：

```text
score DESC
```

前端显示前三条建议。

---

# 17. 不使用大模型也可以完成核心 AI

重要要求：

**不要为了“AI”强行接入大模型。**

核心 AI：

```text
XGBoost
+
Isolation Forest
+
Random Forest
+
规则决策
```

已经足够。

如果时间允许，可以增加一个可选：

```text
LLM Energy Assistant
```

负责把结构化分析结果转换成自然语言。

例如输入：

```json
{
  "today_energy": 18.42,
  "main_device": "air_conditioner",
  "saving_potential": 8.7,
  "anomaly": "water_heater_at_03_17"
}
```

输出：

```text
今天家庭用电主要来自空调，占总用电约42%。
系统发现热水器凌晨出现异常启动行为。
预计通过调整空调运行策略并优化热水器定时设置，
本月可降低约8.7%的能源消耗。
```

注意：

LLM 只能负责解释和交互。

**不能负责核心数值计算。**

---

# 18. API 设计

## 能耗

```http
GET /api/energy/today
GET /api/energy/history
GET /api/energy/hourly
GET /api/energy/summary
```

## 设备

```http
GET /api/devices
GET /api/devices/{id}
GET /api/devices/{id}/energy
```

## 预测

```http
GET /api/prediction/hour
GET /api/prediction/day
```

## 异常

```http
GET /api/anomalies
GET /api/anomalies/latest
```

## 策略

```http
GET /api/strategies
GET /api/strategies/top
POST /api/strategies/simulate
```

## 家庭画像

```http
GET /api/profile
GET /api/profile/energy-score
GET /api/profile/saving-potential
```

---

# 19. Dashboard 页面

首页必须做到“一眼看懂”。

布局：

```text
┌─────────────────────────────────────────────┐
│ 智家能                         今日 08-19    │
├──────────┬──────────┬──────────┬────────────┤
│ 今日用电 │ 能源评分 │ 节能潜力 │ 当前功率   │
│18.42kWh │ 82/100   │ 8.7%     │ 1.28kW    │
├──────────┴──────────┴──────────┴────────────┤
│                                             │
│              家庭实时能耗曲线               │
│                                             │
├──────────────────────┬──────────────────────┤
│ 设备能耗占比          │ AI异常检测           │
│ 饼图                  │ 异常列表             │
├──────────────────────┼──────────────────────┤
│ 能耗预测              │ AI节能建议           │
│ 折线图                │ Top 3策略            │
└──────────────────────┴──────────────────────┘
```

---

# 20. 页面设计

至少实现 6 个页面：

## Dashboard

核心总览。

## Energy

历史能耗分析。

包含：

- 日
- 周
- 月
- 设备
- 峰谷

## Devices

家庭设备列表。

展示：

```text
设备
当前状态
今日耗电
运行时间
占家庭耗电比例
```

## Prediction

展示：

```text
历史真实值
+
未来预测值
```

## Anomaly

展示：

```text
异常时间
设备
异常类型
严重程度
建议
```

## Strategy

展示：

```text
AI推荐
预计节能
执行难度
舒适度影响
```

---

# 21. 前端视觉要求

整体风格：

```text
科技感
简洁
专业
绿色低碳
```

不要做成：

```text
炫酷电竞风
```

建议：

- 白色/浅灰背景
- 绿色作为主要强调色
- 深色文字
- 卡片式 Dashboard
- 大数字指标
- ECharts 数据图
- 清晰的信息层级

---

# 22. Demo 场景必须预设

比赛 Demo 不要随机操作。

固定一个故事：

## 场景

```text
一个四口之家
夏季
成都
```

系统已经运行 30 天。

---

## Demo 第一幕

展示：

```text
今日家庭用电
18.42 kWh
```

---

## 第二幕

点击“能耗分析”。

发现：

```text
空调：
42%

热水器：
21%

冰箱：
12%
```

---

## 第三幕

点击“异常检测”。

发现：

```text
03:17
热水器异常启动
```

---

## 第四幕

点击“能耗预测”。

展示：

```text
未来6小时预计能耗
```

---

## 第五幕

点击“AI节能建议”。

显示：

```text
建议 1
空调 24℃ → 26℃
预计节约 8.4%

建议 2
优化热水器运行时间
预计节约 3.2%

建议 3
减少高峰期非必要设备运行
预计节约 2.1%
```

---

## 第六幕

点击“模拟优化”。

展示：

```text
优化前：
18.42 kWh

优化后：
16.81 kWh

预计节约：
8.74%
```

这就是完整的：

```text
发现问题
→
分析原因
→
预测
→
提出策略
→
模拟效果
```

---

# 23. 实验指标

为了比赛答辩，需要至少准备三组实验。

## 实验 1：能耗预测

指标：

```text
MAE
RMSE
MAPE
R²
```

## 实验 2：异常检测

指标：

```text
Precision
Recall
F1
```

## 实验 3：节能策略模拟

对比：

```text
优化前
优化后
节约比例
```

**所有指标必须由真实程序计算，不允许手工编造。**

---

# 24. 测试要求

后端：

```text
pytest
```

至少测试：

- 数据生成
- API
- 数据库 CRUD
- 能耗统计
- 预测接口
- 异常检测
- 策略生成

前端：

至少保证：

- 页面正常加载
- API 请求失败有提示
- 图表无数据时有空状态
- 手机/桌面基本可用

---

# 25. 工程要求

Cursor 开发时必须遵守：

1. 不要一次生成整个项目。
2. 每完成一个模块立即运行测试。
3. 优先实现 P0。
4. 不要留下大量 TODO。
5. 不要使用伪 API。
6. 不要把核心业务逻辑全部写在前端。
7. AI 模型必须可以真实运行。
8. 数据库模型必须真实可用。
9. API 必须有明确 schema。
10. 所有关键参数集中配置。
11. 不要硬编码大量业务数据。
12. Demo 数据必须由脚本生成。
13. README 必须包含完整启动方法。
14. 保证 Windows 环境可以开发和运行。
15. 如果某个技术方案过于复杂，优先选择简单可靠的替代方案。

---

# 26. 开发顺序

严格按照下面顺序执行。

## Phase 1：项目初始化

- [ ] 创建项目
- [ ] 初始化 Git
- [ ] 初始化 FastAPI
- [ ] 初始化 React
- [ ] 配置数据库
- [ ] 创建环境变量
- [ ] 创建 README

## Phase 2：数据

- [ ] 创建数据库模型
- [ ] 创建 Demo 数据生成器
- [ ] 生成 30 天数据
- [ ] 数据导入数据库
- [ ] 验证数据

## Phase 3：后端

- [ ] 能耗 API
- [ ] 设备 API
- [ ] 预测 API
- [ ] 异常 API
- [ ] 策略 API
- [ ] 家庭画像 API

## Phase 4：AI

- [ ] XGBoost 能耗预测
- [ ] Isolation Forest 异常检测
- [ ] 设备能耗分析
- [ ] 能源画像
- [ ] 节能潜力
- [ ] 策略推荐

## Phase 5：前端

- [ ] Dashboard
- [ ] Energy
- [ ] Devices
- [ ] Prediction
- [ ] Anomaly
- [ ] Strategy

## Phase 6：联调

- [ ] 前后端连接
- [ ] API 调试
- [ ] 图表验证
- [ ] AI结果验证

## Phase 7：Demo

- [ ] 固定 Demo 数据
- [ ] 固定 Demo 流程
- [ ] 优化 UI
- [ ] 增加加载动画
- [ ] 增加错误提示
- [ ] 准备演示账号

## Phase 8：比赛材料

- [ ] 产品介绍
- [ ] 技术架构图
- [ ] 创新点
- [ ] 实验结果
- [ ] Demo 视频
- [ ] PPT
- [ ] 答辩稿

---

# 27. 10 天开发计划

## Day 1

目标：

> 项目能够启动。

完成：

- 项目初始化
- React
- FastAPI
- 数据库
- 基础页面
- Git

---

## Day 2

目标：

> 数据跑起来。

完成：

- 数据库模型
- Demo 数据生成
- 数据导入
- 能耗 API

---

## Day 3

目标：

> Dashboard 能看到真实数据。

完成：

- Dashboard
- 能耗曲线
- 设备统计
- 今日数据
- 本周数据

---

## Day 4

目标：

> AI预测跑起来。

完成：

- 特征工程
- XGBoost
- 训练
- 保存模型
- Prediction API
- 前端预测页面

---

## Day 5

目标：

> 异常检测跑起来。

完成：

- Isolation Forest
- 异常数据
- Anomaly API
- 异常页面

---

## Day 6

目标：

> AI节能决策跑起来。

完成：

- 节能潜力计算
- 策略规则
- 策略评分
- Strategy API
- Strategy 页面

---

## Day 7

目标：

> 完成完整系统。

完成：

- 家庭画像
- 设备页面
- 能耗分析
- 所有 API 联调

---

## Day 8

目标：

> 产品化。

完成：

- UI 优化
- 图表优化
- 首页重构
- Demo 数据
- Logo/项目视觉

---

## Day 9

目标：

> 比赛演示。

完成：

- Demo 流程
- 演示视频
- 技术架构图
- 实验数据
- PPT

---

## Day 10

目标：

> 只做稳定性。

完成：

- Bug 修复
- 压力测试
- Demo 排练
- 答辩模拟
- 备份项目

**Day 10 禁止增加重大新功能。**

---

# 28. Cursor 开发指令

将本文件作为项目规格说明书后，对 Cursor 下达以下总指令：

```text
你现在是本项目的高级全栈工程师 + AI工程师。

请严格按照 docs/TECHNICAL_SPEC.md 开发“智家能——基于多模态家庭数据分析的AI能源管理与节能决策系统”。

开发原则：

1. 先检查当前项目结构。
2. 不要一次性生成所有代码。
3. 按 Phase 1 → Phase 8 顺序开发。
4. 每完成一个阶段都运行测试。
5. 优先保证 P0 功能。
6. 所有核心 AI 功能必须真实运行。
7. 不允许使用伪造 API、伪造预测结果或硬编码实验指标。
8. Demo 数据可以模拟，但必须通过 scripts/generate_demo_data.py 生成。
9. 所有模型必须保存到 models/。
10. 前后端通过 REST API 通信。
11. 数据库通过 SQLAlchemy ORM 访问。
12. API 使用 Pydantic Schema。
13. 所有环境变量放在 .env。
14. 不要把数据库密码、API Key 等写入代码。
15. Windows 环境必须可以启动。
16. 如果 PostgreSQL 环境暂时不可用，允许使用 SQLite 完成开发，但必须保持 ORM 兼容性。
17. UI 必须简洁、专业、具有科技感和绿色低碳视觉特征。
18. Dashboard 必须能够完整展示：
    - 今日用电
    - 能源评分
    - 节能潜力
    - 当前功率
    - 家庭实时能耗
    - 设备能耗
    - 能耗预测
    - 异常检测
    - AI节能建议
19. 不要为了技术复杂度而复杂化。
20. 任何时候如果复杂方案会影响10天内完成，优先采用可靠的简单方案。

现在不要直接开发全部功能。

第一步：
检查当前项目目录和环境。

然后告诉我：
1. 当前环境有什么；
2. 缺少什么；
3. Phase 1 应该做什么；
4. 准备修改哪些文件。

等待确认后再开始第一阶段。
```

---

# 29. 最终产品必须形成的技术闭环

最终系统必须能够回答三个问题：

### 问题 1

> 为什么我家耗电？

通过：

```text
多模态数据
+
设备分析
+
行为分析
```

解决。

### 问题 2

> 哪些地方在浪费？

通过：

```text
异常检测
+
历史基线
+
能耗预测
```

解决。

### 问题 3

> 我应该怎么节能？

通过：

```text
节能潜力评估
+
策略评分
+
AI决策
```

解决。

最终形成：

```text
             感知
              ↓
             分析
              ↓
             预测
              ↓
             诊断
              ↓
             决策
              ↓
             优化
              ↓
             反馈
              └──────→ 持续学习
```

---

# 30. 项目最终技术卖点

最终答辩时不要简单说：

> “这是一个 AI 智能家居系统。”

应该定义为：

> **智家能是一套面向家庭场景的多模态能源智能决策系统。系统融合家庭电力、环境、设备和行为数据，通过机器学习完成家庭能耗预测、异常用能识别和能源画像，并进一步评估家庭节能潜力，生成兼顾节能收益与用户舒适度的个性化节能策略，实现从“能源监测”到“智能决策”的升级。**

核心技术链：

```text
多模态数据融合
        ↓
时序特征工程
        ↓
XGBoost 能耗预测
        ↓
Isolation Forest 异常检测
        ↓
家庭能源画像
        ↓
节能潜力建模
        ↓
多目标策略评分
        ↓
AI节能决策
```

---

# 31. 当前最高优先级

现在不要继续扩展技术方案。

按照以下优先级执行：

```text
★★★★★
项目能启动

★★★★★
数据库 + Demo数据

★★★★★
Dashboard

★★★★★
能耗预测

★★★★★
异常检测

★★★★★
节能策略

★★★★☆
设备识别

★★★☆☆
LLM助手

★☆☆☆☆
硬件
```

**10天版本的成功标准不是“技术最复杂”，而是：**

> **真实数据/模拟数据 → AI分析 → 发现问题 → 给出策略 → 模拟节能效果 → 完整可视化**

只要这个闭环真正跑通，项目就具备比赛 Demo 的核心骨架。
