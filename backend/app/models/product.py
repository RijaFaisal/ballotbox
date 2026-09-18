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
    # The manual is_open toggle and this scheduled deadline are independent
    # levers: is_open can still close entries early, but once closes_at is in
    # the past, effectively_open is False regardless of is_open's value.
    closes_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    candidates: Mapped[list["Candidate"]] = relationship(back_populates="product")
    draws: Mapped[list["Draw"]] = relationship(back_populates="product")

    @property
    def effectively_open(self) -> bool:
        """The real-world state entrants see, vs. is_open's raw switch
        position. SQLite (used in tests) returns closes_at as naive even
        though it's always stored as UTC, so naive values are treated as UTC
        here rather than compared directly against an aware "now"."""
        if not self.is_open or self.closes_at is None:
            return self.is_open

        closes_at = self.closes_at
        if closes_at.tzinfo is None:
            closes_at = closes_at.replace(tzinfo=dt.timezone.utc)
        return closes_at > dt.datetime.now(dt.timezone.utc)
