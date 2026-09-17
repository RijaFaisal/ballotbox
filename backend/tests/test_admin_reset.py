from app.repositories import draw_repository, entry_repository
from app.services.draw_service import run_draw


def _seed_entries(db_session, count: int) -> None:
    for i in range(1, count + 1):
        entry_repository.create(
            db_session, name=f"Person {i}", identifier=f"person{i}@example.com"
        )


def test_reset_requires_admin(client):
    response = client.post("/admin/reset", json={"confirm": "RESET"})
    assert response.status_code == 401


def test_reset_rejects_wrong_confirmation_phrase(client, db_session, auth_headers):
    _seed_entries(db_session, 3)

    response = client.post("/admin/reset", json={"confirm": "yes"}, headers=auth_headers)

    assert response.status_code == 400
    # nothing was deleted
    assert len(entry_repository.list_all_ordered_by_id(db_session)) == 3


def test_reset_clears_entries_draws_and_winners(client, db_session, auth_headers):
    _seed_entries(db_session, 5)
    draw = run_draw(db_session, winner_count=2)
    assert len(draw_repository.list_winners_for_draw(db_session, draw.id)) == 2

    response = client.post("/admin/reset", json={"confirm": "RESET"}, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body == {"entries_deleted": 5, "draws_deleted": 1, "winners_deleted": 2}

    assert entry_repository.list_all_ordered_by_id(db_session) == []
    assert draw_repository.list_all(db_session) == []
    assert draw_repository.list_winners_for_draw(db_session, draw.id) == []


def test_dashboard_shows_zero_entries_after_reset(client, db_session, auth_headers):
    _seed_entries(db_session, 4)

    client.post("/admin/reset", json={"confirm": "RESET"}, headers=auth_headers)
    response = client.get("/entries", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == []


def test_reset_does_not_touch_admin_accounts(client, db_session, auth_headers):
    _seed_entries(db_session, 2)

    response = client.post("/admin/reset", json={"confirm": "RESET"}, headers=auth_headers)
    assert response.status_code == 200

    # the same admin token still works after the reset
    me_response = client.get("/auth/me", headers=auth_headers)
    assert me_response.status_code == 200
