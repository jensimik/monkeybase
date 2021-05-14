from datetime import timedelta
from typing import Any, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, security
from sqlalchemy.ext.asyncio import AsyncSession
from app import schemas, deps, crud
from app.core.config import settings
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.utils import (
    generate_password_reset_token,
    # send_reset_password_email,
    verify_password_reset_token,
)

router = APIRouter()


@router.post("/token", response_model=schemas.Token)
async def login_access_token(
    db: AsyncSession = Depends(deps.get_db),
    form_data: security.OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """

    user = await crud.user.get_by_email(db, form_data.username)

    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.active:
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "scopes": form_data.scopes},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/password-recovery/{email}", response_model=schemas.Msg)
async def recover_password(email: str, db: AsyncSession = Depends(deps.get_db)) -> Any:
    """
    Password Recovery
    """
    user = await crud.user.get_by_email(db, email=email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )
    password_reset_token = generate_password_reset_token(email=email)
    # send_reset_password_email(
    #     email_to=user.email, email=email, token=password_reset_token
    # )
    return {"msg": f"Password recovery email sent token: {password_reset_token}"}


@router.post("/reset-password", response_model=schemas.Msg)
async def reset_password(
    token: str = Body(...),
    new_password: str = Body(...),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Reset password
    """
    email = verify_password_reset_token(token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token")

    user = await crud.user.get_by_email(db, email=email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )
    elif not user.active:
        raise HTTPException(status_code=400, detail="Inactive user")
    user = await crud.user.update(
        db, db_obj=user, obj_in={"hashed_password": get_password_hash(new_password)}
    )
    return {"msg": "Password updated successfully"}
