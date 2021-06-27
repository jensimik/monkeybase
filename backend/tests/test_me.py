from fastapi.testclient import TestClient
from faker import Faker


def test_get_me(auth_client_basic: TestClient):
    response = auth_client_basic.get("/me")
    assert response.status_code == 200

    user = response.json()
    assert user["active"] == True


def test_update_me(auth_client_basic: TestClient, fake_name):
    response = auth_client_basic.patch("/me", json={"name": fake_name})

    assert response.status_code == 200

    user = response.json()

    assert user["name"] == fake_name

    response = auth_client_basic.get("/me")

    user_refresh = response.json()

    assert user_refresh["name"] == fake_name


def test_me_get_members(auth_client_basic: TestClient):
    response = auth_client_basic.get("/me/members")
    assert response.status_code == 200
