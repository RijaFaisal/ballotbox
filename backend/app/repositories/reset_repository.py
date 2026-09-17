from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models.draw import Draw
from app.models.entry import Entry
from app.models.winner import Winner


@dataclass(frozen=True)
class ResetCounts:
    entries_deleted: int
    draws_deleted: int
    winners_deleted: int


def reset_ballot(db: Session) -> ResetCounts:
    """Deletes all winners, then all draws, then all entries, committing once.

    This is the only order that respects the foreign keys: winners
    reference both draws.id (ON DELETE CASCADE) and entries.id (ON DELETE
    RESTRICT), so entries cannot be removed while any winner row still
    points at them. Committing once means the reset is all-or-nothing.
    """
    winners_deleted = db.execute(delete(Winner)).rowcount
    draws_deleted = db.execute(delete(Draw)).rowcount
    entries_deleted = db.execute(delete(Entry)).rowcount
    db.commit()
    return ResetCounts(
        entries_deleted=entries_deleted,
        draws_deleted=draws_deleted,
        winners_deleted=winners_deleted,
    )
