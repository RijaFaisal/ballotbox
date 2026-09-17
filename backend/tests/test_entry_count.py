def test_entry_count_starts_at_zero(client):
    response = client.get("/entries/count")
    assert response.status_code == 200
    assert response.json() == {"count": 0}


def test_entry_count_is_public(client):
    # no Authorization header at all
    response = client.get("/entries/count")
    assert response.status_code == 200


def test_entry_count_increases_after_submission(client):
    client.post("/entries", json={"name": "Alice", "identifier": "alice@example.com"})
    client.post("/entries", json={"name": "Bilal", "identifier": "12345-1234567-1"})

    response = client.get("/entries/count")

    assert response.status_code == 200
    assert response.json() == {"count": 2}


def test_entry_count_response_has_no_other_fields(client):
    client.post("/entries", json={"name": "Alice", "identifier": "alice@example.com"})
    response = client.get("/entries/count")
    assert set(response.json().keys()) == {"count"}
