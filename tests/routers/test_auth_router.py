from time import monotonic

import jwt
from httpx import AsyncClient

from app import rate_limit
from app.core import get_settings
from app.core.constants import ALGORITHM
from app.models import User
from app.schemas.user import UserCreate

settings = get_settings()


async def test_login_returns_token(
    client: AsyncClient, john: User, john_data: UserCreate
):
    res = await client.post(
        "/auth/login",
        json={"username": john_data.username, "password": john_data.password},
    )
    assert res.status_code == 200, res.text

    assert res.json() is not None
    assert "access_token" in res.json()
    payload = jwt.decode(
        res.json()["access_token"], settings.secret_key, algorithms=[ALGORITHM]
    )
    assert payload["sub"] == str(john.id)


async def test_login_rate_limited_after_repeated_attempts(
    client: AsyncClient, john_data: UserCreate
):
    codes = []
    for _ in range(rate_limit.LOGIN_LIMIT + 3):
        res = await client.post(
            "/auth/login",
            json={"username": john_data.username, "password": "wrong-password"},
        )
        codes.append(res.status_code)

    assert codes[: rate_limit.LOGIN_LIMIT] == [401] * rate_limit.LOGIN_LIMIT
    assert set(codes[rate_limit.LOGIN_LIMIT :]) == {429}
    assert "Retry-After" in res.headers


async def test_login_window_resets(
    client: AsyncClient, john: User, john_data: UserCreate
):
    for _ in range(rate_limit.LOGIN_LIMIT):
        await client.post(
            "/auth/login",
            json={"username": john_data.username, "password": "wrong-password"},
        )

    blocked = await client.post(
        "/auth/login",
        json={"username": john_data.username, "password": "wrong-password"},
    )
    assert blocked.status_code == 429, blocked.text

    # Simulate the window elapsing rather than sleeping through it.
    for hits in rate_limit._attempts.values():
        hits.clear()
        hits.append(monotonic() - rate_limit.LOGIN_WINDOW - 1)

    allowed = await client.post(
        "/auth/login",
        json={"username": john_data.username, "password": john_data.password},
    )
    assert allowed.status_code == 200, allowed.text
