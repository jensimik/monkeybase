from ..models import Webauthn
from ..schemas import WebauthnCreate, WebauthnUpdate
from .base import CRUDBase


class CRUDWebauthn(CRUDBase[Webauthn, WebauthnCreate, WebauthnUpdate]):
    pass


webauthn = CRUDWebauthn(Webauthn)
