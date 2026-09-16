from app.repositories import entry_repository


def _seed_entries(db_session, count: int) -> None:
    for i in range(1, count + 1):
        entry_repository.create(
            db_session, name=f"Person {i}", identifier=f"person{i}@example.com"
        )


def test_create_draw_requires_admin_token(client, db_session):
    _seed_entries(db_session, 5)
    response = client.post("/draws", json={"winner_count": 2})
    assert response.status_code == 401


def test_create_draw_returns_winners(client, db_session, auth_headers):
    _seed_entries(db_session, 5)
    response = client.post("/draws", json={"winner_count": 2}, headers=auth_headers)
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "completed"
    assert len(body["winners"]) == 2
    assert body["seed"]


def test_create_draw_with_too_many_winners_returns_422(client, db_session, auth_headers):
    _seed_entries(db_session, 1)
    response = client.post("/draws", json={"winner_count": 5}, headers=auth_headers)
    assert response.status_code == 422


def test_list_draws_returns_past_draws(client, db_session, auth_headers):
    _seed_entries(db_session, 5)
    client.post("/draws", json={"winner_count": 1}, headers=auth_headers)
    client.post("/draws", json={"winner_count": 1}, headers=auth_headers)

    response = client.get("/draws", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_draw_by_id_returns_winners(client, db_session, auth_headers):
    _seed_entries(db_session, 5)
    created = client.post("/draws", json={"winner_count": 2}, headers=auth_headers).json()

    response = client.get(f"/draws/{created['id']}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]
    assert len(response.json()["winners"]) == 2


def test_get_unknown_draw_returns_404(client, auth_headers):
    response = client.get("/draws/999999", headers=auth_headers)
    assert response.status_code == 404
