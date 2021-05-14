from typing import Optional
from datetime import datetime, date
from pydantic import BaseModel, EmailStr
from . import User


# Shared properties
class MemberBase(BaseModel):
    user_id: Optional[int] = None
    membership_type_id: Optional[int] = None
    date_start: Optional[date] = None
    date_end: Optional[date] = None
    payment_id: Optional[int] = None


# Properties to receive via API on creation
class MemberCreate(MemberBase):
    user_id: int
    membership_type_id: int
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
    user: Optional[User] = None


# Additional properties stored in DB
class MemberInDB(MemberInDBBase):
    pass
