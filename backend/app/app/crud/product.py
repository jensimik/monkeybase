import sqlalchemy as sa
from ..models import Product, MemberType, Event
from ..schemas import ProductCreate, ProductUpdate
from .base import CRUDBase
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Union, Dict, List, Any, Optional


class CRUDProduct(CRUDBase[Product, ProductCreate, ProductUpdate]):
    async def get(self, *args, **kwargs) -> Union[MemberType, Event]:
        return await super().get(*args, **kwargs)

    async def get_multi(self, *args, **kwargs) -> List[Union[MemberType, Event]]:
        return await super().get_multi(*args, **kwargs)

    async def create(self, *args, **kwargs) -> Union[MemberType, Event]:
        raise Exception("not implemented - please use a specific type")


product = CRUDProduct(Product)
