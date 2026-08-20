from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.services.life_board import book_schedule, complete_mission, set_comfort, set_demand
from app.services.life_service import get_life_os, toggle_rule

router = APIRouter(prefix="/api/life", tags=["life"])
settings = get_settings()


class RuleToggle(BaseModel):
    key: str
    armed: bool


class MissionBody(BaseModel):
    key: str
    done: bool = True
    execute: bool = False


class DemandBody(BaseModel):
    action: str


class ScheduleBody(BaseModel):
    task: str
    booked: bool = True


class ComfortBody(BaseModel):
    mode: str
    execute: bool = False


@router.get("")
def life_os(user_id: int = Query(default=settings.demo_user_id), db: Session = Depends(get_db)):
    return get_life_os(db, user_id)


@router.post("/rules")
def life_rule(payload: RuleToggle, user_id: int = Query(default=settings.demo_user_id), db: Session = Depends(get_db)):
    return toggle_rule(db, user_id, payload.key, payload.armed)


@router.post("/missions")
def life_mission(payload: MissionBody, user_id: int = Query(default=settings.demo_user_id), db: Session = Depends(get_db)):
    return complete_mission(db, user_id, payload.key, payload.done, payload.execute)


@router.post("/demand")
def life_demand(payload: DemandBody, user_id: int = Query(default=settings.demo_user_id), db: Session = Depends(get_db)):
    return set_demand(db, user_id, payload.action)


@router.post("/schedule")
def life_schedule(payload: ScheduleBody, user_id: int = Query(default=settings.demo_user_id), db: Session = Depends(get_db)):
    return book_schedule(db, user_id, payload.task, payload.booked)


@router.post("/comfort")
def life_comfort(payload: ComfortBody, user_id: int = Query(default=settings.demo_user_id), db: Session = Depends(get_db)):
    return set_comfort(db, user_id, payload.mode, payload.execute)
