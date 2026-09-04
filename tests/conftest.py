import os

os.environ["ENV_FILE"] = ".env.test"

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings
from app.db import Base, get_db
from app.enums import Role
from app.main import app
from app.schemas.user import UserCreate
from app.services.user import UserService

settings = get_settings()


@pytest_asyncio.fixture
async def db():
    test_engine = create_async_engine(settings.database_url)

    TestSessionLocal = async_sessionmaker(
        test_engine,
        expire_on_commit=False,
    )

    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest_asyncio.fixture
async def service(db: AsyncSession):
    return UserService(db)

@pytest.fixture
def user_data() -> UserCreate:
    return UserCreate(
    username="johndoe", email="johndoe@example.com", password="secret"
)

@pytest_asyncio.fixture
async def admin_user(service: UserService):
    return await service.create(
        UserCreate(username="admin", email="admin@example.com", password="adminsecret"),
        role=Role.ADMIN,
    )

@pytest_asyncio.fixture
async def client(db: AsyncSession):
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()
