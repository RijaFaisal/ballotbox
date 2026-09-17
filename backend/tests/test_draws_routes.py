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


def test_create_draw_requires_admin(client, db_session):
    product = product_repository.create(db_session, name="Grand Prize")
    response = client.post(f"/products/{product.id}/draws")
    assert response.status_code == 401


def test_create_draw_for_unknown_product_is_404(client, auth_headers):
    response = client.post("/products/999/draws", headers=auth_headers)
    assert response.status_code == 404


def test_create_draw_selects_exactly_one_winner(client, db_session, auth_headers):
    product = product_repository.create(db_session, name="Grand Prize")
    _seed_candidates(db_session, product.id, 5)

    response = client.post(f"/products/{product.id}/draws", headers=auth_headers)

    assert response.status_code == 201
    body = response.json()
    assert body["winner_count"] == 1
    assert body["status"] == "completed"
    assert len(body["winners"]) == 1
    assert body["product_id"] == product.id


def test_create_draw_with_no_candidates_is_422(client, db_session, auth_headers):
    product = product_repository.create(db_session, name="Grand Prize")
    response = client.post(f"/products/{product.id}/draws", headers=auth_headers)
    assert response.status_code == 422


def test_a_redo_creates_a_new_draw_with_a_new_seed_and_keeps_both(client, db_session, auth_headers):
    product = product_repository.create(db_session, name="Grand Prize")
    _seed_candidates(db_session, product.id, 5)

    first = client.post(f"/products/{product.id}/draws", headers=auth_headers).json()
    second = client.post(f"/products/{product.id}/draws", headers=auth_headers).json()

    assert first["id"] != second["id"]
    assert first["seed"] != second["seed"]

    history = client.get(f"/products/{product.id}/draws", headers=auth_headers).json()
    assert {d["id"] for d in history} == {first["id"], second["id"]}


def test_winning_one_product_does_not_exclude_a_candidate_from_another(
    client, db_session, auth_headers
):
    product_a = product_repository.create(db_session, name="Product A")
    product_b = product_repository.create(db_session, name="Product B")
    candidate_repository.create(
        db_session, product_id=product_a.id, name="Alice", email="alice@a.com", cnic=None
    )
    candidate_repository.create(
        db_session, product_id=product_b.id, name="Alice", email="alice@b.com", cnic=None
    )

    draw_a = client.post(f"/products/{product_a.id}/draws", headers=auth_headers).json()
    draw_b = client.post(f"/products/{product_b.id}/draws", headers=auth_headers).json()

    assert draw_a["winners"][0]["candidate"]["name"] == "Alice"
    assert draw_b["winners"][0]["candidate"]["name"] == "Alice"


def test_get_draw_from_wrong_product_is_404(client, db_session, auth_headers):
    product_a = product_repository.create(db_session, name="Product A")
    product_b = product_repository.create(db_session, name="Product B")
    _seed_candidates(db_session, product_a.id, 3)
    draw = client.post(f"/products/{product_a.id}/draws", headers=auth_headers).json()

    response = client.get(f"/products/{product_b.id}/draws/{draw['id']}", headers=auth_headers)

    assert response.status_code == 404


def test_export_draw_winner_pdf(client, db_session, auth_headers):
    product = product_repository.create(db_session, name="Grand Prize")
    _seed_candidates(db_session, product.id, 3)
    draw = client.post(f"/products/{product.id}/draws", headers=auth_headers).json()

    response = client.get(
        f"/products/{product.id}/draws/{draw['id']}/export", headers=auth_headers
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content[:4] == b"%PDF"


def test_clear_draws_requires_admin(client, db_session):
    product = product_repository.create(db_session, name="Grand Prize")
    response = client.delete(f"/products/{product.id}/draws")
    assert response.status_code == 401


def test_clear_draws_for_unknown_product_is_404(client, auth_headers):
    response = client.delete("/products/999/draws", headers=auth_headers)
    assert response.status_code == 404


def test_clear_draws_keeps_candidates_and_allows_a_fresh_draw(client, db_session, auth_headers):
    product = product_repository.create(db_session, name="Grand Prize")
    _seed_candidates(db_session, product.id, 3)
    client.post(f"/products/{product.id}/draws", headers=auth_headers)

    response = client.delete(f"/products/{product.id}/draws", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {"draws_deleted": 1, "winners_deleted": 1}

    history = client.get(f"/products/{product.id}/draws", headers=auth_headers).json()
    assert history == []

    candidates = client.get(f"/products/{product.id}/candidates", headers=auth_headers).json()
    assert len(candidates) == 3

    redraw = client.post(f"/products/{product.id}/draws", headers=auth_headers)
    assert redraw.status_code == 201


def test_clearing_draws_for_one_product_does_not_touch_another(client, db_session, auth_headers):
    product_a = product_repository.create(db_session, name="Product A")
    product_b = product_repository.create(db_session, name="Product B")
    _seed_candidates(db_session, product_a.id, 3)
    _seed_candidates(db_session, product_b.id, 3)
    client.post(f"/products/{product_a.id}/draws", headers=auth_headers)
    client.post(f"/products/{product_b.id}/draws", headers=auth_headers)

    client.delete(f"/products/{product_a.id}/draws", headers=auth_headers)

    assert client.get(f"/products/{product_a.id}/draws", headers=auth_headers).json() == []
    assert len(client.get(f"/products/{product_b.id}/draws", headers=auth_headers).json()) == 1


def test_export_pdf_filename_is_sanitized_against_header_injection(
    client, db_session, auth_headers
):
    product = product_repository.create(db_session, name='Weird "Name"\r\nX-Injected: yes')
    _seed_candidates(db_session, product.id, 2)
    draw = client.post(f"/products/{product.id}/draws", headers=auth_headers).json()

    response = client.get(
        f"/products/{product.id}/draws/{draw['id']}/export", headers=auth_headers
    )

    assert response.status_code == 200
    disposition = response.headers["content-disposition"]
    assert "\r" not in disposition and "\n" not in disposition
    assert "X-Injected" not in response.headers
