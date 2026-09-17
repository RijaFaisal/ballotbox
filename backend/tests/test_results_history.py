from app.repositories import entry_repository
from app.services.draw_service import run_draw


def _seed_entries(db_session, count: int) -> None:
    for i in range(1, count + 1):
        entry_repository.create(
            db_session, name=f"Person {i}", identifier=f"person{i}@example.com"
        )


def test_history_is_public(client):
    response = client.get("/results/history")
    assert response.status_code == 200


def test_history_empty_with_no_completed_draws(client):
    response = client.get("/results/history")
    assert response.status_code == 200
    assert response.json() == []


def test_history_empty_with_only_one_completed_draw(client, db_session):
    _seed_entries(db_session, 3)
    run_draw(db_session, winner_count=1)

    response = client.get("/results/history")

    assert response.status_code == 200
    assert response.json() == []


def test_history_excludes_the_latest_draw(client, db_session):
    _seed_entries(db_session, 5)
    first = run_draw(db_session, winner_count=1)
    second = run_draw(db_session, winner_count=1)
    third = run_draw(db_session, winner_count=1)

    response = client.get("/results/history")

    assert response.status_code == 200
    body = response.json()
    ids = [entry["id"] for entry in body]
    assert third.id not in ids  # third is the latest, covered by /results instead
    assert set(ids) == {first.id, second.id}
    # newest-first ordering
    assert ids == [second.id, first.id]


def test_history_entry_has_no_identifiers(client, db_session):
    _seed_entries(db_session, 3)
    run_draw(db_session, winner_count=1)
    run_draw(db_session, winner_count=1)

    response = client.get("/results/history")

    for entry in response.json():
        assert set(entry.keys()) == {"id", "drawn_at", "winner_count"}
        assert "seed" not in entry


def test_history_detail_returns_winners(client, db_session):
    _seed_entries(db_session, 4)
    older = run_draw(db_session, winner_count=2)
    run_draw(db_session, winner_count=1)  # latest, not the one we're fetching

    response = client.get(f"/results/history/{older.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == older.id
    assert body["winner_count"] == 2
    assert len(body["winners"]) == 2
    expected_names = {w.entry.name for w in older.winners}
    assert {w["name"] for w in body["winners"]} == expected_names


def test_history_detail_excludes_identifiers(client, db_session):
    _seed_entries(db_session, 3)
    older = run_draw(db_session, winner_count=2)
    run_draw(db_session, winner_count=1)

    response = client.get(f"/results/history/{older.id}")

    body = response.json()
    assert set(body.keys()) == {"id", "drawn_at", "winner_count", "winners"}
    assert "seed" not in body
    for winner in body["winners"]:
        assert set(winner.keys()) == {"position", "name"}
        assert "@" not in winner["name"]


def test_history_detail_404_for_unknown_draw(client):
    response = client.get("/results/history/999999")
    assert response.status_code == 404


def test_history_detail_404_for_non_completed_draw(client, db_session):
    # winner_count exceeding the pool marks the draw failed, never completed
    _seed_entries(db_session, 1)
    from app.services.draw_service import NotEnoughEntriesError
    import pytest

    with pytest.raises(NotEnoughEntriesError):
        run_draw(db_session, winner_count=5)

    from app.repositories import draw_repository

    failed_draw = draw_repository.list_all(db_session)[0]
    assert failed_draw.status.value == "failed"

    response = client.get(f"/results/history/{failed_draw.id}")
    assert response.status_code == 404
