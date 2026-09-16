from app.repositories import draw_repository, entry_repository
from app.services.draw_service import run_draw


def _seed_entries(db_session, count: int) -> None:
    for i in range(1, count + 1):
        entry_repository.create(
            db_session, name=f"Person {i}", identifier=f"person{i}@example.com"
        )


def test_results_returns_winners_of_latest_completed_draw(client, db_session):
    _seed_entries(db_session, 5)
    draw = run_draw(db_session, winner_count=3)

    response = client.get("/results")

    assert response.status_code == 200
    body = response.json()
    assert body["has_results"] is True
    assert body["drawn_at"] == draw.drawn_at.isoformat()
    assert len(body["winners"]) == 3
    positions = [w["position"] for w in body["winners"]]
    assert positions == sorted(positions)


def test_results_excludes_identifiers(client, db_session):
    _seed_entries(db_session, 3)
    run_draw(db_session, winner_count=2)

    response = client.get("/results")
    body = response.json()

    for winner in body["winners"]:
        assert set(winner.keys()) == {"position", "name"}
        assert "@" not in winner["name"]


def test_results_with_no_completed_draw_returns_empty_state_not_error(client):
    response = client.get("/results")

    assert response.status_code == 200
    body = response.json()
    assert body["has_results"] is False
    assert body["winners"] == []
    assert body["drawn_at"] is None


def test_results_returns_most_recent_completed_draw_when_multiple_exist(client, db_session):
    _seed_entries(db_session, 10)
    run_draw(db_session, winner_count=2)
    second_draw = run_draw(db_session, winner_count=2)

    response = client.get("/results")
    body = response.json()

    assert body["drawn_at"] == second_draw.drawn_at.isoformat()
    expected_names = {
        winner.entry.name
        for winner in draw_repository.list_winners_for_draw(db_session, second_draw.id)
    }
    assert {winner["name"] for winner in body["winners"]} == expected_names
