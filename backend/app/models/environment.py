from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class EnvironmentRecord(Base):
    __tablename__ = "environment_records"
    __table_args__ = (Index("ix_env_user_time", "user_id", "timestamp"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    temperature: Mapped[float] = mapped_column(Float, nullable=False)
    humidity: Mapped[float] = mapped_column(Float, nullable=False)
    light: Mapped[float] = mapped_column(Float, nullable=False)
    co2: Mapped[float] = mapped_column(Float, nullable=False)
