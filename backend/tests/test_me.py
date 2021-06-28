import pytest
from faker import Faker
from fastapi import status
from fastapi.testclient import TestClient


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


@pytest.mark.parametrize("c", [pytest.lazy_fixture("client")])
def test_no_access(c: TestClient):
    for response in [
        c.get("/me"),
        c.patch("/me", json={"name": "new name"}),
        c.get("/me/members"),
    ]:
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
