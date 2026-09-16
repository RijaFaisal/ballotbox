from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.draw import Draw
    from app.models.entry import Entry


class Winner(Base):
    __tablename__ = "winners"
    __table_args__ = (
        UniqueConstraint("draw_id", "entry_id", name="uq_winners_draw_entry"),
        UniqueConstraint("draw_id", "position", name="uq_winners_draw_position"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    draw_id: Mapped[int] = mapped_column(
        ForeignKey("draws.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entry_id: Mapped[int] = mapped_column(
        ForeignKey("entries.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    draw: Mapped["Draw"] = relationship(back_populates="winners")
    entry: Mapped["Entry"] = relationship(back_populates="winners")
