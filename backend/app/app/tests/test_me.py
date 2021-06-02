from fastapi.testclient import TestClient


def test_get_me(auth_client_basic: TestClient):
    response = auth_client_basic.get("/me")
    assert response.status_code == 200

    user = response.json()
    assert user["active"] == True


def test_update_me(auth_client_basic: TestClient):
    response = auth_client_basic.patch("/me", json={"name": "new name"})

    assert response.status_code == 200

    user = response.json()

    assert user["name"] == "new name"
