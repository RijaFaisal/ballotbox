from app.repositories import candidate_repository, product_repository


def _seed_candidates(db_session, product_id, count):
    for i in range(1, count + 1):
        candidate_repository.create(
            db_session,
            product_id=product_id,
            name=f"Person {i}",
            email=f"person{i}@example.com",
            cnic=None,
        )


def test_create_draw_with_no_body_still_defaults_to_one_winner(client, db_session, auth_headers):
    product = product_repository.create(db_session, name="Grand Prize")
    _seed_candidates(db_session, product.id, 5)

    response = client.post(f"/products/{product.id}/draws", headers=auth_headers)

    assert response.status_code == 201
    assert response.json()["winner_count"] == 1


def test_create_draw_selects_the_requested_number_of_winners_in_position_order(
    client, db_session, auth_headers
):
    product = product_repository.create(db_session, name="Grand Prize")
    _seed_candidates(db_session, product.id, 5)

    response = client.post(
        f"/products/{product.id}/draws", json={"winner_count": 3}, headers=auth_headers
    )

    assert response.status_code == 201
    body = response.json()
    assert body["winner_count"] == 3
    assert body["status"] == "completed"
    assert [w["position"] for w in body["winners"]] == [1, 2, 3]
    names = {w["candidate"]["name"] for w in body["winners"]}
    assert len(names) == 3


def test_create_draw_requesting_more_winners_than_candidates_is_422(
    client, db_session, auth_headers
):
    product = product_repository.create(db_session, name="Grand Prize")
    _seed_candidates(db_session, product.id, 2)

    response = client.post(
        f"/products/{product.id}/draws", json={"winner_count": 3}, headers=auth_headers
    )

    assert response.status_code == 422


def test_create_draw_with_zero_winner_count_is_rejected(client, db_session, auth_headers):
    product = product_repository.create(db_session, name="Grand Prize")
    _seed_candidates(db_session, product.id, 5)

    response = client.post(
        f"/products/{product.id}/draws", json={"winner_count": 0}, headers=auth_headers
    )

    assert response.status_code == 422
