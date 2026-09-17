def test_ballot_status_defaults_to_open(client):
    response = client.get("/ballot/status")
    assert response.status_code == 200
    assert response.json() == {"is_open": True}


def test_toggle_requires_admin(client):
    response = client.post("/ballot/toggle")
    assert response.status_code == 401


def test_admin_can_close_and_reopen_ballot(client, auth_headers):
    close_response = client.post("/ballot/toggle", headers=auth_headers)
    assert close_response.status_code == 200
    assert close_response.json() == {"is_open": False}
    assert client.get("/ballot/status").json() == {"is_open": False}

    reopen_response = client.post("/ballot/toggle", headers=auth_headers)
    assert reopen_response.status_code == 200
    assert reopen_response.json() == {"is_open": True}
    assert client.get("/ballot/status").json() == {"is_open": True}
