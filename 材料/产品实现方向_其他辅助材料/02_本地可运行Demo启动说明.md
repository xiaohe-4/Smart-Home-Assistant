# 本地可运行 Demo 启动说明（Windows）

## 环境

- Python 3.10+（项目含 `.venv` 时可直接用）
- Node.js 18+（前端）

## 步骤

在项目根目录 `智家能/`：

```powershell
# 依赖（若尚未安装）
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt

# 数据与模型（若库已有可跳过）
.\.venv\Scripts\python.exe scripts\generate_demo_data.py
.\.venv\Scripts\python.exe scripts\init_db.py
.\.venv\Scripts\python.exe scripts\train_models.py

# 后端（新终端）
$env:PYTHONPATH = "$pwd\backend;$pwd"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000

# 前端（新终端）
cd frontend
npm install
npm run dev
```

打开：http://127.0.0.1:5174/

点右下角「3 分钟演示」可锁定演示户并静音。

改 Python 代码后必须重启 uvicorn。
