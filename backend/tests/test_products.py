from app.repositories import candidate_repository, product_repository


def test_create_product_requires_admin(client):
    response = client.post("/products", json={"name": "Grand Prize"})
    assert response.status_code == 401


def test_create_and_list_products(client, auth_headers):
    create_response = client.post(
        "/products", json={"name": "Grand Prize"}, headers=auth_headers
    )
    assert create_response.status_code == 201
    body = create_response.json()
    assert body["name"] == "Grand Prize"
    assert "id" in body and "created_at" in body

    list_response = client.get("/products", headers=auth_headers)
    assert list_response.status_code == 200
    assert [p["name"] for p in list_response.json()] == ["Grand Prize"]


def test_duplicate_product_name_is_rejected_case_insensitively(client, auth_headers):
    client.post("/products", json={"name": "Grand Prize"}, headers=auth_headers)

    response = client.post("/products", json={"name": "grand prize"}, headers=auth_headers)

    assert response.status_code == 409


def test_list_products_requires_admin(client):
    response = client.get("/products")
    assert response.status_code == 401


def test_list_candidates_for_product_requires_admin(client, db_session):
    product = product_repository.create(db_session, name="Grand Prize")
    response = client.get(f"/products/{product.id}/candidates")
    assert response.status_code == 401


def test_list_candidates_for_unknown_product_is_404(client, auth_headers):
    response = client.get("/products/999/candidates", headers=auth_headers)
    assert response.status_code == 404


def test_admin_candidate_list_includes_contact_details(client, db_session, auth_headers):
    product = product_repository.create(db_session, name="Grand Prize")
    candidate_repository.create(
        db_session, product_id=product.id, name="Alice", email="alice@example.com", cnic=None
    )
    candidate_repository.create(
        db_session, product_id=product.id, name="Bob", email=None, cnic="1234512345671"
    )

    response = client.get(f"/products/{product.id}/candidates", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body == [
        {
            "id": body[0]["id"],
            "name": "Alice",
            "email": "alice@example.com",
            "cnic": None,
            "created_at": body[0]["created_at"],
        },
        {
            "id": body[1]["id"],
            "name": "Bob",
            "email": None,
            "cnic": "1234512345671",
            "created_at": body[1]["created_at"],
        },
    ]


def test_candidates_for_one_product_are_not_listed_under_another(client, db_session, auth_headers):
    product_a = product_repository.create(db_session, name="Product A")
    product_b = product_repository.create(db_session, name="Product B")
    candidate_repository.create(
        db_session, product_id=product_a.id, name="Alice", email="alice@example.com", cnic=None
    )

    response = client.get(f"/products/{product_b.id}/candidates", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == []
