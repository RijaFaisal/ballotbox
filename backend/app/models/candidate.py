from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.winner import Winner


class Candidate(Base):
    __tablename__ = "candidates"

    # Dedup within a product (CNIC if provided, else email) is enforced at
    # the service layer and backed by partial unique indexes created in the
    # migration (uq_candidates_product_cnic, uq_candidates_product_email) --
    # not representable as plain SQLAlchemy column constraints, since
    # neither field alone is required.
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    cnic: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    product: Mapped["Product"] = relationship(back_populates="candidates")
    winners: Mapped[list["Winner"]] = relationship(back_populates="candidate")
