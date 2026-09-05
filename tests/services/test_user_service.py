import pytest

from app.exceptions.base import AlreadyExistsError, NotFoundError
from app.exceptions.user import (
    AuthenticationError,
)
from app.models import User
from app.schemas.user import UserCreate, UserUpdate
from app.security import verify_password
from app.services.user import UserService


@pytest.mark.asyncio
async def test_authenticate_success(service: UserService, john: User, john_data: UserCreate):
    authed = await service.authenticate(john_data.username, john_data.password)
    assert authed.id == john.id

@pytest.mark.asyncio
async def test_authenticate_wrong_password(service: UserService, alice: User):
    with pytest.raises(AuthenticationError):
        await service.authenticate(alice.username, "wrongpass")

@pytest.mark.asyncio
async def test_authenticate_user_not_found(service: UserService):
    with pytest.raises(AuthenticationError):
        await service.authenticate("nonexistent", "secret12345")

@pytest.mark.asyncio
async def test_authenticate_disabled_user(service: UserService, john: User, john_data: UserCreate):
    await service.disable(john.id)
    with pytest.raises(AuthenticationError):
        await service.authenticate(john_data.username, john_data.password)

@pytest.mark.asyncio
async def test_get_user_by_username(service: UserService, john: User):
    result = await service.get_by_username(john.username)

    assert result is not None
    assert result.id == john.id
    assert result.username == john.username

@pytest.mark.asyncio
async def test_create_user(service: UserService, alice_data: UserCreate):
    user = await service.create(alice_data)

    assert user.id is not None
    assert user.username == alice_data.username
    assert user.email == alice_data.email
    assert user.password_hash != alice_data.password

    with pytest.raises(AlreadyExistsError):
        # Attempt to create user with same credentials
        await service.create(alice_data)


@pytest.mark.asyncio
async def test_update_user(service: UserService, alice: User, alice_data: UserCreate):
    # Test field update + password re-hashing
    updated = await service.update(
        alice.id, UserUpdate(username="newname", password="newsecret")
    )
    assert updated.username == "newname"
    assert verify_password("newsecret", updated.password_hash)
    assert not verify_password(alice_data.password, updated.password_hash)


@pytest.mark.asyncio
async def test_delete_user(service: UserService, john: User):
    await service.delete(john.id)

    with pytest.raises(NotFoundError):
        # Performs `service.get_by_id` first inside `service.delete`
        await service.delete(john.id)
