import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)

from app.db import Base

# from app.models.user import User

test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")

TestSessionLocal = async_sessionmaker(
    test_engine,
    expire_on_commit=False,
)


@pytest_asyncio.fixture
async def db():
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
