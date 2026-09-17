from __future__ import annotations

import datetime as dt
import enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.winner import Winner


class DrawStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class Draw(Base):
    __tablename__ = "draws"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    seed: Mapped[str] = mapped_column(String(128), nullable=False)
    drawn_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    winner_count: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[DrawStatus] = mapped_column(
        SAEnum(
            DrawStatus,
            name="draw_status",
            native_enum=False,
            length=20,
            # Without this, SQLAlchemy persists each member's NAME
            # ("PENDING") instead of its value ("pending"), which the
            # database's lowercase ck_draws_status CHECK constraint rejects.
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=DrawStatus.PENDING,
    )

    product: Mapped["Product"] = relationship(back_populates="draws")
    winners: Mapped[list["Winner"]] = relationship(
        back_populates="draw", order_by="Winner.position"
    )
