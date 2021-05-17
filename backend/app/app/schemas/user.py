from typing import Optional, List
from uuid import UUID
from datetime import datetime, date
from pydantic import BaseModel, EmailStr

# Shared properties
class UserBase(BaseModel):
    uuid: Optional[UUID] = None
    email: Optional[EmailStr] = None
    active: Optional[bool] = True
    name: Optional[str] = None
    birthday: Optional[date] = None


# Properties to receive via API on creation
class UserCreate(UserBase):
    email: EmailStr
    password: str


# Properties to receive via API on update
class UserUpdate(UserBase):
    hashed_password: Optional[str] = None


class UserUpdateMe(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    birthday: Optional[date] = None


class UserInDBBase(UserBase):
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


# dont show user id in API - only the UUID
class UserInDBBase2(UserBase):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


# Additional properties to return via API
class User(UserInDBBase2):
    member: "List[MemberMemberType]" = []


# Additional properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str


from .member import MemberMemberType

User.update_forward_refs()
