from __future__ import annotations

import datetime as dt
import random
import secrets
from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.models.draw import Draw, DrawStatus
from app.models.entry import Entry
from app.models.winner import Winner
from app.repositories import draw_repository, entry_repository


class DrawAlreadyCompletedError(Exception):
    """Raised when a draw that isn't PENDING is asked to run."""


class NotEnoughEntriesError(Exception):
    """Raised when winner_count exceeds the number of eligible entries."""


def _generate_seed() -> str:
    # secrets, not random: this is the one place a non-reproducible value is
    # needed. Everything downstream is reproducible from this string alone.
    return secrets.token_hex(32)


def select_winners(entries: Sequence[Entry], seed: str, winner_count: int) -> list[Entry]:
    """Pure, deterministic selection.

    The ONLY randomness source is random.Random(seed). Given the same seed,
    the same entries (in the same order), and the same winner_count, this
    always returns the same winners in the same order — that determinism is
    the entire reproducibility guarantee of a draw.
    """
    return random.Random(seed).sample(list(entries), winner_count)


def create_pending_draw(db: Session, winner_count: int) -> Draw:
    """Step 1 of a draw: persist the seed and a pending row before any
    selection happens. This row is the audit anchor — it exists in the
    database whether or not the selection that follows succeeds.
    """
    seed = _generate_seed()
    return draw_repository.create_pending(db, seed=seed, winner_count=winner_count)


def execute_draw(db: Session, draw: Draw) -> Draw:
    """Runs the seeded selection for an already-persisted pending draw.

    A draw that isn't PENDING (completed or failed) is immutable: it cannot
    be re-run in place. A redo must go through create_pending_draw to get a
    brand-new draw row and a brand-new seed, so both attempts stay on record.
    """
    if draw.status != DrawStatus.PENDING:
        raise DrawAlreadyCompletedError(
            f"Draw {draw.id} is already {draw.status.value}; it cannot be "
            "re-run. Start a new draw instead."
        )

    try:
        entries = entry_repository.list_all_ordered_by_id(db)

        if draw.winner_count > len(entries):
            raise NotEnoughEntriesError(
                f"Requested {draw.winner_count} winners but only {len(entries)} "
                "eligible entries exist."
            )

        selected = select_winners(entries, draw.seed, draw.winner_count)
        winners = [
            Winner(draw_id=draw.id, entry_id=entry.id, position=position)
            for position, entry in enumerate(selected, start=1)
        ]

        return draw_repository.complete(
            db, draw, winners, drawn_at=dt.datetime.now(dt.timezone.utc)
        )
    except Exception:
        draw_repository.mark_failed(db, draw)
        raise


def run_draw(db: Session, winner_count: int) -> Draw:
    """Full flow used by the route: create the pending/seeded draw, then
    execute it. Every call produces a brand-new draw row — there is no path
    by which this re-runs an existing draw.
    """
    draw = create_pending_draw(db, winner_count)
    return execute_draw(db, draw)
