import datetime as dt

import pytest

from app.core.security import create_access_token, hash_password
from app.models.admin import Admin


@pytest.fixture()
def admin(db_session):
    admin = Admin(username="root", password_hash=hash_password("correct-horse-battery"))
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


def test_login_with_correct_credentials_returns_token(client, admin):
    response = client.post(
        "/auth/login", json={"username": "root", "password": "correct-horse-battery"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_with_wrong_password_returns_401(client, admin):
    response = client.post("/auth/login", json={"username": "root", "password": "wrong"})
    assert response.status_code == 401


def test_login_with_unknown_username_returns_401(client):
    response = client.post("/auth/login", json={"username": "ghost", "password": "whatever"})
    assert response.status_code == 401


def test_login_failure_message_does_not_reveal_which_field_was_wrong(client, admin):
    wrong_password = client.post(
        "/auth/login", json={"username": "root", "password": "wrong"}
    )
    wrong_username = client.post(
        "/auth/login", json={"username": "ghost", "password": "whatever"}
    )
    assert wrong_password.json()["detail"] == wrong_username.json()["detail"]


def test_protected_route_rejects_request_with_no_token(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_protected_route_rejects_tampered_token(client, admin):
    token = create_access_token(subject=admin.username)
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {tampered}"})
    assert response.status_code == 401


def test_protected_route_rejects_expired_token(client, admin):
    expired_token = create_access_token(
        subject=admin.username, expires_delta=dt.timedelta(minutes=-1)
    )
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert response.status_code == 401


def test_protected_route_accepts_valid_token(client, admin):
    login_response = client.post(
        "/auth/login", json={"username": "root", "password": "correct-horse-battery"}
    )
    token = login_response.json()["access_token"]

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["username"] == "root"
