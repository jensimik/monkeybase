from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, constr


NAME = constr(min_length=4, max_length=50)
PASSWORD = constr(min_length=4, max_length=50)

# Shared properties
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[NAME] = None
    birthday: Optional[date] = None


# Properties to receive via API on creation
class UserCreate(UserBase):
    email: EmailStr
    password: PASSWORD
    birthday: date


# Properties to receive via API on update
class UserUpdate(UserBase):
    enabled_2fa: Optional[bool] = None
    password: Optional[PASSWORD] = None


class UserUpdateMe(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[NAME] = None
    birthday: Optional[date] = None
    enabled_2fa: Optional[bool] = None
    password: Optional[PASSWORD] = None


class UserInDBBase(UserBase):
    id: Optional[int] = None
    active: Optional[bool] = True
    enabled_2fa: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


# Additional properties to return via API
class User(UserInDBBase):
    member: "List[MemberMemberType]" = []


# Additional properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str


from .member import MemberMemberType

User.update_forward_refs()
