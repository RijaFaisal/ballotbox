from app.repositories import login_event_repository


def test_successful_login_is_recorded(client, admin, auth_headers):
    response = client.post(
        "/auth/login", json={"username": "root", "password": "correct-horse-battery"}
    )
    assert response.status_code == 200

    events = client.get("/admin/users/login-events", headers=auth_headers).json()
    matching = [e for e in events if e["username"] == "root" and e["success"] is True]
    assert len(matching) == 1
    assert matching[0]["admin_id"] == admin.id


def test_failed_login_against_a_real_username_is_recorded_with_its_admin_id(
    client, admin, auth_headers
):
    response = client.post("/auth/login", json={"username": "root", "password": "wrong"})
    assert response.status_code == 401

    events = client.get("/admin/users/login-events", headers=auth_headers).json()
    matching = [e for e in events if e["username"] == "root" and e["success"] is False]
    assert len(matching) == 1
    assert matching[0]["admin_id"] == admin.id


def test_failed_login_against_an_unknown_username_has_no_admin_id(client, auth_headers):
    response = client.post("/auth/login", json={"username": "ghost", "password": "whatever"})
    assert response.status_code == 401

    events = client.get("/admin/users/login-events", headers=auth_headers).json()
    matching = [e for e in events if e["username"] == "ghost"]
    assert len(matching) == 1
    assert matching[0]["admin_id"] is None
    assert matching[0]["success"] is False


def test_login_events_are_most_recent_first(client, db_session, admin, auth_headers):
    login_event_repository.create(
        db_session, admin_id=admin.id, username="root", success=True, ip_address="10.0.0.1"
    )
    login_event_repository.create(
        db_session, admin_id=admin.id, username="root", success=True, ip_address="10.0.0.2"
    )

    events = client.get("/admin/users/login-events", headers=auth_headers).json()

    assert events[0]["ip_address"] == "10.0.0.2"
    assert events[1]["ip_address"] == "10.0.0.1"


def test_list_login_events_requires_admin(client):
    response = client.get("/admin/users/login-events")
    assert response.status_code == 401
