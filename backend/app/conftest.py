import datetime

import pytest
import sqlalchemy as sa
from faker import Faker
from fastapi.testclient import TestClient
from pytest_pgsql.time import SQLAlchemyFreezegun
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app import models
from app.core.config import settings
from app.core.security import get_password_hash
from app.main import app
from app.utils.models_utils import StripeStatusEnum

fake = Faker()


@pytest.fixture
def fake_name():
    yield fake.name()


@pytest.fixture(scope="session")
def db():
    engine = sa.create_engine(settings.SQLALCHEMY_DATABASE_URI, echo=True, future=True)
    session = sessionmaker(engine, expire_on_commit=False, future=True)
    with session() as s:
        yield s


@pytest.fixture(scope="function")
async def async_engine():
    DATABASE_URL = settings.SQLALCHEMY_DATABASE_URI.replace(
        "postgresql://", "postgresql+asyncpg://"
    )
    engine = create_async_engine(DATABASE_URL)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture
async def async_db(async_engine):

    connection = await async_engine.connect()
    trans = await connection.begin()

    Session = sessionmaker(
        connection, expire_on_commit=False, future=True, class_=AsyncSession
    )
    session = Session()
    try:
        yield session
    finally:
        await session.close()
        await trans.rollback()
        await connection.close()


@pytest.fixture(scope="session")
def user_basic(db: sa.orm.Session):
    email = fake.email()
    q = sa.insert(models.User).values(
        {
            "name": fake.name(),
            "email": email,
            "birthday": fake.date_of_birth(),
            "hashed_password": get_password_hash("basic"),
            "scopes": "basic",
        }
    )
    db.execute(q)
    db.commit()
    q = sa.select(models.User).where(models.User.email == email)
    user = db.execute(q).scalar_one_or_none()

    yield user


@pytest.fixture(scope="session")
def user_admin(db: sa.orm.Session):
    email = fake.email()
    q = (
        sa.insert(models.User)
        .values(
            {
                "name": fake.name(),
                "email": email,
                "birthday": fake.date_of_birth(),
                "hashed_password": get_password_hash("admin"),
                "scopes": "basic,admin",
            }
        )
        .returning(models.User)
    )
    q = sa.select(models.User).from_statement(q)
    user = db.execute(q).scalar_one()
    db.commit()

    yield user


@pytest.fixture(scope="session")
def slot_with_stripe_id(user_basic: models.User, db: sa.orm.Session):
    q = (
        sa.insert(models.Slot)
        .values(
            {
                "stripe_id": fake.md5(),
                "user_id": user_basic.id,
                "product_id": 1,
                "stripe_status": StripeStatusEnum.PENDING,
                "reserved_until": datetime.datetime.utcnow()
                + datetime.timedelta(hours=1),
            }
        )
        .returning(models.Slot)
    )
    q = sa.select(models.Slot).from_statement(q)
    slot = db.execute(q).scalar_one()
    db.commit()
    yield slot


@pytest.fixture(scope="function")
def client():
    yield TestClient(app)


@pytest.fixture(scope="session")
def auth_client_basic(user_basic: models.User):

    c = TestClient(app)
    response = c.post(
        "/auth/token", data={"username": user_basic.email, "password": "basic"}
    )
    access_token = response.json()
    token = access_token["access_token"]
    c.headers.update({"Authorization": f"bearer {token}"})

    yield c


@pytest.fixture(scope="session")
def auth_client_admin(user_admin: models.User):

    c = TestClient(app)

    response = c.post(
        "/auth/token", data={"username": user_admin.email, "password": "admin"}
    )
    access_token = response.json()
    token = access_token["access_token"]
    c.headers.update({"Authorization": f"bearer {token}"})

    yield c
