from loguru import logger
import asyncio
import sqlalchemy as sa
import random
import datetime
from loguru import logger
from ..db.base import Base, engine
from ..models import User, MemberType, Member, Webauthn, MemberTypeSlot, LockTable
from ..core.security import get_password_hash
from faker import Faker


async def test():
    async with engine.begin() as conn:
        q = sa.select(Webauthn).order_by(Webauthn.id)
        data = await conn.execute(q)
        print(data)
        print(data.scalars().all())
        print(data)


async def seed_data():
    fake = Faker()
    async with engine.begin() as conn:
        # load uuid extension
        await conn.execute(sa.text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
        q = sa.insert(User).values(
            {
                "name": "Some Name",
                "email": "test@test.dk",
                "birthday": fake.date_of_birth(),
                "hashed_password": get_password_hash("password"),
                "scopes": "basic,admin,other",
            }
        )
        await conn.execute(q)
        q = sa.insert(User).values(
            {
                "name": "Some Name",
                "email": "test-admin@test.dk",
                "birthday": fake.date_of_birth(),
                "hashed_password": get_password_hash("password"),
                "scopes": "basic,admin",
            }
        )
        await conn.execute(q)
        q = sa.insert(User).values(
            {
                "name": "Some Name",
                "email": "test-basic@test.dk",
                "birthday": fake.date_of_birth(),
                "hashed_password": get_password_hash("password"),
                "scopes": "basic",
            }
        )
        await conn.execute(q)
        for x in ["Full membership", "Morning membership"]:
            q = sa.insert(MemberType).values(
                {
                    "name": x,
                }
            )
            await conn.execute(q)

        for _ in range(100):
            q = sa.insert(User).values(
                {
                    "name": fake.name(),
                    "email": fake.email(),
                    "birthday": fake.date_of_birth(),
                    "hashed_password": get_password_hash("password"),
                }
            )
            await conn.execute(q)
        for x in range(5, 20):
            q = sa.insert(Member).values(
                {
                    "user_id": x,
                    "member_type_id": 1,
                    "date_start": fake.date_this_year(
                        before_today=True, after_today=False
                    ),
                    "date_end": fake.date_this_year(
                        before_today=False, after_today=True
                    ),
                }
            )
            await conn.execute(q)

        for x in range(5):
            q = sa.insert(MemberTypeSlot).values(
                {
                    "member_type_id": 1,
                    "slot_type": "OPEN",
                    "reserved_until": datetime.datetime.utcnow(),
                }
            )
            await conn.execute(q)

        q = sa.insert(LockTable).values({"name": "crontest"})
        await conn.execute(q)

        await conn.commit()


async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await seed_data()


if __name__ == "__main__":
    # asyncio.run(test())
    asyncio.run(init_models())
