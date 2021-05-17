import sqlalchemy as sa
import fido2
import base64
from fastapi import (
    APIRouter,
    Request,
    Response,
    Depends,
    HTTPException,
    security,
    Security,
    Query,
    status,
)
from typing import Any
from app import deps, models, crud, schemas
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.utils import generate_webauthn_state_token, verify_webauthn_staten_token

rp = fido2.webauthn.PublicKeyCredentialRpEntity(
    settings.WEBAUTHN_RP_ID, settings.WEBAUTHN_RP_NAME
)
fido2server = fido2.server.Fido2Server(rp)
webauthn_state = security.APIKeyCookie(name="_state", auto_error=True)
USER_VERIFICATION = fido2.webauthn.UserVerificationRequirement.DISCOURAGED

router = APIRouter()


@router.post("/add/begin")
async def webauthn_add_begin(
    response: Response,
    db: AsyncSession = Depends(deps.get_db),
    user_id: models.User = Security(deps.get_current_user_id, scopes=["basic"]),
) -> Any:

    user = await crud.user.get(
        db,
        models.User.id == user_id,
        options=[sa.orm.subqueryload(models.User.webauthn)],
    )

    # calls the library which provides the credential options and a state
    registration_data, state = fido2server.register_begin(
        {
            # id is a byte sequence as described in
            # https://w3c.github.io/webauthn/#dom-publickeycredentialuserentity-id
            "id": str(user.uuid).encode("utf-8"),
            # we use the email address here for passwordless login later
            "name": user.email,
            # we don't have any 'real' name to display and therefore this example uses
            # the part before the @ in the email address.
            "displayName": user.name,
        },
        # A list of already registered credentials is passed to the library and to the
        # client to avoid adding the same webauthn credential twice.
        credentials=[
            fido2.ctap2.AttestedCredentialData(base64.b64decode(wac.credential))
            for wac in user.webauthn
        ],
        # We want to use some kind of cross platform authenticator like a Yubikey not
        # something like Windows Hello on PCs or TouchID on some macs.
        # authenticator_attachment="cross-platform",
        # authenticator_attachment="platform",
        # We want to require the pin of the authenticator as a second factor.
        # user_verification="required",
        # user_verification=USER_VERIFICATION,
        # We want to store a credential on the client side
        # resident_key=True,
    )
    # create a custom response with the ``Content-Type`` ``application/cbor``. Most
    # browsers and applications won't be able to display the body of the requests.
    response = Response(
        content=fido2.cbor.encode(registration_data), media_type="application/cbor"
    )
    # set the state parameter as a signed cookie
    response.set_cookie("_state", generate_webauthn_state_token(state, user))

    # return the response.
    return response


@router.post("/add/complete", response_class=Response)
async def complete_webauthn(
    request: Request,
    db: AsyncSession = Depends(deps.get_db),
    user_id: models.User = Security(deps.get_current_user_id, scopes=["basic"]),
    _state=Depends(webauthn_state),
    securitykey_name: str = Query(...),
):
    try:
        # decode the requests body using cbor
        data = fido2.cbor.decode(await request.body())
        client_data = fido2.client.ClientData(data["clientDataJSON"])
        att_obj = fido2.ctap2.AttestationObject(data["attestationObject"])
    except ValueError as ex:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Failed to parse request body!",
        ) from ex
    state = verify_webauthn_staten_token(_state)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Warning: Invalid state parameter!",
        )
    try:
        # verify authentication data
        auth_data: fido2.ctap2.AuthenticatorData = fido2server.register_complete(
            state,
            client_data,
            att_obj,
        )
    except ValueError as ex:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication data!",
        ) from ex

    # create the response with ``Content-Type`` ``application/cbor``.
    response = Response(
        content=fido2.cbor.encode({"status": "OK"}), media_type="application/cbor"
    )

    # Tell the client to delete the cookie used to store the state since it is not
    # needed anymore.
    response.delete_cookie("_state")

    # save the new webauthn credidential
    await crud.webauthn.create(
        db,
        schemas.WebauthnCreate(
            user_id=user_id,
            name=securitykey_name,
            credential=base64.b64encode(auth_data.credential_data),
            credential_id=auth_data.credential_data.credential_id.hex(),
        ),
    )
    user = await crud.user.get(db, models.User.id == user_id)
    await crud.user.update(db, user, {"enabled_2fa": True})
    await db.commit()

    # return the response
    return response
