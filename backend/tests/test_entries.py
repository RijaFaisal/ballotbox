def test_create_entry_with_email(client):
    response = client.post("/entries", json={"name": "Alice", "identifier": "alice@example.com"})
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Alice"
    assert "identifier" not in body


def test_create_entry_with_cnic(client):
    response = client.post("/entries", json={"name": "Bilal", "identifier": "12345-1234567-1"})
    assert response.status_code == 201


def test_duplicate_email_rejected(client):
    client.post("/entries", json={"name": "Ayesha", "identifier": "ayesha@example.com"})
    response = client.post(
        "/entries", json={"name": "Ayesha Clone", "identifier": "ayesha@example.com"}
    )
    assert response.status_code == 409


def test_cnic_dedup_ignores_formatting(client):
    first = client.post("/entries", json={"name": "Faisal", "identifier": "12345-1234567-1"})
    assert first.status_code == 201
    second = client.post(
        "/entries", json={"name": "Faisal Clone", "identifier": "1234512345671"}
    )
    assert second.status_code == 409


def test_invalid_identifier_rejected(client):
    response = client.post("/entries", json={"name": "Zara", "identifier": "not-an-identifier"})
    assert response.status_code == 422


def test_blank_name_rejected(client):
    response = client.post("/entries", json={"name": "   ", "identifier": "zara@example.com"})
    assert response.status_code == 422


def test_list_entries_requires_admin(client):
    response = client.get("/entries")
    assert response.status_code == 401


def test_list_entries_returns_names_without_identifiers(client, auth_headers):
    client.post("/entries", json={"name": "Alice", "identifier": "alice@example.com"})
    client.post("/entries", json={"name": "Bilal", "identifier": "12345-1234567-1"})

    response = client.get("/entries", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert {entry["name"] for entry in body} == {"Alice", "Bilal"}
    for entry in body:
        assert set(entry.keys()) == {"id", "name", "created_at"}
