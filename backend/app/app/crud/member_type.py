from ..models import MemberType
from ..schemas import MemberTypeCreate, MemberTypeUpdate
from .base import CRUDBase
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Union, Dict, Any


class CRUDMemberType(CRUDBase[MemberType, MemberTypeCreate, MemberTypeUpdate]):
    async def create(
        self,
        db: AsyncSession,
        obj_in: Union[MemberTypeCreate, Dict[str, Any]],
    ) -> MemberType:
        # ensure obj_type is set as insert doesnt seem to handle this on poly
        values = obj_in if isinstance(obj_in, dict) else obj_in.dict(exclude_unset=True)
        values["obj_type"] = "member_type"
        return await super().create(db, obj_in=values)


member_type = CRUDMemberType(MemberType)
