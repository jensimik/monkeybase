import aiohttp
from fastapi import Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import jwt
from pydantic import ValidationError
from typing import AsyncIterator, Optional
from . import schemas, models, crud
from .core import security
from .core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from .db.base import async_session
from contextlib import asynccontextmanager


reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl="/auth/token",
    scopes={
        "basic": "the basic scope for a logged in user",
        "member": "user is a member at some level",
        "member_full": "standard full member",
        "member_morning": "member morning only",
        "member_banana": "member banana",
        "admin": "admin scope only for the board/admin",
    },
)


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
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
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
