from app.core.security import hash_password
from app.models.admin import Admin


def _create_second_admin(db_session, username="second"):
    admin = Admin(username=username, password_hash=hash_password("correct-horse-battery"))
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


def test_list_admins_requires_admin(client):
    response = client.get("/admin/users")
    assert response.status_code == 401


def test_list_admins_includes_the_seeded_admin(client, admin, auth_headers):
    response = client.get("/admin/users", headers=auth_headers)
    assert response.status_code == 200
    usernames = {a["username"] for a in response.json()}
    assert usernames == {"root"}


def test_create_admin_requires_admin(client):
    response = client.post("/admin/users", json={"username": "new", "password": "longenough1"})
    assert response.status_code == 401


def test_create_admin_success(client, admin, auth_headers):
    response = client.post(
        "/admin/users",
        json={"username": "new_admin", "password": "longenough1"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "new_admin"
    assert "password" not in body
    assert "password_hash" not in body


def test_create_admin_rejects_short_password(client, admin, auth_headers):
    response = client.post(
        "/admin/users", json={"username": "new_admin", "password": "short"}, headers=auth_headers
    )
    assert response.status_code == 422


def test_create_admin_duplicate_username_is_409(client, admin, auth_headers):
    client.post(
        "/admin/users",
        json={"username": "dupe", "password": "longenough1"},
        headers=auth_headers,
    )
    response = client.post(
        "/admin/users",
        json={"username": "DUPE", "password": "otherlongenough"},
        headers=auth_headers,
    )
    assert response.status_code == 409


def test_new_admin_can_log_in(client, admin, auth_headers):
    client.post(
        "/admin/users",
        json={"username": "new_admin", "password": "longenough1"},
        headers=auth_headers,
    )
    login_response = client.post(
        "/auth/login", json={"username": "new_admin", "password": "longenough1"}
    )
    assert login_response.status_code == 200


def test_delete_admin_requires_admin(client, db_session, admin):
    other = _create_second_admin(db_session)
    response = client.delete(f"/admin/users/{other.id}")
    assert response.status_code == 401


def test_admin_can_delete_another_admin(client, db_session, admin, auth_headers):
    other = _create_second_admin(db_session)

    response = client.delete(f"/admin/users/{other.id}", headers=auth_headers)

    assert response.status_code == 200
    usernames = {a["username"] for a in client.get("/admin/users", headers=auth_headers).json()}
    assert usernames == {"root"}


def test_admin_cannot_delete_own_account(client, admin, auth_headers):
    response = client.delete(f"/admin/users/{admin.id}", headers=auth_headers)
    assert response.status_code == 400
    assert "own" in response.json()["detail"].lower()

    usernames = {a["username"] for a in client.get("/admin/users", headers=auth_headers).json()}
    assert usernames == {"root"}


def test_delete_unknown_admin_is_404(client, admin, auth_headers):
    response = client.delete("/admin/users/999", headers=auth_headers)
    assert response.status_code == 404
