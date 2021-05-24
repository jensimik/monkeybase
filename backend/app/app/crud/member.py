import datetime
from typing import Optional
from app.crud.base import CRUDBase
from app.models import MemberType, Member, User
from app.schemas import MemberCreate, MemberUpdate
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession


class CRUDMember(CRUDBase[Member, MemberCreate, MemberUpdate]):
    pass


member = CRUDMember(Member)
