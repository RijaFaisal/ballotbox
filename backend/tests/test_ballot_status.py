from app.repositories import entry_repository
from app.services.draw_service import run_draw


def _seed_entries(db_session, count: int) -> None:
    for i in range(1, count + 1):
        entry_repository.create(
            db_session, name=f"Person {i}", identifier=f"person{i}@example.com"
        )


def test_ballot_status_defaults_to_open(client):
    response = client.get("/ballot/status")
    assert response.status_code == 200
    assert response.json() == {"is_open": True}


def test_toggle_requires_admin(client):
    response = client.post("/ballot/toggle")
    assert response.status_code == 401


def test_admin_can_close_and_reopen_ballot(client, auth_headers):
    close_response = client.post("/ballot/toggle", headers=auth_headers)
    assert close_response.status_code == 200
    assert close_response.json() == {"is_open": False}
    assert client.get("/ballot/status").json() == {"is_open": False}

    reopen_response = client.post("/ballot/toggle", headers=auth_headers)
    assert reopen_response.status_code == 200
    assert reopen_response.json() == {"is_open": True}
    assert client.get("/ballot/status").json() == {"is_open": True}


def test_entry_rejected_when_ballot_closed(client, auth_headers):
    client.post("/ballot/toggle", headers=auth_headers)  # close it

    response = client.post(
        "/entries", json={"name": "Alice", "identifier": "alice@example.com"}
    )

    assert response.status_code == 403
    assert "closed" in response.json()["detail"].lower()


def test_entry_accepted_after_ballot_reopened(client, auth_headers):
    client.post("/ballot/toggle", headers=auth_headers)  # close
    client.post("/ballot/toggle", headers=auth_headers)  # reopen

    response = client.post(
        "/entries", json={"name": "Alice", "identifier": "alice@example.com"}
    )

    assert response.status_code == 201


def test_draw_still_works_when_ballot_is_closed(client, db_session, auth_headers):
    _seed_entries(db_session, 5)
    client.post("/ballot/toggle", headers=auth_headers)  # close entries only

    response = client.post("/draws", json={"winner_count": 2}, headers=auth_headers)

    assert response.status_code == 201
    assert response.json()["status"] == "completed"


def test_draw_still_works_when_ballot_is_closed_via_service(db_session):
    # Same check at the service layer, independent of the HTTP client fixture,
    # to make sure closing the ballot never touches draw_service itself.
    _seed_entries(db_session, 3)
    from app.repositories import ballot_settings_repository

    ballot_settings_repository.set_open(db_session, False)

    draw = run_draw(db_session, winner_count=2)

    assert draw.status.value == "completed"
