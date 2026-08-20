from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.schemas import ChatRequest
from app.services.energy_service import today_stats
from app.services.insight_service import chat_with_assistant, correlation_report, get_dashboard_insights, load_today_frame, tou_breakdown


router = APIRouter(prefix="/api/insights", tags=["insights"])
settings = get_settings()


@router.get("")
def insights(user_id: int = Query(default=settings.demo_user_id), db: Session = Depends(get_db)):
    data = get_dashboard_insights(db, user_id)
    data["top_strategies"] = [
        {
            "id": s.id,
            "title": s.title,
            "estimated_saving_percent": s.estimated_saving_percent,
            "comfort_impact": s.comfort_impact,
            "score": s.score,
        }
        for s in data["top_strategies"]
    ]
    return data


@router.get("/twin")
def twin(user_id: int = Query(default=settings.demo_user_id), db: Session = Depends(get_db)):
    return get_dashboard_insights(db, user_id)["twin"]


@router.get("/correlation")
def correlation(user_id: int = Query(default=settings.demo_user_id), db: Session = Depends(get_db)):
    frame = load_today_frame(db, user_id)
    return correlation_report(frame)


@router.get("/bill")
def bill(user_id: int = Query(default=settings.demo_user_id), db: Session = Depends(get_db)):
    stats = today_stats(db, user_id)
    frame = load_today_frame(db, user_id)
    return {"energy": stats["today_energy"], **tou_breakdown(frame)}


@router.post("/chat")
def chat(payload: ChatRequest, user_id: int = Query(default=settings.demo_user_id), db: Session = Depends(get_db)):
    return chat_with_assistant(db, user_id, payload.question)
