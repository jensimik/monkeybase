from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

import aiohttp
import stripe
from fastapi import Depends, Header, HTTPException, Query, Request, Security, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from fastapi.security.api_key import APIKeyHeader
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from . import crud, models, schemas
from .core import security
from .core.config import settings
from .db.base import async_session

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl="/auth/token",
    scopes={
        "basic": "the basic scope for a logged in user",
        "admin": "admin scope only for the board/admin",
    },
)
stripe_signature_header = APIKeyHeader(name="stripe-signature", auto_error=True)


@asynccontextmanager
async def get_db_context():
    async with async_session() as session:
        yield session


async def get_db() -> AsyncIterator[AsyncSession]:
    async with async_session() as session:
        yield session


async def get_http_session() -> AsyncIterator[aiohttp.ClientSession]:
    async with aiohttp.ClientSession() as session:
        yield session


async def stripe_webhook_event(
    request: Request, stripe_signature: str = Security(stripe_signature_header)
) -> stripe.Event:
    data = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload=data,
            sig_header=stripe_signature,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError as ex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="bad payload"
        ) from ex
    except stripe.error.SignatureVerificationError as ex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="invalid signature"
        ) from ex
    return event


async def get_current_user_id(
    security_scopes: SecurityScopes, token: str = Depends(reusable_oauth2)
) -> int:
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    try:
        payload = parse_token(token)
        token_data = schemas.TokenPayload(**payload)
    except (jwt.JWTError, ValidationError) as ex:
        raise credentials_exception from ex
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )
    return int(token_data.sub)


def parse_token(token: str) -> dict:
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
    return payload


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> models.User:
    user = await crud.user.get(db, models.User.id == user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


class Paging:
    def __init__(
        self,
        page: Optional[str] = Query(
            None,
            description="page keyset to fetch, empty/undefined for first page",
        ),
        per_page: Optional[int] = Query(
            100,
            description="rows to fetch per page",
            ge=1,
            le=10000,
        ),
    ):
        self.page = page
        self.per_page = per_page


class Q:
    def __init__(
        self,
        q: Optional[str] = Query(None, description="search string"),
    ):
        self.q = q
