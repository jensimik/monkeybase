from typing import Any, Dict, List, Optional, Union

import sqlalchemy as sa

from ..db import AsyncSession
from ..models import Event, MemberType, Product
from ..schemas import ProductCreate, ProductUpdate
from .base import CRUDBase


class CRUDProduct(CRUDBase[Product, ProductCreate, ProductUpdate]):
    async def get(self, *args, **kwargs) -> Union[MemberType, Event]:
        return await super().get(*args, **kwargs)

    async def get_multi(self, *args, **kwargs) -> List[Union[MemberType, Event]]:
        return await super().get_multi(*args, **kwargs)

    async def create(self, *args, **kwargs) -> Union[MemberType, Event]:
        raise Exception("not implemented - please use a specific type")


product = CRUDProduct(Product)
