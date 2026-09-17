from app.repositories import candidate_repository, product_repository
from app.services.draw_service import run_draw


def _seed_product_with_candidates(db_session, count: int):
    product = product_repository.create(db_session, name="Grand Prize")
    for i in range(1, count + 1):
        candidate_repository.create(
            db_session,
            product_id=product.id,
            name=f"Person {i}",
            email=f"person{i}@example.com",
            cnic=None,
        )
    return product


def test_reset_requires_admin(client):
    response = client.post("/admin/reset", json={"confirm": "RESET"})
    assert response.status_code == 401


def test_reset_rejects_wrong_confirmation_phrase(client, db_session, auth_headers):
    product = _seed_product_with_candidates(db_session, 3)

    response = client.post("/admin/reset", json={"confirm": "yes"}, headers=auth_headers)

    assert response.status_code == 400
    # nothing was deleted
    assert len(candidate_repository.list_by_product_ordered_by_id(db_session, product.id)) == 3


def test_reset_clears_products_candidates_draws_and_winners(client, db_session, auth_headers):
    product = _seed_product_with_candidates(db_session, 5)
    draw = run_draw(db_session, product_id=product.id, winner_count=1)
    assert len(candidate_repository.list_by_product_ordered_by_id(db_session, product.id)) == 5

    response = client.post("/admin/reset", json={"confirm": "RESET"}, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "products_deleted": 1,
        "candidates_deleted": 5,
        "draws_deleted": 1,
        "winners_deleted": 1,
    }

    assert product_repository.list_all_ordered_by_created_at(db_session) == []
    assert candidate_repository.list_by_product_ordered_by_id(db_session, product.id) == []


def test_dashboard_shows_zero_products_after_reset(client, db_session, auth_headers):
    _seed_product_with_candidates(db_session, 4)

    client.post("/admin/reset", json={"confirm": "RESET"}, headers=auth_headers)
    response = client.get("/products", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == []


def test_reset_does_not_touch_admin_accounts(client, db_session, auth_headers):
    _seed_product_with_candidates(db_session, 2)

    response = client.post("/admin/reset", json={"confirm": "RESET"}, headers=auth_headers)
    assert response.status_code == 200

    # the same admin token still works after the reset
    me_response = client.get("/auth/me", headers=auth_headers)
    assert me_response.status_code == 200
