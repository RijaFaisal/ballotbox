from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.draw import Draw, DrawStatus
from app.models.winner import Winner


def create_pending(db: Session, seed: str, winner_count: int) -> Draw:
    draw = Draw(seed=seed, winner_count=winner_count, status=DrawStatus.PENDING)
    db.add(draw)
    db.commit()
    db.refresh(draw)
    return draw


def get_by_id(db: Session, draw_id: int) -> Draw | None:
    return db.execute(select(Draw).where(Draw.id == draw_id)).scalar_one_or_none()


def list_all(db: Session) -> list[Draw]:
    return list(db.execute(select(Draw).order_by(Draw.id.desc())).scalars().all())


def get_latest_completed(db: Session) -> Draw | None:
    return db.execute(
        select(Draw)
        .where(Draw.status == DrawStatus.COMPLETED)
        .order_by(Draw.drawn_at.desc(), Draw.id.desc())
        .limit(1)
    ).scalar_one_or_none()


def list_winners_for_draw(db: Session, draw_id: int) -> list[Winner]:
    return list(
        db.execute(
            select(Winner).where(Winner.draw_id == draw_id).order_by(Winner.position)
        ).scalars().all()
    )


def complete(db: Session, draw: Draw, winners: list[Winner], drawn_at: dt.datetime) -> Draw:
    """Writes winners and marks the draw completed in a single transaction.

    Both must land together: a commit failure here must never leave winner
    rows attached to a draw that isn't marked completed, or vice versa.
    """
    for winner in winners:
        db.add(winner)
    draw.status = DrawStatus.COMPLETED
    draw.drawn_at = drawn_at
    db.commit()
    db.refresh(draw)
    return draw


def mark_failed(db: Session, draw: Draw) -> Draw:
    # Roll back first to discard any partial, uncommitted writes from this
    # attempt (e.g. winner rows added but not yet committed) without
    # touching the seed/winner_count already committed by create_pending.
    db.rollback()
    draw.status = DrawStatus.FAILED
    db.add(draw)
    db.commit()
    db.refresh(draw)
    return draw
