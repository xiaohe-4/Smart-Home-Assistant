from pathlib import Path
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.api import anomaly, butler, devices, energy, insight, life, model_lab, prediction, profile, sources, strategy  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.core.database import Base, engine  # noqa: E402
from app.models import *  # noqa: F401,F403


settings = get_settings()
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(energy.router)
app.include_router(devices.router)
app.include_router(prediction.router)
app.include_router(anomaly.router)
app.include_router(strategy.router)
app.include_router(profile.router)
app.include_router(insight.router)
app.include_router(butler.router)
app.include_router(life.router)
app.include_router(sources.router)
app.include_router(model_lab.router)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "name": settings.app_name,
        "demo_date": settings.demo_date,
        "city": settings.city,
        "data_mode": settings.data_mode,
    }
