from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from passlib.context import CryptContext
from fido2.server import Fido2Server
from fido2.webauthn import PublicKeyCredentialRpEntity
from fastapi.security import APIKeyCookie
from .config import settings
from .. import models

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

rp = PublicKeyCredentialRpEntity(settings.WEBAUTHN_RP_ID, settings.WEBAUTHN_RP_NAME)
fido2server = Fido2Server(rp)
webauthn_state = APIKeyCookie(name="_state", auto_error=True)

ALGORITHM = "HS256"


def create_access_token(
    user: models.User, expires_delta: Optional[timedelta] = None
) -> str:
    data = {"sub": str(user.id), "scopes": user.scopes.split(",")}
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    data.update({"exp": expire})
    encoded_jwt = jwt.encode(data, settings.SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": encoded_jwt, "token_type": "bearer"}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
