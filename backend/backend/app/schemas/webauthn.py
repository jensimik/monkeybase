from typing import Optional

from pydantic import BaseModel


# Shared properties
class WebauthnBase(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None


# Properties to receive via API on creation
class WebauthnCreate(WebauthnBase):
    name: str
    user_id: int
    credential: str
    credential_id: str


# Properties to receive via API on update
class WebauthnUpdate(WebauthnBase):
    name: str


class Webauthn(WebauthnBase):
    pass
