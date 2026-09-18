from app.repositories import candidate_repository, product_repository


def test_summary_requires_admin(client):
    response = client.get("/products/summary")
    assert response.status_code == 401


def test_summary_counts_are_accurate(client, db_session, auth_headers):
    product_a = product_repository.create(db_session, name="Product A")
    product_b = product_repository.create(db_session, name="Product B")
    product_repository.set_open(db_session, product_b, False)
    candidate_repository.create(
        db_session, product_id=product_a.id, name="Alice", email="a@example.com", cnic=None
    )
    candidate_repository.create(
        db_session, product_id=product_a.id, name="Bob", email="b@example.com", cnic=None
    )
    candidate_repository.create(
        db_session, product_id=product_b.id, name="Carl", email="c@example.com", cnic=None
    )

    response = client.get("/products/summary", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {
        "product_count": 2,
        "open_product_count": 1,
        "candidate_count": 3,
    }


def test_summary_with_no_data(client, auth_headers):
    response = client.get("/products/summary", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == {
        "product_count": 0,
        "open_product_count": 0,
        "candidate_count": 0,
    }
