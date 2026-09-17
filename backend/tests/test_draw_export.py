import csv
import io

from app.repositories import entry_repository
from app.services.draw_service import run_draw


def _seed_entries(db_session, count: int) -> None:
    for i in range(1, count + 1):
        entry_repository.create(
            db_session, name=f"Person {i}", identifier=f"person{i}@example.com"
        )


def test_export_requires_admin(client, db_session):
    _seed_entries(db_session, 3)
    draw = run_draw(db_session, winner_count=2)

    response = client.get(f"/draws/{draw.id}/export")

    assert response.status_code == 401


def test_export_unknown_draw_returns_404(client, auth_headers):
    response = client.get("/draws/999999/export", headers=auth_headers)
    assert response.status_code == 404


def test_export_returns_csv_with_position_name_and_date(client, db_session, auth_headers):
    _seed_entries(db_session, 4)
    draw = run_draw(db_session, winner_count=3)

    response = client.get(f"/draws/{draw.id}/export", headers=auth_headers)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert f'draw-{draw.id}-winners.csv' in response.headers["content-disposition"]

    rows = list(csv.reader(io.StringIO(response.text)))
    header, *data_rows = rows
    assert header == ["position", "name", "draw_date"]
    assert len(data_rows) == 3

    expected_names = {winner.entry.name for winner in draw.winners}
    csv_names = {row[1] for row in data_rows}
    assert csv_names == expected_names

    positions = sorted(int(row[0]) for row in data_rows)
    assert positions == [1, 2, 3]

    for row in data_rows:
        assert row[2] == draw.drawn_at.isoformat()


def test_export_does_not_include_identifiers(client, db_session, auth_headers):
    _seed_entries(db_session, 2)
    draw = run_draw(db_session, winner_count=2)

    response = client.get(f"/draws/{draw.id}/export", headers=auth_headers)

    assert "@" not in response.text
