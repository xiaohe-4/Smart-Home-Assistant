"""一键完成：生成数据 → 入库 → 训练模型。"""

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(script: str) -> None:
    print(f"\n=== {script} ===")
    subprocess.check_call([sys.executable, str(ROOT / "scripts" / script)], cwd=ROOT)


if __name__ == "__main__":
    run("generate_demo_data.py")
    run("init_db.py")
    run("train_models.py")
    print("\nBootstrap 完成。接下来启动后端和前端即可演示。")
