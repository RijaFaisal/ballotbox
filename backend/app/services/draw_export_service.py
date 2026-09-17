import csv
import io

from sqlalchemy.orm import Session

from app.models.draw import Draw
from app.repositories import draw_repository


def winners_csv(db: Session, draw: Draw) -> str:
    """Builds a CSV of a draw's winners: position, name, and the draw date.

    Deliberately excludes entry.identifier -- the same PII rule as the
    public results endpoint and the admin entry list.
    """
    winners = draw_repository.list_winners_for_draw(db, draw.id)
    drawn_at = draw.drawn_at.isoformat() if draw.drawn_at is not None else ""

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["position", "name", "draw_date"])
    for winner in winners:
        writer.writerow([winner.position, winner.entry.name, drawn_at])
    return buffer.getvalue()
