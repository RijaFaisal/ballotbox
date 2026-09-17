import io

from pypdf import PdfReader

from app.repositories import entry_repository
from app.services.draw_service import run_draw


def _seed_entries(db_session, count: int) -> None:
    for i in range(1, count + 1):
        entry_repository.create(
            db_session, name=f"Person {i}", identifier=f"person{i}@example.com"
        )


def _extract_text(pdf_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def test_export_requires_admin(client, db_session):
    _seed_entries(db_session, 3)
    draw = run_draw(db_session, winner_count=2)

    response = client.get(f"/draws/{draw.id}/export")

    assert response.status_code == 401


def test_export_unknown_draw_returns_404(client, auth_headers):
    response = client.get("/draws/999999/export", headers=auth_headers)
    assert response.status_code == 404


def test_export_returns_pdf_with_winners(client, db_session, auth_headers):
    _seed_entries(db_session, 4)
    draw = run_draw(db_session, winner_count=3)

    response = client.get(f"/draws/{draw.id}/export", headers=auth_headers)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert f'draw-{draw.id}-winners.pdf' in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF")

    text = _extract_text(response.content)
    assert f"Draw #{draw.id} Winners" in text
    expected_names = {winner.entry.name for winner in draw.winners}
    for name in expected_names:
        assert name in text


def test_export_does_not_include_identifiers(client, db_session, auth_headers):
    _seed_entries(db_session, 2)
    draw = run_draw(db_session, winner_count=2)

    response = client.get(f"/draws/{draw.id}/export", headers=auth_headers)

    text = _extract_text(response.content)
    assert "@" not in text
