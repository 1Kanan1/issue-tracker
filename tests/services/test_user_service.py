import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.user import (
    AuthenticationError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.schemas.user import UserCreate, UserUpdate
from app.security import verify_password
from app.services.user import UserService


@pytest.mark.asyncio
async def test_authenticate_success(service: UserService, user_data: UserCreate):
    user = await service.create(user_data)
    authed = await service.authenticate("johndoe", "secret")
    assert authed.id == user.id

@pytest.mark.asyncio
async def test_authenticate_wrong_password(service: UserService, user_data: UserCreate):
    await service.create(user_data)
    with pytest.raises(AuthenticationError):
        await service.authenticate("johndoe", "wrongpass")

@pytest.mark.asyncio
async def test_authenticate_user_not_found(service: UserService):
    with pytest.raises(AuthenticationError):
        await service.authenticate("nonexistent", "secret")

@pytest.mark.asyncio
async def test_authenticate_disabled_user(service: UserService, db: AsyncSession, user_data: UserCreate):
    user = await service.create(user_data)
    user.is_disabled = True
    await db.commit()
    with pytest.raises(AuthenticationError):
        await service.authenticate("johndoe", "secret")

@pytest.mark.asyncio
async def test_get_user_by_username(service: UserService, user_data: UserCreate):
    user = await service.create(user_data)

    result = await service.get_by_username(user.username)

    assert result is not None
    assert result.id == user.id
    assert result.username == user.username

@pytest.mark.asyncio
async def test_create_user(service: UserService, user_data: UserCreate):
    user = await service.create(user_data)

    assert user.id is not None
    assert user.username == user_data.username
    assert user.email == user_data.email
    assert user.password_hash != user_data.password

    with pytest.raises(UserAlreadyExistsError):
        # Attempt to create user with same credentials
        await service.create(user_data)


@pytest.mark.asyncio
async def test_update_user(service: UserService, user_data: UserCreate):
    user = await service.create(user_data)

    # Test field update + password re-hashing
    updated = await service.update(
        user.id, UserUpdate(username="newname", password="newsecret")
    )
    assert updated.username == "newname"
    assert verify_password("newsecret", updated.password_hash)
    assert not verify_password("secret", updated.password_hash)


@pytest.mark.asyncio
async def test_delete_user(service: UserService, user_data: UserCreate):
    user = await service.create(user_data)

    await service.delete(user.id)

    with pytest.raises(UserNotFoundError):
        # Performs `service.get_by_id` first inside `service.delete`
        await service.delete(user.id)
