from fastapi import status
from fastapi.testclient import TestClient

from backend.app import crud, models
from backend.app.core.config import settings


def test_door_access(client: TestClient):
    headers = {"api_key": settings.DOOR_API_KEY}
    response = client.post(
        "/door-access", headers=headers, json={"key": "some-door-id1"}
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # unknown code
    response = client.post("/door-access", headers=headers, json={"key": "puccio"})
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # TODO: test morning by freeze time
