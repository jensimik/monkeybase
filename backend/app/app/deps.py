import aiohttp
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import jwt
from pydantic import ValidationError
from typing import AsyncIterator, Optional
from app import schemas
from app.core import security
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import async_session
from app import crud
from app.models import User


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
) -> User:
    user = await crud.user.get(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


class ListQP:
    def __init__(self, q: Optional[str] = None, page: str = None, per_page: int = 100):
        self.q = q
        self.page = page
        self.per_page = per_page
