from typing import Optional
from datetime import datetime, date
from pydantic import BaseModel, EmailStr


# Shared properties
class MemberTypeBase(BaseModel):
    active: Optional[bool] = True
    name: Optional[str] = None
    slots_available: Optional[int] = None
    open_public: Optional[bool] = False
    open_wait: Optional[bool] = False


# Properties to receive via API on creation
class MemberTypeCreate(MemberTypeBase):
    name: str
    slots_available: int
    open_public: bool
    open_wait: bool


# Properties to receive via API on update
class MemberTypeUpdate(MemberTypeBase):
    active: Optional[bool] = True
    name: Optional[str] = None
    slots_available: Optional[int] = None
    open_public: Optional[bool] = False
    open_wait: Optional[bool] = False


class MemberTypeInDBBase(MemberTypeBase):
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


# Additional properties to return via API
class MemberType(MemberTypeInDBBase):
    pass


# Additional properties stored in DB
class MemberTypeInDB(MemberTypeInDBBase):
    pass
