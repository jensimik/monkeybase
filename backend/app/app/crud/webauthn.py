from app.crud.base import CRUDBase
from app.models import Webauthn
from app.schemas import WebauthnCreate, WebauthnUpdate
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession


class CRUDWebauthn(CRUDBase[Webauthn, WebauthnCreate, WebauthnUpdate]):
    pass


webauthn = CRUDWebauthn(Webauthn)
