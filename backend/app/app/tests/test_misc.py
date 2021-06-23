import pytest
from fastapi import status
from fastapi.testclient import TestClient


@pytest.mark.vcr()
def test_opening_hours(client: TestClient):
    response = client.get("/opening-hours")
    assert response.status_code == status.HTTP_200_OK


def test_healtz(client: TestClient):
    response = client.get("/healthz")
    assert response.status_code == status.HTTP_200_OK


def test_docs(client: TestClient):
    response = client.get("/docs")
    assert response.status_code == status.HTTP_200_OK
