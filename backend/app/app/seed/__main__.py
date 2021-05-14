import asyncio
import sqlalchemy as sa
import random
from loguru import logger
from app.db.base import Base, engine
from app.models import User, MemberType, Member
from app.core.security import get_password_hash
from faker import Faker


async def seed_data():
    fake = Faker()
    async with engine.begin() as conn:
        q = sa.insert(User).values(
            {
                "name": "Some Name",
                "email": "test@test.dk",
                "birthday": fake.date_of_birth(),
                "hashed_password": get_password_hash("password"),
            }
        )
        await conn.execute(q)

        for x in ["Full membership", "Morning membership"]:
            q = sa.insert(MemberType).values(
                {
                    "name": x,
                    "slots_available": random.randint(2, 10),
                    "open_public": True,
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

        await conn.commit()


async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await seed_data()


if __name__ == "__main__":
    asyncio.run(init_models())
