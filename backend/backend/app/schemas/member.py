from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


# Shared properties
class MemberBase(BaseModel):
    user_id: Optional[int] = None
    member_type_id: Optional[int] = None
    date_start: Optional[date] = None
    date_end: Optional[date] = None
    payment_id: Optional[int] = None


class MemberCreateMe(BaseModel):
    key: UUID
    payment_id: int


# Properties to receive via API on creation
class MemberCreate(MemberBase):
    user_id: int
    member_type_id: int
    date_start: date
    date_end: date
    payment_id: int


# Properties to receive via API on update
class MemberUpdate(MemberBase):
    pass


class MemberInDBBase(MemberBase):
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    active: Optional[bool] = True

    class Config:
        orm_mode = True


# Additional properties to return via API
class Member(MemberInDBBase):
    pass


class MemberUser(MemberInDBBase):
    user: "Optional[User]" = None


class MemberMemberType(MemberInDBBase):
    product: "Optional[MemberType]" = None


# Additional properties stored in DB
class MemberInDB(MemberInDBBase):
    pass


from .user import User

MemberUser.update_forward_refs()

from .member_type import MemberType

MemberMemberType.update_forward_refs()
