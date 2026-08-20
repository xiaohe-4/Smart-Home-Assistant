from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.schemas import SimulateOut, SimulateRequest, StrategyOut
from app.services.strategy_service import list_strategies, simulate, top_strategies


router = APIRouter(prefix="/api/strategies", tags=["strategies"])
settings = get_settings()


@router.get("", response_model=list[StrategyOut])
def strategies(user_id: int = Query(default=settings.demo_user_id), db: Session = Depends(get_db)):
    return list_strategies(db, user_id)


@router.get("/top", response_model=list[StrategyOut])
def strategies_top(
    limit: int = Query(default=3, ge=1, le=10),
    user_id: int = Query(default=settings.demo_user_id),
    db: Session = Depends(get_db),
):
    return top_strategies(db, user_id, limit=limit)


@router.post("/simulate", response_model=SimulateOut)
def strategies_simulate(
    payload: SimulateRequest,
    user_id: int = Query(default=settings.demo_user_id),
    db: Session = Depends(get_db),
):
    return simulate(db, user_id, payload.strategy_ids)
