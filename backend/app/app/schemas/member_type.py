from typing import Optional
from datetime import datetime
from pydantic import BaseModel


# Shared properties
class MemberTypeBase(BaseModel):
    active: Optional[bool] = True
    name: Optional[str] = None


# Properties to receive via API on creation
class MemberTypeCreate(MemberTypeBase):
    name: str


# Properties to receive via API on update
class MemberTypeUpdate(MemberTypeBase):
    active: Optional[bool] = True
    name: Optional[str] = None


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
