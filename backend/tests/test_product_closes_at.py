import datetime as dt

from app.repositories import product_repository

FUTURE = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1)).isoformat()
PAST = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=1)).isoformat()


def test_new_product_has_no_schedule_by_default(client, auth_headers):
    response = client.post("/products", json={"name": "Grand Prize"}, headers=auth_headers)
    assert response.status_code == 201
    body = response.json()
    assert body["closes_at"] is None
    assert body["effectively_open"] is True


def test_product_created_with_a_future_close_time_is_effectively_open(client, auth_headers):
    response = client.post(
        "/products", json={"name": "Grand Prize", "closes_at": FUTURE}, headers=auth_headers
    )
    assert response.status_code == 201
    body = response.json()
    assert body["closes_at"] is not None
    assert body["effectively_open"] is True


def test_product_created_with_a_past_close_time_is_effectively_closed(client, auth_headers):
    response = client.post(
        "/products", json={"name": "Grand Prize", "closes_at": PAST}, headers=auth_headers
    )
    assert response.status_code == 201
    assert response.json()["effectively_open"] is False


def test_a_passed_schedule_closes_entries_even_though_is_open_is_still_true(
    client, db_session, auth_headers
):
    product = product_repository.create(
        db_session, name="Grand Prize", closes_at=dt.datetime.fromisoformat(PAST)
    )
    assert product.is_open is True

    response = client.post(
        "/candidates",
        json={"product_id": product.id, "name": "Alice", "email": "alice@example.com"},
    )

    assert response.status_code == 403


def test_public_product_list_excludes_a_product_past_its_schedule(
    client, db_session, auth_headers
):
    open_product = product_repository.create(db_session, name="Open One")
    expired_product = product_repository.create(
        db_session, name="Expired One", closes_at=dt.datetime.fromisoformat(PAST)
    )

    names = {p["name"] for p in client.get("/products/public").json()}

    assert open_product.name in names
    assert expired_product.name not in names


def test_dashboard_summary_does_not_count_an_expired_product_as_open(
    client, db_session, auth_headers
):
    product_repository.create(db_session, name="Expired One", closes_at=dt.datetime.fromisoformat(PAST))

    summary = client.get("/products/summary", headers=auth_headers).json()

    assert summary["open_product_count"] == 0


def test_admin_can_set_and_clear_a_products_schedule(client, db_session, auth_headers):
    product = product_repository.create(db_session, name="Grand Prize")

    close_response = client.post(
        f"/products/{product.id}/closes-at", json={"closes_at": PAST}, headers=auth_headers
    )
    assert close_response.status_code == 200
    assert close_response.json()["effectively_open"] is False

    clear_response = client.post(
        f"/products/{product.id}/closes-at", json={"closes_at": None}, headers=auth_headers
    )
    assert clear_response.status_code == 200
    assert clear_response.json()["closes_at"] is None
    assert clear_response.json()["effectively_open"] is True


def test_set_closes_at_requires_admin(client, db_session):
    product = product_repository.create(db_session, name="Grand Prize")
    response = client.post(f"/products/{product.id}/closes-at", json={"closes_at": None})
    assert response.status_code == 401


def test_set_closes_at_for_unknown_product_is_404(client, auth_headers):
    response = client.post("/products/999/closes-at", json={"closes_at": None}, headers=auth_headers)
    assert response.status_code == 404
