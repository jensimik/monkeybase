from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from ..utils.models_utils import SlotTypeEnum


# Shared properties
class SlotBase(BaseModel):
    active: Optional[bool] = True


# Properties to receive via API on creation
class SlotCreate(SlotBase):
    slot_type: SlotTypeEnum
    reserved_until: datetime
    user_id: int
    product_id: int


# Properties to receive via API on update
class SlotUpdate(SlotBase):
    active: Optional[bool] = True
    name: Optional[str] = None
    slots_available: Optional[int] = None
    open_public: Optional[bool] = False
    open_wait: Optional[bool] = False


class SlotInDBBase(SlotBase):
    id: int
    slot_type: SlotTypeEnum
    reserved_until: datetime
    user_id: int
    product_id: int
    key: UUID
    active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# Additional properties to return via API
class Slot(SlotInDBBase):
    pass


# Additional properties stored in DB
class SlotInDB(SlotInDBBase):
    pass
