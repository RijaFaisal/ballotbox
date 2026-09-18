from app.repositories import product_repository


def _upload(client, headers, content: bytes, filename: str = "products.csv"):
    return client.post(
        "/products/bulk-upload",
        files={"file": (filename, content, "text/csv")},
        headers=headers,
    )


def test_bulk_upload_requires_admin(client):
    response = _upload(client, {}, b"name\nGrand Prize\n")
    assert response.status_code == 401


def test_bulk_upload_creates_products_from_valid_csv(client, db_session, auth_headers):
    csv_bytes = b"name\nGrand Prize\nRunner Up\n"

    response = _upload(client, auth_headers, csv_bytes)

    assert response.status_code == 200
    body = response.json()
    assert body == {"created_count": 2, "skipped": []}
    names = {p.name for p in product_repository.list_all_ordered_by_created_at(db_session)}
    assert names == {"Grand Prize", "Runner Up"}


def test_bulk_upload_skips_blank_name_rows(client, auth_headers):
    # A truly empty line is invisible to the csv module (skipped entirely,
    # like a trailing newline) -- a whitespace-only line is what actually
    # produces a row whose name is blank after stripping.
    csv_bytes = b"name\nGrand Prize\n   \n"

    response = _upload(client, auth_headers, csv_bytes)

    assert response.status_code == 200
    body = response.json()
    assert body["created_count"] == 1
    assert body["skipped"] == [{"row": 2, "name": "", "reason": "blank name"}]


def test_bulk_upload_skips_duplicate_within_file_case_insensitively(client, auth_headers):
    csv_bytes = b"name\nGrand Prize\ngrand prize\nGRAND PRIZE\n"

    response = _upload(client, auth_headers, csv_bytes)

    body = response.json()
    assert body["created_count"] == 1
    assert len(body["skipped"]) == 2
    assert all(s["reason"] == "duplicate in file" for s in body["skipped"])
    assert [s["row"] for s in body["skipped"]] == [2, 3]


def test_bulk_upload_skips_names_that_already_exist_in_db(client, db_session, auth_headers):
    product_repository.create(db_session, name="Grand Prize")
    csv_bytes = b"name\ngrand prize\nNew One\n"

    response = _upload(client, auth_headers, csv_bytes)

    body = response.json()
    assert body["created_count"] == 1
    assert body["skipped"] == [{"row": 1, "name": "grand prize", "reason": "already exists"}]


def test_bulk_upload_reports_mixed_valid_and_invalid_rows(client, db_session, auth_headers):
    product_repository.create(db_session, name="Existing")
    csv_bytes = (
        b"name\n"
        b"Valid One\n"
        b"   \n"
        b"Existing\n"
        b"Valid One\n"
        b"Valid Two\n"
    )

    response = _upload(client, auth_headers, csv_bytes)

    body = response.json()
    assert body["created_count"] == 2
    reasons = {(s["row"], s["reason"]) for s in body["skipped"]}
    assert reasons == {
        (2, "blank name"),
        (3, "already exists"),
        (4, "duplicate in file"),
    }


def test_bulk_upload_empty_file_is_400(client, auth_headers):
    response = _upload(client, auth_headers, b"")
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_bulk_upload_whitespace_only_file_is_400(client, auth_headers):
    response = _upload(client, auth_headers, b"   \n\n  ")
    assert response.status_code == 400


def test_bulk_upload_missing_name_column_is_400(client, auth_headers):
    csv_bytes = b"product_name\nGrand Prize\n"
    response = _upload(client, auth_headers, csv_bytes)
    assert response.status_code == 400
    assert "name" in response.json()["detail"].lower()


def test_bulk_upload_undecodable_file_is_400(client, auth_headers):
    response = _upload(client, auth_headers, b"\xff\xfe\x00\x01garbage")
    assert response.status_code == 400


def test_bulk_upload_header_is_case_insensitive(client, db_session, auth_headers):
    csv_bytes = b"NAME\nGrand Prize\n"
    response = _upload(client, auth_headers, csv_bytes)
    assert response.status_code == 200
    assert response.json()["created_count"] == 1
