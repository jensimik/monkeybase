from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# Shared properties
class EventBase(BaseModel):
    active: Optional[bool] = True
    name: Optional[str] = None
    name_short: Optional[str] = None
    slot_enabled: Optional[bool] = None
    slot_limit: Optional[int] = None
    date_signup_deadline: Optional[datetime] = None
    date_start: Optional[datetime] = None
    date_end: Optional[datetime] = None


# Properties to receive via API on creation
class EventCreate(EventBase):
    name: str
    name_short: str
    date_signup_deadline: datetime
    date_start: datetime
    date_end: datetime


# Properties to receive via API on update
class EventUpdate(EventBase):
    pass


class EventInDBBase(EventBase):
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


# Additional properties to return via API
class Event(EventInDBBase):
    pass


# Additional properties stored in DB
class EventInDB(EventInDBBase):
    pass
