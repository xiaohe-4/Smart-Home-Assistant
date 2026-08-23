"""创建数据表并导入 Demo CSV。"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import delete


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.models import (  # noqa: E402
    Anomaly,
    BehaviorRecord,
    ButlerLog,
    ButlerMemory,
    Device,
    DeviceActuator,
    EnergyRecord,
    EnvironmentRecord,
    HomeFlag,
    HomeRule,
    HomeScene,
    Prediction,
    Strategy,
    User,
    WeatherRecord,
)


DEMO_DIR = PROJECT_ROOT / "data" / "demo"


def _read_csv(name: str) -> pd.DataFrame:
    path = DEMO_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"缺少 Demo 数据文件: {path}，请先运行 scripts/generate_demo_data.py")
    return pd.read_csv(path, parse_dates=["timestamp"] if "timestamp" in open(path, encoding="utf-8").readline() else [])


def reset_tables() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def import_all() -> None:
    users = pd.read_csv(DEMO_DIR / "users.csv")
    devices = pd.read_csv(DEMO_DIR / "devices.csv")
    energy = pd.read_csv(DEMO_DIR / "energy_records.csv", parse_dates=["timestamp"])
    env = pd.read_csv(DEMO_DIR / "environment_records.csv", parse_dates=["timestamp"])
    behavior = pd.read_csv(DEMO_DIR / "behavior_records.csv", parse_dates=["timestamp"])
    weather = pd.read_csv(DEMO_DIR / "weather_records.csv", parse_dates=["timestamp"])

    db = SessionLocal()
    try:
        for model in (
            HomeFlag,
            HomeRule,
            ButlerLog,
            ButlerMemory,
            HomeScene,
            DeviceActuator,
            Anomaly,
            Prediction,
            Strategy,
            EnergyRecord,
            EnvironmentRecord,
            BehaviorRecord,
            WeatherRecord,
            Device,
            User,
        ):
            db.execute(delete(model))
        db.commit()

        db.bulk_insert_mappings(User, users.to_dict(orient="records"))
        db.bulk_insert_mappings(Device, devices.to_dict(orient="records"))
        db.commit()

        def chunks(df: pd.DataFrame, size: int = 5000):
            for start in range(0, len(df), size):
                yield df.iloc[start : start + size]

        for part in chunks(energy):
            db.bulk_insert_mappings(EnergyRecord, part.to_dict(orient="records"))
        for part in chunks(env):
            db.bulk_insert_mappings(EnvironmentRecord, part.to_dict(orient="records"))
        for part in chunks(behavior):
            db.bulk_insert_mappings(BehaviorRecord, part.to_dict(orient="records"))
        for part in chunks(weather):
            db.bulk_insert_mappings(WeatherRecord, part.to_dict(orient="records"))
        db.commit()
        print(
            "导入完成:",
            f"users={len(users)}, devices={len(devices)}, energy={len(energy)},",
            f"env={len(env)}, behavior={len(behavior)}, weather={len(weather)}",
        )
    finally:
        db.close()


if __name__ == "__main__":
    reset_tables()
    import_all()
    import subprocess

    subprocess.check_call([sys.executable, str(PROJECT_ROOT / "scripts" / "import_real_home.py")], cwd=PROJECT_ROOT)
