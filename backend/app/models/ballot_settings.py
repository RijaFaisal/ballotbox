from __future__ import annotations

from sqlalchemy import Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BallotSettings(Base):
    __tablename__ = "ballot_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    is_open: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
