from sqlalchemy.orm import Session

from app.models.draw import Draw
from app.repositories import draw_repository
from app.schemas.results import DrawHistoryDetail, DrawHistoryEntry, ResultsRead, ResultsWinner


def get_latest_results(db: Session) -> ResultsRead:
    draw = draw_repository.get_latest_completed(db)
    if draw is None:
        return ResultsRead(has_results=False)

    winners = draw_repository.list_winners_for_draw(db, draw.id)
    return ResultsRead(
        has_results=True,
        drawn_at=draw.drawn_at,
        # Only position + name cross the boundary — never entry.identifier.
        winners=[ResultsWinner(position=w.position, name=w.entry.name) for w in winners],
    )


def get_draw_history(db: Session) -> list[Draw]:
    """Completed draws excluding the latest one (already covered by
    get_latest_results), newest first. Both are derived from the same
    ordered query so "latest" and "history" can never disagree."""
    completed = draw_repository.list_completed_ordered(db)
    return completed[1:]


def get_history_entry(draw: Draw) -> DrawHistoryEntry:
    return DrawHistoryEntry(id=draw.id, drawn_at=draw.drawn_at, winner_count=draw.winner_count)


def get_history_detail(db: Session, draw_id: int) -> DrawHistoryDetail | None:
    draw = draw_repository.get_completed_by_id(db, draw_id)
    if draw is None:
        return None
    winners = draw_repository.list_winners_for_draw(db, draw.id)
    return DrawHistoryDetail(
        id=draw.id,
        drawn_at=draw.drawn_at,
        winner_count=draw.winner_count,
        winners=[ResultsWinner(position=w.position, name=w.entry.name) for w in winners],
    )
