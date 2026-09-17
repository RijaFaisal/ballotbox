from fpdf import FPDF, XPos, YPos
from sqlalchemy.orm import Session

from app.models.draw import Draw
from app.repositories import draw_repository


def _latin1_safe(value: str) -> str:
    # The core PDF font (Helvetica) only supports Latin-1. Names typed on
    # phones often contain smart quotes or other characters outside that
    # range (e.g. iOS autocorrect); replace rather than crash the export.
    return value.encode("latin-1", "replace").decode("latin-1")


def winners_pdf(db: Session, draw: Draw) -> bytes:
    """Builds a one-page PDF of a draw's winners: position, name, and the
    draw date.

    Deliberately excludes entry.identifier -- the same PII rule as the
    public results endpoint and the admin entry list.
    """
    winners = draw_repository.list_winners_for_draw(db, draw.id)
    drawn_at = draw.drawn_at.isoformat() if draw.drawn_at is not None else "-"

    pdf = FPDF()
    pdf.set_title(f"Draw #{draw.id} winners")
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, f"Draw #{draw.id} Winners", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(90, 90, 90)
    pdf.cell(0, 8, f"Drawn: {_latin1_safe(drawn_at)}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(6)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(30, 9, "Position", border=1, fill=True)
    pdf.cell(0, 9, "Name", border=1, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "", 11)
    for winner in winners:
        pdf.cell(30, 9, str(winner.position), border=1)
        pdf.cell(
            0,
            9,
            _latin1_safe(winner.entry.name),
            border=1,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )

    return bytes(pdf.output())
