from app.repositories import candidate_repository, product_repository


def test_export_requires_admin(client, db_session):
    product = product_repository.create(db_session, name="Grand Prize")
    response = client.get(f"/products/{product.id}/candidates/export")
    assert response.status_code == 401


def test_export_unknown_product_is_404(client, auth_headers):
    response = client.get("/products/999/candidates/export", headers=auth_headers)
    assert response.status_code == 404


def test_export_contains_header_and_rows(client, db_session, auth_headers):
    product = product_repository.create(db_session, name="Grand Prize")
    candidate_repository.create(
        db_session, product_id=product.id, name="Alice", email="alice@example.com", cnic=None
    )
    candidate_repository.create(
        db_session, product_id=product.id, name="Bob", email=None, cnic="1234512345671"
    )

    response = client.get(f"/products/{product.id}/candidates/export", headers=auth_headers)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    lines = response.text.strip().splitlines()
    assert lines[0] == "name,email,cnic,created_at"
    assert lines[1].startswith("Alice,alice@example.com,,")
    assert lines[2].startswith("Bob,,1234512345671,")


def test_export_with_no_candidates_is_header_only(client, db_session, auth_headers):
    product = product_repository.create(db_session, name="Grand Prize")

    response = client.get(f"/products/{product.id}/candidates/export", headers=auth_headers)

    assert response.status_code == 200
    assert response.text.strip() == "name,email,cnic,created_at"


def test_export_filename_is_sanitized(client, db_session, auth_headers):
    product = product_repository.create(db_session, name='Weird "Name"\r\nX-Injected: yes')

    response = client.get(f"/products/{product.id}/candidates/export", headers=auth_headers)

    assert response.status_code == 200
    disposition = response.headers["content-disposition"]
    assert "\r" not in disposition and "\n" not in disposition
    assert "X-Injected" not in response.headers
