from .base import CRUDBase
from ..models import User
from ..schemas import UserCreate, UserUpdate
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    async def get_by_email(self, session: AsyncSession, email: str) -> User:
        query = sa.select(User).where(User.email == email)
        return (await session.execute(query)).scalar_one_or_none()


user = CRUDUser(User)
