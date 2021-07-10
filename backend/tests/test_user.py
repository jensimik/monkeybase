import datetime
from unittest import mock

import pytest
from backend.app import models, crud
from backend.app.db.base import engine, AsyncSession
from backend.app.core.security import generate_signup_confirm_token
from faker import Faker
from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from pytest_pgsql.time import SQLAlchemyFreezegun


def test_get_user(auth_client_admin: TestClient):
    response = auth_client_admin.get("/users/1")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert "email" in data


def test_get_users(auth_client_admin: TestClient):
    response = auth_client_admin.get("/users")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["has_next"] is True
    assert data["next"] != ""

    assert "items" in data

    user = [u for u in data["items"] if u["member"]][0]

    assert "email" in user

    assert "name" in user

    member = user["member"][0]

    assert "date_start" in member
    assert "date_end" in member

    member_type = member["product"]

    assert "name" in member_type

    # fetch page 2
    response2 = auth_client_admin.get("/users", params={"page": data["next"]})
    assert response2.status_code == 200

    data2 = response2.json()

    items_ids_1 = set([i["id"] for i in data["items"]])
    items_ids_2 = set([i["id"] for i in data2["items"]])

    # make sure no overlap between the two pages
    assert items_ids_1 & items_ids_2 == set()


def test_get_users_page_size(auth_client_admin: TestClient):
    response = auth_client_admin.get("/users", params={"per_page": 10})
    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert len(data["items"]) == 10


def test_create_user(auth_client_admin: TestClient, client: TestClient):
    faker = Faker()
    new_user_dict = {
        "name": faker.name(),
        "email": faker.email(),
        "mobile": "+4581818181",
        "password": faker.password(),
        "birthday": faker.date_of_birth(),
    }
    response = auth_client_admin.post("/users", json=jsonable_encoder(new_user_dict))
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()

    for x in ["name", "email", "birthday"]:
        assert data[x] == str(new_user_dict[x])

    # test login this new user
    response = client.post(
        "/auth/token",
        data={
            "username": new_user_dict["email"],
            "password": new_user_dict["password"],
        },
    )
    assert response.status_code == status.HTTP_200_OK


def test_update_user(auth_client_admin: TestClient, fake_name):
    response = auth_client_admin.get("/users/1")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    response = auth_client_admin.patch("/users/1", json={"name": fake_name})

    assert response.status_code == status.HTTP_200_OK

    data2 = response.json()

    assert data["name"] != data2["name"]
    assert data2["name"] == fake_name


def test_identicon(client: TestClient):
    response = client.get("/users/1/identicon.png")
    assert response.status_code == status.HTTP_200_OK


@mock.patch("backend.app.core.utils._sendgrid_send")
def test_signup(mock_mail_send, client: TestClient):
    faker = Faker()
    new_user_dict = {
        "name": faker.name(),
        "email": faker.email(),
        "mobile": "+4542808080",
        "password": faker.password(),
        "birthday": faker.date_of_birth(),
    }
    response = client.post("/users/signup", json=jsonable_encoder(new_user_dict))
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()

    for x in ["name", "email", "birthday"]:
        assert data[x] == str(new_user_dict[x])

    assert mock_mail_send.called

    # test login this new user (denied because email not confirmed yet)
    response = client.post(
        "/auth/token",
        data={
            "username": new_user_dict["email"],
            "password": new_user_dict["password"],
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # confirm the email
    confirm_token = generate_signup_confirm_token(email=new_user_dict["email"])
    response = client.post(f"/auth/confirm_email/{confirm_token}")
    assert response.status_code == status.HTTP_200_OK

    # test login this new user
    response = client.post(
        "/auth/token",
        data={
            "username": new_user_dict["email"],
            "password": new_user_dict["password"],
        },
    )
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize(
    "c", [pytest.lazy_fixture("auth_client_basic"), pytest.lazy_fixture("client")]
)
def test_no_access(c: TestClient, user_basic: models.User):
    for response in [
        c.get("/users", params={"per_page": 10}),
        c.get(f"/users/{user_basic.id}"),
        c.patch(f"/users/{user_basic.id}", json={"name": "new name"}),
        c.post("/users", json={"name": "new user"}),
        c.delete(f"/users/{user_basic.id}"),
    ]:
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
