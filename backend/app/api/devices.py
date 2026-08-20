from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.schemas import DeviceEnergyOut, DeviceOut, EnergyPoint
from app.services.device_service import device_energy_breakdown, device_energy_series, get_device, list_devices


router = APIRouter(prefix="/api/devices", tags=["devices"])
settings = get_settings()


@router.get("", response_model=list[DeviceEnergyOut])
def devices(user_id: int = Query(default=settings.demo_user_id), db: Session = Depends(get_db)):
    return device_energy_breakdown(db, user_id)


@router.get("/{device_id}", response_model=DeviceOut)
def device_detail(
    device_id: int,
    user_id: int = Query(default=settings.demo_user_id),
    db: Session = Depends(get_db),
):
    device = get_device(db, user_id, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    return device


@router.get("/{device_id}/energy", response_model=list[EnergyPoint])
def device_energy(
    device_id: int,
    user_id: int = Query(default=settings.demo_user_id),
    db: Session = Depends(get_db),
):
    device = get_device(db, user_id, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    return device_energy_series(db, user_id, device_id)
