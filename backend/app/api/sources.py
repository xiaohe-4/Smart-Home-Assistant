from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.services.source_service import degrade_report, get_source_map, validate_ingest

router = APIRouter(prefix="/api/sources", tags=["sources"])
settings = get_settings()


class IngestBody(BaseModel):
    modality: str
    rows: list[dict] = Field(default_factory=list)


@router.get("")
def sources(user_id: int = Query(default=settings.demo_user_id), db: Session = Depends(get_db)):
    return get_source_map(db, user_id)


@router.get("/degrade")
def degrade(
    drop: str = Query(default=""),
    user_id: int = Query(default=settings.demo_user_id),
    db: Session = Depends(get_db),
):
    dropped = [item.strip() for item in drop.split(",") if item.strip()]
    return degrade_report(db, user_id, dropped)


@router.post("/validate")
def validate(payload: IngestBody):
    return validate_ingest(payload.modality, payload.rows)
