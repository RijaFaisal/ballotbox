from sqlalchemy.orm import Session

from app.repositories import draw_repository
from app.schemas.results import ResultsRead, ResultsWinner


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
