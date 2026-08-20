from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.schemas import ButlerCommand
from app.services.butler_service import handle_command, home_snapshot

router = APIRouter(prefix="/api/butler", tags=["butler"])
settings = get_settings()


@router.get("/state")
def butler_state(user_id: int = Query(default=settings.demo_user_id), db: Session = Depends(get_db)):
    return home_snapshot(db, user_id)


@router.post("/command")
def butler_command(
    payload: ButlerCommand,
    user_id: int = Query(default=settings.demo_user_id),
    db: Session = Depends(get_db),
):
    return handle_command(db, user_id, payload.text)
