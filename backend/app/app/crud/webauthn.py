from .base import CRUDBase
from ..models import Webauthn
from ..schemas import WebauthnCreate, WebauthnUpdate


class CRUDWebauthn(CRUDBase[Webauthn, WebauthnCreate, WebauthnUpdate]):
    pass


webauthn = CRUDWebauthn(Webauthn)
