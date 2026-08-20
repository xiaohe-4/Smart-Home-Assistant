from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.schemas import AnomalyOut
from app.services.anomaly_service import latest_anomalies, list_anomalies


router = APIRouter(prefix="/api/anomalies", tags=["anomalies"])
settings = get_settings()


@router.get("", response_model=list[AnomalyOut])
def anomalies(user_id: int = Query(default=settings.demo_user_id), db: Session = Depends(get_db)):
    return list_anomalies(db, user_id)


@router.get("/latest", response_model=list[AnomalyOut])
def anomalies_latest(
    limit: int = Query(default=5, ge=1, le=20),
    user_id: int = Query(default=settings.demo_user_id),
    db: Session = Depends(get_db),
):
    return latest_anomalies(db, user_id, limit=limit)
