from __future__ import annotations

import datetime as dt
import random
import secrets
from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.models.draw import Draw, DrawStatus
from app.models.winner import Winner
from app.repositories import candidate_repository, draw_repository


class DrawAlreadyCompletedError(Exception):
    """Raised when a draw that isn't PENDING is asked to run."""


class NotEnoughEntriesError(Exception):
    """Raised when winner_count exceeds the number of eligible candidates."""


def _generate_seed() -> str:
    # secrets, not random: this is the one place a non-reproducible value is
    # needed. Everything downstream is reproducible from this string alone.
    return secrets.token_hex(32)


def select_winners(candidates: Sequence[Candidate], seed: str, winner_count: int) -> list[Candidate]:
    """Pure, deterministic selection.

    The ONLY randomness source is random.Random(seed). Given the same seed,
    the same candidates (in the same order), and the same winner_count, this
    always returns the same winners in the same order — that determinism is
    the entire reproducibility guarantee of a draw.
    """
    return random.Random(seed).sample(list(candidates), winner_count)


def create_pending_draw(db: Session, product_id: int, winner_count: int) -> Draw:
    """Step 1 of a draw: persist the seed and a pending row before any
    selection happens. This row is the audit anchor — it exists in the
    database whether or not the selection that follows succeeds.
    """
    seed = _generate_seed()
    return draw_repository.create_pending(
        db, product_id=product_id, seed=seed, winner_count=winner_count
    )


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
        candidates = candidate_repository.list_by_product_ordered_by_id(db, draw.product_id)

        if draw.winner_count > len(candidates):
            raise NotEnoughEntriesError(
                f"Requested {draw.winner_count} winners but only {len(candidates)} "
                "eligible candidates exist for this product."
            )

        selected = select_winners(candidates, draw.seed, draw.winner_count)
        winners = [
            Winner(draw_id=draw.id, candidate_id=candidate.id, position=position)
            for position, candidate in enumerate(selected, start=1)
        ]

        return draw_repository.complete(
            db, draw, winners, drawn_at=dt.datetime.now(dt.timezone.utc)
        )
    except Exception:
        draw_repository.mark_failed(db, draw)
        raise


def run_draw(db: Session, product_id: int, winner_count: int) -> Draw:
    """Full flow used by the route: create the pending/seeded draw, then
    execute it. Every call produces a brand-new draw row — there is no path
    by which this re-runs an existing draw.
    """
    draw = create_pending_draw(db, product_id, winner_count)
    return execute_draw(db, draw)
