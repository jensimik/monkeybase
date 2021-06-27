from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# Shared properties
class ProductBase(BaseModel):
    active: Optional[bool] = True
    name: Optional[str] = None
    name_short: Optional[str] = None
    slot_enabled: Optional[bool] = None
    slot_limit: Optional[int] = None


# Properties to receive via API on creation
class ProductCreate(ProductBase):
    name: str
    name_short: str


# Properties to receive via API on update
class ProductUpdate(ProductBase):
    pass


class ProductInDBBase(ProductBase):
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


# Additional properties to return via API
class Product(ProductInDBBase):
    pass


# Additional properties stored in DB
class ProductInDB(ProductInDBBase):
    pass
