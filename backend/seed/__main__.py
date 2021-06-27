from loguru import logger
import asyncio
import sqlalchemy as sa
import random
import uuid
import datetime
from loguru import logger
from backend.app.db.base import Base, engine
from backend.app.models import (
    User,
    MemberType,
    Event,
    Member,
    Webauthn,
    Slot,
    LockTable,
)
from backend.app import crud, deps, models
from backend.app.core.security import get_password_hash
from faker import Faker
from backend.app.utils.models_utils import DoorAccessEnum


async def seed_data():
    fake = Faker()
    # async with engine.begin() as conn:
    async with deps.get_db_context() as db:
        # create 100 users
        password_hash = get_password_hash("test")
        for x in range(1, 100):
            await crud.user.create(
                db,
                {
                    "name": f"name {x}",
                    "email": f"test{x}@test.dk",
                    "birthday": fake.date_of_birth(),
                    "hashed_password": password_hash,
                    "scopes": "basic",
                    "door_id": f"some-door-id{x}",
                },
            )
        # create 2 member_types
        for x, door_access in [
            ("Full membership", DoorAccessEnum.FULL),
            ("Morning membership", DoorAccessEnum.MORNING),
        ]:
            await crud.member_type.create(
                db,
                {
                    "name": x,
                    "name_short": x[:5],
                    "door_access": door_access,
                    "price": 1000,
                },
            )
        # create 2 events
        for x in ["Event 1", "Event 2"]:
            await crud.event.create(
                db,
                {
                    "name": x,
                    "name_short": x[:3],
                    "date_signup_deadline": fake.date_this_year(
                        before_today=False, after_today=True
                    ),
                    "date_start": fake.date_this_year(
                        before_today=False, after_today=True
                    ),
                    "date_end": fake.date_this_year(
                        before_today=False, after_today=True
                    ),
                    "price": 1000,
                },
            )
        # create 40 memberships to full membership
        full_membership = await crud.member_type.get(
            db, models.MemberType.name == "Full membership"
        )
        for x in range(1, 41):
            await crud.member.create(
                db,
                {
                    "user_id": x,
                    "product_id": full_membership.id,
                    "date_start": fake.date_this_year(
                        before_today=True, after_today=False
                    ),
                    "date_end": fake.date_this_year(
                        before_today=False, after_today=True
                    ),
                },
            )
        # create 10 memberships to morning membership
        morning_membership = await crud.member_type.get(
            db, models.MemberType.name == "Morning membership"
        )
        for x in range(41, 52):
            await crud.member.create(
                db,
                {
                    "user_id": x,
                    "product_id": morning_membership.id,
                    "date_start": fake.date_this_year(
                        before_today=True, after_today=False
                    ),
                    "date_end": fake.date_this_year(
                        before_today=False, after_today=True
                    ),
                },
            )
        # create 10 memberships to event 1
        event_1 = await crud.event.get(db, models.Event.name == "Event 1")
        for x in range(1, 11):
            await crud.member.create(
                db,
                {
                    "user_id": x,
                    "product_id": event_1.id,
                    "date_start": fake.date_this_year(
                        before_today=True, after_today=False
                    ),
                    "date_end": fake.date_this_year(
                        before_today=False, after_today=True
                    ),
                },
            )
        # create 5 slots for full_membership
        for _ in range(1, 6):
            await crud.slot.create(
                db,
                {
                    "product_id": full_membership.id,
                    "reserved_until": datetime.datetime.utcnow()
                    + datetime.timedelta(days=7),
                    "key": uuid.uuid4().hex,
                },
            )

        # make locktable entries
        for x in ["cron_generate_slots"]:
            await crud.lock_table.create(db, {"name": x})

        await db.commit()


async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await seed_data()


async def test():
    async with deps.get_db_context() as db:
        slot = await crud.slot.get(
            db, Slot.key == "ceb7c46a-9dcf-4a35-80ab-635eba9d114c", Slot.user_id == 122
        )
        print(slot)
        exit()


if __name__ == "__main__":
    # asyncio.run(test())
    asyncio.run(init_models())
