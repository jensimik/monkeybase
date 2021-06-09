from loguru import logger
import asyncio
import sqlalchemy as sa
import random
import datetime
from loguru import logger
from ..db.base import Base, engine
from ..models import User, MemberType, Event, Member, Webauthn, Slot, LockTable
from .. import crud, deps, models
from ..core.security import get_password_hash
from faker import Faker
from ..utils.models_utils import DoorAccessEnum


# async def test():
#     async with deps.get_db_context() as conn:
#         # engine.begin() as conn:
#         q = sa.select(User)
#         data = await conn.execute(q)
#         print(data)
#         print(data.scalars().all())


async def seed_data():
    fake = Faker()
    # async with engine.begin() as conn:
    async with deps.get_db_context() as conn:
        # engine.begin() as conn:
        # load uuid extension
        await conn.execute(sa.text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
        q = sa.insert(User).values(
            {
                "name": "Some Name",
                "email": "test@test.dk",
                "birthday": fake.date_of_birth(),
                "hashed_password": get_password_hash("test"),
                "scopes": "basic,admin,other",
                "door_id": "some-door-id",
            }
        )
        await conn.execute(q)
        for x in ["Full membership", "Morning membership"]:
            q = sa.insert(MemberType).values(
                {
                    "name": x,
                    "name_short": x,
                    "obj_type": "member_type",
                    "door_access": DoorAccessEnum.FULL,
                }
            )
            await conn.execute(q)

        for x in ["Event 1", "Event 2"]:
            q = sa.insert(MemberType).values(
                {"name": x, "name_short": x, "obj_type": "event"}
            )
            await conn.execute(q)

        q = sa.select(MemberType).where(MemberType.name == "Full membership")
        full_membership = (await conn.execute(q)).scalar_one()

        q = sa.select(Event).where(Event.name == "Event 1")
        event_1 = (await conn.execute(q)).scalar_one()

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
        for x in range(1, 80):
            q = sa.insert(Member).values(
                {
                    "user_id": x,
                    "product_id": full_membership.id,
                    "date_start": fake.date_this_year(
                        before_today=True, after_today=False
                    ),
                    "date_end": fake.date_this_year(
                        before_today=False, after_today=True
                    ),
                }
            )
            await conn.execute(q)

        q = sa.insert(Member).values(
            {
                "user_id": 1,
                "product_id": event_1.id,
                "date_start": fake.date_this_year(before_today=True, after_today=False),
                "date_end": fake.date_this_year(before_today=False, after_today=True),
            }
        )
        await conn.execute(q)

        for x in range(5):
            q = sa.insert(Slot).values(
                {
                    "product_id": full_membership.id,
                    "reserved_until": datetime.datetime.utcnow(),
                }
            )
            await conn.execute(q)

        q = sa.insert(LockTable).values({"name": "crontest"})
        await conn.execute(q)

        q = sa.select(User).where(User.id == 1)

        print((await conn.execute(q)).scalar_one())

        await conn.commit()


async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await seed_data()


async def test():
    async with deps.get_db_context() as db:
        user = await crud.user.get(
            db,
            models.User.id == 1,
            options=[
                sa.orm.selectinload(
                    models.User.member.and_(models.Member.active == True)
                ).selectinload(
                    models.Member.product.and_(models.Product.active == True)
                )
            ],
        )
        print(user)
        for member in user.member:
            print(member)
            print(member.product)


if __name__ == "__main__":
    # asyncio.run(test())
    asyncio.run(init_models())
