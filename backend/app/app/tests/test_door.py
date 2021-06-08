from fastapi import status
from fastapi.testclient import TestClient

from .. import crud, models
from ..core.config import settings


def test_door_access(client: TestClient):
    headers = {"api_key": settings.DOOR_API_KEY}
    response = client.post(
        "/door-access", headers=headers, json={"key": "some-door-id"}
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # unknown code
    response = client.post("/door-access", headers=headers, json={"key": "alex puccio"})
    assert response.status_code == status.HTTP_403_FORBIDDEN
