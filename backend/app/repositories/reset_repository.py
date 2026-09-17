from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.models.draw import Draw
from app.models.product import Product
from app.models.winner import Winner


@dataclass(frozen=True)
class ResetCounts:
    products_deleted: int
    candidates_deleted: int
    draws_deleted: int
    winners_deleted: int


def reset_ballot(db: Session) -> ResetCounts:
    """Deletes all winners, then draws, then candidates, then products,
    committing once.

    This is the only order that respects the foreign keys without relying
    on cascades: winners reference draws.id (ON DELETE CASCADE) and
    candidates.id (ON DELETE RESTRICT), and draws reference products.id
    (ON DELETE RESTRICT). Committing once means the reset is all-or-nothing.
    """
    winners_deleted = db.execute(delete(Winner)).rowcount
    draws_deleted = db.execute(delete(Draw)).rowcount
    candidates_deleted = db.execute(delete(Candidate)).rowcount
    products_deleted = db.execute(delete(Product)).rowcount
    db.commit()
    return ResetCounts(
        products_deleted=products_deleted,
        candidates_deleted=candidates_deleted,
        draws_deleted=draws_deleted,
        winners_deleted=winners_deleted,
    )
