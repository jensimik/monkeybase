import datetime

import pytest
from backend.app import models
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from fastapi import status


def test_get_member_types(client: TestClient):
    response = client.get("/member_types")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["has_next"] is False
    assert data["next"] == ""

    assert len(data["items"]) >= 2


def test_get_members_of_member_type(auth_client_admin: TestClient, member_type_id=1):
    response = auth_client_admin.get(f"/member_types/{member_type_id}/members")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["has_next"] is False
    assert data["next"] == ""

    assert len(data["items"]) >= 2


def test_get_member_type(client: TestClient, member_type_id=1):
    response = client.get(f"/member_types/{member_type_id}")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["id"] == member_type_id

    # non existing id
    response = client.get("/member_type/999999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_create_member_type(auth_client_admin: TestClient):
    new_member_type = {"name": "new_member_type", "name_short": "nmt"}
    response = auth_client_admin.post("/member_types", json=new_member_type)
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()

    assert new_member_type["name"] == data["name"]

    test_get_member_type(client=auth_client_admin, member_type_id=data["id"])


def test_patch_member_type(auth_client_admin: TestClient, fake_name: str):
    response = auth_client_admin.patch("/member_types/1", json={"name": fake_name})
    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["name"] == fake_name

    # unknown id
    response = auth_client_admin.patch("/member_types/999999", json={"name": fake_name})
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_member_type(auth_client_admin: TestClient):
    new_member_type = {"name": "new_member_type", "name_short": "nmt"}
    response = auth_client_admin.post("/member_types", json=new_member_type)
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()

    id = data["id"]

    response = auth_client_admin.delete(f"/member_types/{id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = auth_client_admin.get(f"/member_types/{id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND

    # remove a member_type with members

    response = auth_client_admin.delete(f"/member_types/1")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_reserve_a_slot(auth_client_basic: TestClient):
    response = auth_client_basic.post("/member_types/1/reserve_a_slot")
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize(
    "c", [pytest.lazy_fixture("auth_client_basic"), pytest.lazy_fixture("client")]
)
def test_no_access(c: TestClient):
    for response in [
        c.patch("/member_types/1", json={"name": "new name"}),
        c.post("/member_types", json={"name": "new user"}),
        c.delete("/member_types/1"),
    ]:
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
