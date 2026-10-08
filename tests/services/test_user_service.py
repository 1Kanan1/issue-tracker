import pytest

import app.services.user as user_service_module
from app.exceptions.base import AlreadyExistsError, NotFoundError
from app.exceptions.user import (
    AuthenticationError,
)
from app.models import User
from app.schemas.user import UserCreate, UserUpdate
from app.security import verify_password
from app.services.user import UserService, _dummy_hash


async def test_authenticate_success(
    user_service: UserService, john: User, john_data: UserCreate
):
    authed = await user_service.authenticate(john_data.username, john_data.password)
    assert authed.id == john.id


async def test_authenticate_wrong_password(user_service: UserService, alice: User):
    with pytest.raises(AuthenticationError):
        await user_service.authenticate(alice.username, "wrongpass")


async def test_authenticate_user_not_found(user_service: UserService):
    with pytest.raises(AuthenticationError):
        await user_service.authenticate("nonexistent", "secret12345")


async def test_authenticate_does_equal_work_for_unknown_user(
    user_service: UserService, monkeypatch
):
    """A missing user must still cost one password verification (CWE-208)."""
    calls = []
    monkeypatch.setattr(
        user_service_module, "verify_password", lambda *a: calls.append(a) or False
    )

    with pytest.raises(AuthenticationError):
        await user_service.authenticate("nonexistent", "whatever")

    assert len(calls) == 1, "unknown user skipped the hash verification"


async def test_authenticate_does_equal_work_for_disabled_user(
    user_service: UserService, alice: User, monkeypatch
):
    calls = []
    real_verify = user_service_module.verify_password
    monkeypatch.setattr(
        user_service_module,
        "verify_password",
        lambda *a: (calls.append(a), real_verify(*a))[1],
    )

    await user_service.disable(alice.id)

    with pytest.raises(AuthenticationError):
        await user_service.authenticate(alice.username, "whatever")

    assert len(calls) == 1, "disabled user skipped the hash verification"


def test_dummy_hash_built_with_current_hasher():
    """Guards the import-time bug: a dummy built with a stale hasher makes
    unknown usernames measurably slower than real ones under test."""
    fresh = user_service_module.hash_password("probe")
    assert _dummy_hash().split("$")[3] == fresh.split("$")[3]


async def test_authenticate_disabled_user(
    user_service: UserService, john: User, john_data: UserCreate
):
    await user_service.disable(john.id)
    with pytest.raises(AuthenticationError):
        await user_service.authenticate(john_data.username, john_data.password)


async def test_get_user_by_username(user_service: UserService, john: User):
    result = await user_service.get_by_username(john.username)

    assert result is not None
    assert result.id == john.id
    assert result.username == john.username


async def test_create_user(user_service: UserService, alice_data: UserCreate):
    user = await user_service.create(alice_data)

    assert user.id is not None
    assert user.username == alice_data.username
    assert user.email == alice_data.email
    assert user.password_hash != alice_data.password

    with pytest.raises(AlreadyExistsError):
        # Attempt to create user with same credentials
        await user_service.create(alice_data)


async def test_update_user(
    user_service: UserService, alice: User, alice_data: UserCreate
):
    # Test field update + password re-hashing
    updated = await user_service.update(
        alice.id, UserUpdate(username="newname", password="newsecret")
    )
    assert updated.username == "newname"
    assert verify_password("newsecret", updated.password_hash)
    assert not verify_password(alice_data.password, updated.password_hash)


async def test_delete_user(user_service: UserService, john: User):
    await user_service.delete(john.id)

    with pytest.raises(NotFoundError):
        # Performs `service.get_by_id` first inside `service.delete`
        await user_service.delete(john.id)
