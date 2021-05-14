import datetime
from typing import Optional
from app.crud.base import CRUDBase
from app.models import MemberType, Member, User
from app.schemas import MemberCreate, MemberUpdate
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession


class CRUDMember(CRUDBase[Member, MemberCreate, MemberUpdate]):
    async def create_membership_paid(
        self,
        session: AsyncSession,
        membership_type_id: int,
        user_id: int,
        payment_id: int,
    ) -> Member:
        # get the membership type locked row and subtract a slot
        query = (
            sa.select(MemberType)
            .where(MemberType.id == membership_type_id)
            .where(MemberType.slots_available > 0)
            .with_for_update()
        )
        m_t = (await session.execute(query)).scalar_one_or_none()
        if not m_t:
            raise Exception("sorry - all memberships sold out :-(")
        # subtract a slot available
        m_t.slots_available -= 1
        query_insert = (
            sa.insert(Member)
            .values(
                **{
                    Member.user_id: user_id,
                    Member.membership_type_id: membership_type_id,
                    Member.date_start: datetime.date.utcnow(),
                    Member.date_end: datetime.date.utcnow()
                    + datetime.timedelta(days=14),
                    Member.payment_id: payment_id,
                }
            )
            .returning(Member)
        )
        obj = (await session.execute(query_insert)).scalar_one()
        try:
            await session.commit()
        except Exception as ex:
            await session.rollback()
            raise Exception("sorry - all memberships sold out :-(") from ex
        return obj


member = CRUDMember(Member)
