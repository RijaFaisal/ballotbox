from app.repositories import product_repository


def test_toggle_requires_admin(client, db_session):
    product = product_repository.create(db_session, name="Grand Prize")
    response = client.post(f"/products/{product.id}/open", json={"is_open": False})
    assert response.status_code == 401


def test_new_product_defaults_to_open(client, auth_headers):
    response = client.post("/products", json={"name": "Grand Prize"}, headers=auth_headers)
    assert response.status_code == 201
    assert response.json()["is_open"] is True


def test_admin_can_close_and_reopen_one_product_without_affecting_another(
    client, db_session, auth_headers
):
    product_a = product_repository.create(db_session, name="Product A")
    product_b = product_repository.create(db_session, name="Product B")

    close_response = client.post(
        f"/products/{product_a.id}/open", json={"is_open": False}, headers=auth_headers
    )
    assert close_response.status_code == 200
    assert close_response.json()["is_open"] is False

    products = client.get("/products", headers=auth_headers).json()
    by_id = {p["id"]: p["is_open"] for p in products}
    assert by_id[product_a.id] is False
    assert by_id[product_b.id] is True


def test_toggle_unknown_product_is_404(client, auth_headers):
    response = client.post("/products/999/open", json={"is_open": False}, headers=auth_headers)
    assert response.status_code == 404
