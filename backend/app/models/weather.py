from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WeatherRecord(Base):
    __tablename__ = "weather_records"
    __table_args__ = (Index("ix_weather_time", "timestamp"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    temperature: Mapped[float] = mapped_column(Float, nullable=False)
    humidity: Mapped[float] = mapped_column(Float, nullable=False)
    weather: Mapped[str] = mapped_column(String(32), nullable=False)
    wind_speed: Mapped[float] = mapped_column(Float, nullable=False)
