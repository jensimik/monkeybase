import datetime

import pytest
import sqlalchemy as sa
from ..db.base import engine
from pytest_pgsql.time import SQLAlchemyFreezegun

from .. import crud, models


# db, time,
def test_slots(db, client, user_admin):
    # q = sa.select(models.Member).where(models.Member.active == True)
    # assert len(db.execute(q).scalars().all()) == 80

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
