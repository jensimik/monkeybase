from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from ..models_utils import SlotTypeEnum

# Shared properties
class MemberTypeSlotBase(BaseModel):
    active: Optional[bool] = True


# Properties to receive via API on creation
class MemberTypeSlotCreate(MemberTypeSlotBase):
    slot_type: SlotTypeEnum
    reserved_until: datetime
    user_id: int
    member_type_id: int


# Properties to receive via API on update
class MemberTypeSlotUpdate(MemberTypeSlotBase):
    active: Optional[bool] = True
    name: Optional[str] = None
    slots_available: Optional[int] = None
    open_public: Optional[bool] = False
    open_wait: Optional[bool] = False


class MemberTypeSlotInDBBase(MemberTypeSlotBase):
    id: int
    slot_type: SlotTypeEnum
    reserved_until: datetime
    user_id: int
    member_type_id: int
    key: UUID
    active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# Additional properties to return via API
class MemberTypeSlot(MemberTypeSlotInDBBase):
    pass


# Additional properties stored in DB
class MemberTypeSlotInDB(MemberTypeSlotInDBBase):
    pass
