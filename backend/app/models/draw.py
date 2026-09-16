from __future__ import annotations

import datetime as dt
import enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.winner import Winner


class DrawStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class Draw(Base):
    __tablename__ = "draws"

    id: Mapped[int] = mapped_column(primary_key=True)
    seed: Mapped[str] = mapped_column(String(128), nullable=False)
    drawn_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    winner_count: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[DrawStatus] = mapped_column(
        SAEnum(DrawStatus, name="draw_status", native_enum=False, length=20),
        nullable=False,
        default=DrawStatus.PENDING,
    )

    winners: Mapped[list["Winner"]] = relationship(
        back_populates="draw", order_by="Winner.position"
    )
