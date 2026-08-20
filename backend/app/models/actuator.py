from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DeviceActuator(Base):
    __tablename__ = "device_actuators"

    device_id: Mapped[int] = mapped_column(Integer, ForeignKey("devices.id"), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    setpoint: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_command: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class HomeScene(Base):
    __tablename__ = "home_scenes"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scene: Mapped[str] = mapped_column(String(32), nullable=False, default="日常")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class ButlerLog(Base):
    __tablename__ = "butler_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    command: Mapped[str] = mapped_column(String(255), nullable=False)
    intent: Mapped[str] = mapped_column(String(64), nullable=False)
    speech: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ButlerMemory(Base):
    __tablename__ = "butler_memory"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pending_cmd: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    pending_reason: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    preferred_ac: Mapped[int] = mapped_column(Integer, nullable=False, default=26)
    quiet: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
