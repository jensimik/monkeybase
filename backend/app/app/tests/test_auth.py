from fastapi.testclient import TestClient
from .. import models
from ..core.utils import generate_password_reset_token, verify_password_reset_token
from ..core.security import get_password_hash, verify_password, ALGORITHM
from ..core.config import settings
from jose import jwt


def test_password_reset_token():
    # correct
    email = "test@test.dk"
    token = generate_password_reset_token(email)
    assert verify_password_reset_token(token) == email

    # wrong returns None
    assert verify_password_reset_token("gibberish") is None


def test_password_hash_verify():
    password = "some_g8_password"
    password_wrong = "wrong_password"
    password_hash = get_password_hash(password)

    assert verify_password(password, password_hash) is True

    assert verify_password(password_wrong, password_hash) is False


def test_auth_basic(user_basic: models.User, client: TestClient):

    response = client.post(
        "/auth/token", data={"username": user_basic.email, "password": "basic"}
    )
    assert response.status_code == 200
    access_token = response.json()
    assert set(access_token.keys()) == set(["access_token", "token_type"])

    payload = jwt.decode(
        access_token["access_token"], settings.SECRET_KEY, algorithms=[ALGORITHM]
    )

    assert payload["scopes"] == ["basic"]

    assert payload["sub"] == str(user_basic.id)


def test_auth_basic_fail(client: TestClient):
    response = client.post(
        "/auth/token", data={"username": "non-existant@email.dk", "password": "basic"}
    )
    assert response.status_code == 400