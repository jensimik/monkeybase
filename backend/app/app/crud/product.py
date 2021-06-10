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

    async def update(
        self,
        db: AsyncSession,
        *args: List[sa.sql.elements.BinaryExpression],
        obj_in: Union[ProductUpdate, Dict[str, Any]],
        multi: Optional[bool] = False,
        only_active: Optional[bool] = True,
    ) -> Union[MemberType, Event]:
        # ensure obj_type is an arg
        return await super().update(
            db,
            self.model.obj_type == self.model.__mapper_args__["polymorphic_identity"],
            *args,
            multi=multi,
            only_active=only_active,
            obj_in=obj_in,
        )

    async def remove(
        self,
        db: AsyncSession,
        *args: List[sa.sql.elements.BinaryExpression],
        actual_delete: Optional[bool] = False,
    ) -> Union[MemberType, Event]:
        # ensure obj_type is an arg
        return await super().remove(
            db,
            self.model.obj_type == self.model.__mapper_args__["polymorphic_identity"],
            *args,
            actual_delete=actual_delete,
        )


product = CRUDProduct(Product)
