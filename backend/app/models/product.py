from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.candidate import Candidate
    from app.models.draw import Draw


class Product(Base):
    __tablename__ = "products"

    # Case-insensitive uniqueness on name is enforced by a functional index
    # (uq_products_name_lower) created in the migration, not representable
    # as a plain SQLAlchemy column constraint.
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_open: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    candidates: Mapped[list["Candidate"]] = relationship(back_populates="product")
    draws: Mapped[list["Draw"]] = relationship(back_populates="product")
