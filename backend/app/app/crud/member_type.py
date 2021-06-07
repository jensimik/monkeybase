import sqlalchemy as sa
from ..models import MemberType
from ..schemas import MemberTypeCreate, MemberTypeUpdate
from .base import CRUDBase
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Union, Dict, List, Any, Optional


class CRUDMemberType(CRUDBase[MemberType, MemberTypeCreate, MemberTypeUpdate]):
    async def create(
        self,
        db: AsyncSession,
        obj_in: Union[MemberTypeCreate, Dict[str, Any]],
    ) -> MemberType:
        # ensure obj_type is set as insert doesnt seem to handle this on poly
        values = obj_in if isinstance(obj_in, dict) else obj_in.dict(exclude_unset=True)
        values["obj_type"] = self.model.__mapper_args__["polymorphic_identity"]
        return await super().create(db, obj_in=values)

    async def update(
        self,
        db: AsyncSession,
        *args: List[sa.sql.elements.BinaryExpression],
        obj_in: Union[MemberTypeUpdate, Dict[str, Any]],
        multi: Optional[bool] = False,
        only_active: Optional[bool] = True,
    ) -> MemberType:
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
    ) -> MemberType:
        # ensure obj_type is an arg
        return await super().remove(
            db,
            self.model.obj_type == self.model.__mapper_args__["polymorphic_identity"],
            *args,
            actual_delete=actual_delete,
        )


member_type = CRUDMemberType(MemberType)
