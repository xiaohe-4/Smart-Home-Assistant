from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EnergyRecord(Base):
    __tablename__ = "energy_records"
    __table_args__ = (
        Index("ix_energy_user_time", "user_id", "timestamp"),
        Index("ix_energy_device_time", "device_id", "timestamp"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    power: Mapped[float] = mapped_column(Float, nullable=False)
    voltage: Mapped[float] = mapped_column(Float, nullable=False, default=220.0)
    current: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    energy: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    device = relationship("Device", back_populates="energy_records")
