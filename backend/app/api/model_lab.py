from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.services.model_lab import get_model_lab

router = APIRouter(prefix="/api/models", tags=["models"])
settings = get_settings()


@router.get("")
def model_lab(user_id: int = Query(default=settings.demo_user_id), db: Session = Depends(get_db)):
    return get_model_lab(db, user_id)
