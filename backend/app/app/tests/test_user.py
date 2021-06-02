import datetime

import pytest
from app import models
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient


def test_get_users(auth_client_admin: TestClient):
    response = auth_client_admin.get("/users")
    assert response.status_code == 200

    data = response.json()

    assert "has_next" in data

    assert "next" in data

    assert "items" in data

    user = [u for u in data["items"] if u["member"]][0]

    assert "email" in user

    assert "name" in user

    member = user["member"][0]

    assert "date_start" in member
    assert "date_end" in member

    member_type = member["member_type"]

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
    assert response.status_code == 200

    data = response.json()

    assert len(data["items"]) == 10


def test_create_user(auth_client_admin: TestClient):
    new_user_dict = {
        "name": "new user",
        "email": "test-create-user@test.dk",
        "password": "humn",
        "birthday": datetime.date.today(),
    }
    response = auth_client_admin.post("/users", json=jsonable_encoder(new_user_dict))
    assert response.status_code == 200

    data = response.json()

    for x in ["name", "email", "birthday"]:
        assert data[x] == new_user_dict[x]


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
        assert response.status_code == 401
