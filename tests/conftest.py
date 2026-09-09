import os

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from sqlalchemy import text

from app.services.project import ProjectService

os.environ["ENV_FILE"] = ".env.test"

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

import app.security as app_security
from app.core.config import get_settings
from app.db import Base, get_db
from app.main import app
from app.services.comment import CommentService
from app.services.issue import IssueService
from app.services.user import UserService

settings = get_settings()

pytest_plugins = [
    "tests.fixtures.users",
    "tests.fixtures.projects",
    "tests.fixtures.issues",
    "tests.fixtures.comments",
]


# Argon2id takes ~50ms per hash. Below is used to low-cost rounds (down to 0.1ms per hash)
app_security.password_hash = PasswordHash(
    (Argon2Hasher(time_cost=1, memory_cost=8, parallelism=1),)
)

@pytest_asyncio.fixture
async def db():
    engine = create_async_engine(settings.database_url)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine,
        expire_on_commit=False
    )
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.execute(
                text("TRUNCATE TABLE users, projects, issues, comments, project_members CASCADE;")		
            )
            await session.commit()

    await engine.dispose()


@pytest_asyncio.fixture
async def user_service(db: AsyncSession):
    return UserService(db)

@pytest_asyncio.fixture
async def project_service(db: AsyncSession):
    return ProjectService(db)

@pytest_asyncio.fixture
async def issue_service(db: AsyncSession):
    return IssueService(db)

@pytest_asyncio.fixture
async def comment_service(db: AsyncSession):
    return CommentService(db)

@pytest_asyncio.fixture
async def client(db: AsyncSession):
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test/api/v1"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()
