from app.repositories import candidate_repository, product_repository


def test_list_products_public_requires_no_auth(client, db_session):
    product_repository.create(db_session, name="Grand Prize")
    response = client.get("/products/public")
    assert response.status_code == 200
    assert response.json() == [{"id": response.json()[0]["id"], "name": "Grand Prize"}]


def test_public_product_list_never_includes_candidate_data(client, db_session):
    product = product_repository.create(db_session, name="Grand Prize")
    candidate_repository.create(
        db_session, product_id=product.id, name="Alice", email="alice@example.com", cnic=None
    )
    response = client.get("/products/public")
    assert response.json() == [{"id": product.id, "name": "Grand Prize"}]


def test_submit_candidate_requires_name(client, db_session):
    product = product_repository.create(db_session, name="Grand Prize")
    response = client.post(
        "/candidates", json={"product_id": product.id, "name": "", "email": "a@example.com"}
    )
    assert response.status_code == 422


def test_submit_candidate_requires_email_or_cnic(client, db_session):
    product = product_repository.create(db_session, name="Grand Prize")
    response = client.post("/candidates", json={"product_id": product.id, "name": "Alice"})
    assert response.status_code == 422


def test_submit_candidate_for_unknown_product_is_404(client):
    response = client.post(
        "/candidates", json={"product_id": 999, "name": "Alice", "email": "a@example.com"}
    )
    assert response.status_code == 404


def test_submit_candidate_success_returns_confirmation(client, db_session):
    product = product_repository.create(db_session, name="Grand Prize")
    response = client.post(
        "/candidates",
        json={"product_id": product.id, "name": "Alice", "email": "alice@example.com"},
    )
    assert response.status_code == 201
    assert response.json() == {"name": "Alice", "product_name": "Grand Prize"}


def test_submit_candidate_never_returns_other_candidates(client, db_session):
    product = product_repository.create(db_session, name="Grand Prize")
    candidate_repository.create(
        db_session, product_id=product.id, name="Existing Person", email="e@example.com", cnic=None
    )
    response = client.post(
        "/candidates",
        json={"product_id": product.id, "name": "Alice", "email": "alice@example.com"},
    )
    assert "Existing Person" not in response.text


def test_duplicate_candidate_is_a_friendly_409(client, db_session):
    product = product_repository.create(db_session, name="Grand Prize")
    client.post(
        "/candidates",
        json={"product_id": product.id, "name": "Alice", "cnic": "12345-1234567-1"},
    )
    response = client.post(
        "/candidates",
        json={"product_id": product.id, "name": "Alice Again", "cnic": "1234512345671"},
    )
    assert response.status_code == 409
    assert "already entered" in response.json()["detail"].lower()


def test_submit_candidate_rejected_when_product_is_closed(client, db_session):
    product = product_repository.create(db_session, name="Grand Prize")
    product_repository.set_open(db_session, product, False)

    response = client.post(
        "/candidates", json={"product_id": product.id, "name": "Alice", "email": "a@example.com"}
    )

    assert response.status_code == 403
    assert "closed" in response.json()["detail"].lower()


def test_closed_product_is_excluded_from_public_list_but_open_ones_are_not(client, db_session):
    open_product = product_repository.create(db_session, name="Open One")
    closed_product = product_repository.create(db_session, name="Closed One")
    product_repository.set_open(db_session, closed_product, False)

    response = client.get("/products/public")

    assert response.status_code == 200
    names = {p["name"] for p in response.json()}
    assert names == {"Open One"}


def test_same_person_can_enter_two_different_products(client, db_session):
    product_a = product_repository.create(db_session, name="Product A")
    product_b = product_repository.create(db_session, name="Product B")

    first = client.post(
        "/candidates",
        json={"product_id": product_a.id, "name": "Alice", "cnic": "12345-1234567-1"},
    )
    second = client.post(
        "/candidates",
        json={"product_id": product_b.id, "name": "Alice", "cnic": "12345-1234567-1"},
    )

    assert first.status_code == 201
    assert second.status_code == 201
