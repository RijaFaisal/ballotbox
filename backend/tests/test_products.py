from app.models.draw import Draw, DrawStatus
from app.models.winner import Winner
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


def test_get_product_requires_admin(client, db_session):
    product = product_repository.create(db_session, name="Grand Prize")
    response = client.get(f"/products/{product.id}")
    assert response.status_code == 401


def test_get_product_returns_it(client, db_session, auth_headers):
    product = product_repository.create(db_session, name="Grand Prize")
    response = client.get(f"/products/{product.id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Grand Prize"


def test_get_unknown_product_is_404(client, auth_headers):
    response = client.get("/products/999", headers=auth_headers)
    assert response.status_code == 404


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


def _seed_product_with_completed_draw(db_session):
    product = product_repository.create(db_session, name="Grand Prize")
    candidate = candidate_repository.create(
        db_session, product_id=product.id, name="Alice", email="alice@example.com", cnic=None
    )
    draw = Draw(product_id=product.id, seed="seed", winner_count=1, status=DrawStatus.COMPLETED)
    db_session.add(draw)
    db_session.commit()
    db_session.refresh(draw)
    db_session.add(Winner(draw_id=draw.id, candidate_id=candidate.id, position=1))
    db_session.commit()
    return product, candidate, draw


def test_delete_product_requires_admin(client, db_session):
    product = product_repository.create(db_session, name="Grand Prize")
    response = client.delete(f"/products/{product.id}")
    assert response.status_code == 401


def test_delete_unknown_product_is_404(client, auth_headers):
    response = client.delete("/products/999", headers=auth_headers)
    assert response.status_code == 404


def test_delete_product_removes_its_candidates_and_draws(client, db_session, auth_headers):
    product, _candidate, _draw = _seed_product_with_completed_draw(db_session)

    response = client.delete(f"/products/{product.id}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {"candidates_deleted": 1, "draws_deleted": 1, "winners_deleted": 1}
    assert product_repository.get_by_id(db_session, product.id) is None


def test_deleting_one_product_does_not_touch_another(client, db_session, auth_headers):
    keep = product_repository.create(db_session, name="Keep Me")
    candidate_repository.create(
        db_session, product_id=keep.id, name="Bob", email="bob@example.com", cnic=None
    )
    doomed, _candidate, _draw = _seed_product_with_completed_draw(db_session)

    client.delete(f"/products/{doomed.id}", headers=auth_headers)

    assert product_repository.get_by_id(db_session, keep.id) is not None
    remaining = client.get(f"/products/{keep.id}/candidates", headers=auth_headers).json()
    assert len(remaining) == 1


def test_clear_product_candidates_requires_admin(client, db_session):
    product = product_repository.create(db_session, name="Grand Prize")
    response = client.delete(f"/products/{product.id}/candidates")
    assert response.status_code == 401


def test_clear_product_candidates_for_unknown_product_is_404(client, auth_headers):
    response = client.delete("/products/999/candidates", headers=auth_headers)
    assert response.status_code == 404


def test_clear_product_candidates_also_clears_its_draws(client, db_session, auth_headers):
    product, _candidate, _draw = _seed_product_with_completed_draw(db_session)

    response = client.delete(f"/products/{product.id}/candidates", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {"candidates_deleted": 1, "draws_deleted": 1, "winners_deleted": 1}
    assert product_repository.get_by_id(db_session, product.id) is not None
    assert candidate_repository.list_by_product_ordered_by_id(db_session, product.id) == []


def test_clearing_candidates_for_one_product_does_not_touch_another(
    client, db_session, auth_headers
):
    keep = product_repository.create(db_session, name="Keep Me")
    candidate_repository.create(
        db_session, product_id=keep.id, name="Bob", email="bob@example.com", cnic=None
    )
    doomed, _candidate, _draw = _seed_product_with_completed_draw(db_session)

    client.delete(f"/products/{doomed.id}/candidates", headers=auth_headers)

    remaining = candidate_repository.list_by_product_ordered_by_id(db_session, keep.id)
    assert len(remaining) == 1
