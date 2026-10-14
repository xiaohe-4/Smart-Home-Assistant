# 智家能——基于多模态家庭数据分析的 AI 能源管理与节能决策系统

给家庭今晚一张「该关什么」的执行单，并能模拟执行后的电费变化。演示户是仿真（稳定打出 03:17）；验证户走公开负荷风格/真实导出，缺模态已降级。

三句边界：演示含仿真；负荷识别不是 NILM；异常 F1=0.35，上线以规则为准。

演示家庭：成都四口之家 · 夏季 · 已连续运行 30 天 · 演示时刻 2026-08-19 20:30。

## 功能

- 家庭实时/历史能耗、分路分解、峰谷电费与碳排
- XGBoost 能耗预测（R² / MAE / RMSE / MAPE 全部来自训练落盘）
- Isolation Forest + 规则异常检测（Precision / Recall / F1 诚实展示）
- 有标签窗口的负荷识别（RandomForest，**不是**总表盲拆 NILM）
- 家庭能源画像、多目标节能策略与优化前后模拟
- 管家宝强：场景、点头确认、记忆偏好、模拟控制
- 生活系统：电价时钟、今晚任务、电网削峰邀约、谷电预约
- 数据来源页：四路对齐、缺模态降级、接入合同校验
- 模型实验舱：特征重要性与实验指标一页讲清

## 技术栈

- 前端：React + TypeScript + Vite + Ant Design + ECharts
- 后端：Python + FastAPI + SQLAlchemy + Pydantic
- AI：NumPy / Pandas / Scikit-learn / XGBoost（若环境不支持则自动回退 RandomForest）
- 数据库：默认 SQLite，可切换 PostgreSQL

## Windows 快速启动

在项目根目录执行：

```powershell
# Windows 若 python 不在 PATH，把下面的 python 换成 py -3
python -m pip install -r backend\requirements.txt

python scripts\generate_demo_data.py
python scripts\init_db.py
python scripts\train_models.py
# 或一步完成：python scripts\bootstrap.py

# 启动后端（新终端；改 Python 后必须重启，不要只靠 --reload）
$env:PYTHONPATH = "$pwd\backend;$pwd"
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
# 也可：.\scripts\start_backend.ps1

# 启动前端（新终端）
cd frontend
npm install
npm run dev
```

然后打开：

- 前端：http://127.0.0.1:5174/
- 后端 API 文档：http://127.0.0.1:8000/docs

不要用 `localhost` 的 IPv6 地址，也不要把中文和 URL 写在同一条可点击链接里。演示账号无需登录，默认 Demo 家庭（user_id=1，演示日 2026-08-19）。

家庭用户入口请打开：http://127.0.0.1:5174/guide （侧栏和顶栏都有「使用说明」）。

如果 `xgboost` 安装失败，可忽略。训练脚本会自动使用 `RandomForestRegressor`。

## 真实实验指标（勿口头编造）

来源：`models/metrics.json`，训练日 2026-08-19。

| 实验 | 指标 |
| --- | --- |
| 能耗预测 XGBoost（演示户） | 以 `models/metrics.json` 为准；只报 MAE/RMSE/MAPE/R²，并对照昨天同时段与近 7 日同时段平均 |
| 异常检测 规则主+IF 辅 | Precision 0.2593 · Recall 0.5385 · F1 0.35 · 标注 13 / 检出 27 |
| 负荷识别 RF | Accuracy 0.9513 · macro-F1 0.9515（有分路标签的 1 小时窗分类，不是总表 NILM） |
| 演示日用电 | 18.73 kWh；空调 41.3%、热水器 22.3%、冰箱 11.8% |

## 目录

```text
frontend/     Web 可视化
backend/      FastAPI 服务
ai/           预测、异常、画像、策略引擎
scripts/      数据生成、入库、训练
data/demo/    生成的 Demo 数据
models/       训练后的模型与指标
tests/        pytest
docs/         比赛与技术文档
```

## 测试

```powershell
$env:PYTHONPATH = "$pwd\backend;$pwd"
pytest -q
```

请先完成数据生成、入库和模型训练，否则部分 API 测试会拿到空结果（但不应报错）。

## Docker（可选）

```powershell
docker compose up --build
# 首次启动后初始化演示数据与模型
docker compose exec backend python scripts/bootstrap.py
```

开发阶段优先使用 SQLite + 本地前后端，不必依赖 Docker。
