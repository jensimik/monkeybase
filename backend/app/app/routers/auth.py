import uuid
import sqlalchemy as sa
import secrets
import fido2
from base64 import b64encode, b64decode
from loguru import logger
from datetime import datetime, timedelta
from typing import Any, Optional
from fastapi import (
    APIRouter,
    Request,
    Response,
    Body,
    Depends,
    HTTPException,
    security,
    Path,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession
from app import schemas, deps, crud, models
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    webauthn_state,
    fido2server,
)
from app.core.utils import (
    generate_password_reset_token,
    # send_reset_password_email,
    verify_password_reset_token,
    generate_webauthn_state_token,
    verify_webauthn_staten_token,
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

    user = await crud.user.get(
        db,
        (models.User.email == form_data.username),
        options=[sa.orm.selectinload(models.User.webauthn)],
    )

    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not user.active:
        raise HTTPException(status_code=400, detail="Inactive user")
    # if 2factor enabled then return a 2factor challenge in application/cboe format
    # user then have to finish getting the token from the 2factor endpoint
    if user.enabled_2fa:
        auth_data, state = fido2server.authenticate_begin(
            credentials=[
                fido2.ctap2.AttestedCredentialData(b64decode(wac.credential))
                for wac in user.webauthn
            ],
            user_verification=fido2.webauthn.UserVerificationRequirement.DISCOURAGED,
        )
        response = Response(
            content=fido2.cbor.encode(auth_data), media_type="application/cbor"
        )
        # set the state parameter as a signed cookie
        response.set_cookie("_state", generate_webauthn_state_token(state, user))
        return response

    return create_access_token(user)


@router.post("/two-factor-complete", response_model=schemas.Token)
async def login_access_token_with_2fa(
    request: Request,
    response: Response,
    _state=Depends(webauthn_state),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    try:
        # decode the request's body
        data = fido2.cbor.decode(await request.body())
        credential_id = data["credentialId"]
        client_data = fido2.client.ClientData(data["clientDataJSON"])
        auth_data = fido2.ctap2.AuthenticatorData(data["authenticatorData"])
        signature = data["signature"]

    except (ValueError, KeyError) as ex:
        logger.exception(ex)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Received invalid data!",
        ) from ex

    state = verify_webauthn_staten_token(_state)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Warning: Invalid state parameter!",
        )

    logger.info(state)

    user = await crud.user.get(
        db,
        (models.User.id == state["user_id"]),
        options=[sa.orm.selectinload(models.User.webauthn)],
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User does not exist!",
        )

    try:
        fido2server.authenticate_complete(
            state,
            # list all registered credidentials of the user
            [
                fido2.ctap2.AttestedCredentialData(b64decode(wac.credential))
                for wac in user.webauthn
            ],
            credential_id,
            client_data,
            auth_data,
            signature,
        )
    except ValueError as ex:
        logger.info("invalid fido data verfiy")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Received invalid data!",
        ) from ex

    if not user.active:
        raise HTTPException(status_code=400, detail="Inactive user")

    # remove temoprary webauth state cookie
    response.delete_cookie("_state")

    return create_access_token(user)


@router.post("/password-recovery/{email}", response_model=schemas.Msg)
async def recover_password(
    email: str = Path(..., title="the email address to recover email from"),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
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
