import pytest
import asyncio
import sqlalchemy as sa
from app.main import app
from app import models, deps
from app.core.security import get_password_hash
from fastapi.testclient import TestClient
from faker import Faker

fake = Faker()


@pytest.fixture(scope="session")
def event_loop(request):
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.mark.asyncio
@pytest.fixture(scope="session")
async def user_basic():
    async with deps.get_db_context() as db:
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
        await db.execute(q)
        await db.commit()
        q = sa.select(models.User).where(models.User.email == email)
        user = (await db.execute(q)).scalar_one_or_none()

        yield user

        q = sa.delete(models.User).where(models.User.email == email)
        await db.execute(q)
        await db.commit()


@pytest.mark.asyncio
@pytest.fixture(scope="session")
async def user_admin():
    async with deps.get_db_context() as db:
        email = fake.email()
        q = sa.insert(models.User).values(
            {
                "name": fake.name(),
                "email": email,
                "birthday": fake.date_of_birth(),
                "hashed_password": get_password_hash("admin"),
                "scopes": "basic,admin",
            }
        )
        await db.execute(q)
        await db.commit()
        q = sa.select(models.User).where(models.User.email == email)
        user = (await db.execute(q)).scalar_one_or_none()

        yield user

        q = sa.delete(models.User).where(models.User.email == email)
        await db.execute(q)
        await db.commit()


@pytest.fixture(scope="session")
def client():
    yield TestClient(app)


@pytest.fixture(scope="session")
def client_admin():
    yield TestClient(app)


@pytest.fixture(scope="session")
def client_basic():
    yield TestClient(app)


@pytest.fixture(scope="session")
def auth_client_basic(client_basic: TestClient, user_basic: models.User):

    response = client_basic.post(
        "/auth/token", data={"username": user_basic.email, "password": "basic"}
    )
    access_token = response.json()
    token = access_token["access_token"]
    client_basic.headers.update({"Authorization": f"bearer {token}"})

    yield client_basic


@pytest.fixture(scope="session")
def auth_client_admin(client_admin: TestClient, user_admin: models.User):

    response = client_admin.post(
        "/auth/token", data={"username": user_admin.email, "password": "admin"}
    )
    access_token = response.json()
    token = access_token["access_token"]
    client_admin.headers.update({"Authorization": f"bearer {token}"})

    yield client_admin
