from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# Shared properties
class WaitingListBase(BaseModel):
    active: Optional[bool] = True
    user_id: Optional[int] = None
    product_id: Optional[int] = None


# Properties to receive via API on creation
class WaitingListCreate(WaitingListBase):
    user_id: int
    product_id: int


# Properties to receive via API on update
class WaitingListUpdate(WaitingListBase):
    user_id: Optional[int] = None
    product_id: Optional[int] = None


class WaitingListInDBBase(WaitingListBase):
    id: int
    user_id: int
    product_id: int
    active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# Additional properties to return via API
class WaitingList(WaitingListInDBBase):
    pass


# Additional properties stored in DB
class WaitingListInDB(WaitingListInDBBase):
    pass
