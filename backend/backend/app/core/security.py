from datetime import datetime, timedelta
from typing import Optional

from fastapi.security import APIKeyCookie
from fido2.server import Fido2Server
from fido2.webauthn import PublicKeyCredentialRpEntity
from jose import jwt
from loguru import logger
from passlib.context import CryptContext

from .. import models
from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

rp = PublicKeyCredentialRpEntity(settings.WEBAUTHN_RP_ID, settings.WEBAUTHN_RP_NAME)
fido2server = Fido2Server(rp)
webauthn_state = APIKeyCookie(name="_state", auto_error=True)

ALGORITHM = "HS256"


def create_access_token(
    user: models.User, expires_delta: Optional[timedelta] = None
) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    data = {"sub": str(user.id), "scopes": user.scopes.split(","), "exp": expire}
    encoded_jwt = jwt.encode(data, settings.SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": encoded_jwt, "token_type": "bearer"}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def generate_password_reset_token(email: str) -> str:
    delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    now = datetime.utcnow()
    exp = now + delta
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "aud": "password_reset", "sub": email},
        settings.SECRET_KEY,
        algorithm="HS256",
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> Optional[str]:
    try:
        decoded_token = jwt.decode(
            token, settings.SECRET_KEY, audience="password_reset", algorithms=["HS256"]
        )
        return decoded_token["sub"]
    except jwt.JWTError:
        return None


def generate_signup_confirm_token(email: str) -> str:
    delta = timedelta(days=14)
    now = datetime.utcnow()
    exp = now + delta
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "aud": "signup_confirm", "sub": email},
        settings.SECRET_KEY,
        algorithm="HS256",
    )
    return encoded_jwt


def verify_signup_confirm_token(token: str) -> Optional[str]:
    try:
        decoded_token = jwt.decode(
            token, settings.SECRET_KEY, audience="signup_confirm", algorithms=["HS256"]
        )
        return decoded_token["sub"]
    except jwt.JWTError:
        return None


def generate_webauthn_state_token(state: dict, user: models.User) -> str:
    _state = state.copy()
    now = datetime.utcnow()
    exp = now + timedelta(minutes=5)
    _state.update({"exp": exp, "nbf": now, "aud": "webauthn_state", "user_id": user.id})
    encoded_jwt = jwt.encode(
        _state,
        settings.SECRET_KEY,
        algorithm="HS256",
    )
    return encoded_jwt


def verify_webauthn_staten_token(token: str) -> Optional[str]:
    try:
        decoded_token = jwt.decode(
            token, settings.SECRET_KEY, audience="webauthn_state", algorithms=["HS256"]
        )
        return decoded_token
    except jwt.JWTError as ex:
        logger.exception(f"failed with {ex}")
        return None
