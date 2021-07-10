import datetime

import pytest
import sqlalchemy as sa
from fastapi import status
from fastapi.testclient import TestClient
from pytest_pgsql.time import SQLAlchemyFreezegun

from backend.app import crud, models
from backend.app.db.base import engine


@pytest.mark.vcr()
def test_slots(auth_client_basic: TestClient):

    # no free slot in member_type 2 - return waiting list 429
    response = auth_client_basic.post("/member_types/2/reserve-a-slot")

    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    # get the free slot in member_type 1
    response = auth_client_basic.post("/member_types/1/reserve-a-slot")

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    slot_key = data["key"]

    # do stripe testing

    response = auth_client_basic.post(f"/slots/{slot_key}/create-payment-intent")

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert "secret" in data["client_secret"]

    # do nets easy testing

    response = auth_client_basic.post(f"/slots/{slot_key}/create-payment-id")

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert "payment_id" in data


def test_member(db, client, user_admin):

    response = client.post(
        "/auth/token", data={"username": user_admin.email, "password": "admin"}
    )
    access_token = response.json()
    token = access_token["access_token"]
    client.headers.update({"Authorization": f"bearer {token}"})

    resp = client.get("/members")

    data = resp.json()

    assert len(data["items"]) >= 50

    # check if no members in far future
    freezer = SQLAlchemyFreezegun(engine.sync_engine)
    with freezer.freeze("2050-01-01"):
        response = client.post(
            "/auth/token", data={"username": user_admin.email, "password": "admin"}
        )
        access_token = response.json()
        token = access_token["access_token"]
        client.headers.update({"Authorization": f"bearer {token}"})

        resp = client.get("/members")

        data = resp.json()

        assert len(data["items"]) == 0
