from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.schemas import AssistantOut, EnergyScoreOut, ProfileOut, SavingPotentialOut
from app.services.profile_service import assistant_summary, experiment_results, get_energy_score, get_profile, get_saving_potential


router = APIRouter(prefix="/api/profile", tags=["profile"])
settings = get_settings()


@router.get("", response_model=ProfileOut)
def profile(user_id: int = Query(default=settings.demo_user_id), db: Session = Depends(get_db)):
    return get_profile(db, user_id)


@router.get("/energy-score", response_model=EnergyScoreOut)
def energy_score(user_id: int = Query(default=settings.demo_user_id), db: Session = Depends(get_db)):
    return get_energy_score(db, user_id)


@router.get("/saving-potential", response_model=SavingPotentialOut)
def saving_potential(user_id: int = Query(default=settings.demo_user_id), db: Session = Depends(get_db)):
    return get_saving_potential(db, user_id)


@router.get("/assistant", response_model=AssistantOut)
def assistant(user_id: int = Query(default=settings.demo_user_id), db: Session = Depends(get_db)):
    return assistant_summary(db, user_id)


@router.get("/experiments")
def experiments():
    return experiment_results()
