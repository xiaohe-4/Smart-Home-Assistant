from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    household_size: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    home_type: Mapped[str] = mapped_column(String(64), nullable=False, default="apartment")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    devices = relationship("Device", back_populates="user")
