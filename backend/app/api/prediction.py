from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.schemas import PredictionOut
from app.services.prediction_service import get_prediction


router = APIRouter(prefix="/api/prediction", tags=["prediction"])
settings = get_settings()


@router.get("/hour", response_model=PredictionOut)
def prediction_hour(user_id: int = Query(default=settings.demo_user_id), db: Session = Depends(get_db)):
    return get_prediction(db, user_id, hours=1)


@router.get("/day", response_model=PredictionOut)
def prediction_day(
    hours: int = Query(default=24, ge=1, le=24),
    user_id: int = Query(default=settings.demo_user_id),
    db: Session = Depends(get_db),
):
    return get_prediction(db, user_id, hours=hours)
