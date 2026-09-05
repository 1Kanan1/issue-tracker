
import pytest
import pytest_asyncio

from app.enums import Role
from app.models import User
from app.schemas.user import UserCreate
from app.security import create_access_token
from app.services.user import UserService


@pytest.fixture
def john_data() -> UserCreate:
    return UserCreate(
        username="john", email="john@example.com", password="secret123"
)

@pytest.fixture
def alice_data() -> UserCreate:
    return UserCreate(
        username="alice", email="alice@example.com", password="password123"
    )

@pytest.fixture
def admin_data() -> UserCreate:
    return UserCreate(
        username="admin", email="admin@example.com", password="supersecret123"
    )


@pytest_asyncio.fixture
async def john(service: UserService, john_data: UserCreate) -> User:
    return await service.create(john_data)

@pytest_asyncio.fixture
async def alice(service: UserService, alice_data: UserCreate) -> User:
    return await service.create(alice_data)

@pytest_asyncio.fixture
async def admin(service: UserService, admin_data: UserCreate) -> User:
    return await service.create(admin_data, role=Role.ADMIN)


@pytest_asyncio.fixture
async def john_token(john: User) -> str:
    return create_access_token(john.id)

@pytest_asyncio.fixture
async def alice_token(alice: User) -> str:
    return create_access_token(alice.id)

@pytest_asyncio.fixture
async def admin_token(admin: User) -> str:
    return create_access_token(admin.id)
