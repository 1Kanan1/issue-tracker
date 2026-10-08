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
    # Distinct usernames so the per-account lockout never engages and only the
    # per-IP limiter is under test.
    codes = []
    for i in range(rate_limit.LOGIN_LIMIT + 3):
        res = await client.post(
            "/auth/login",
            json={"username": f"sprayed-{i}", "password": "wrong-password"},
        )
        codes.append(res.status_code)

    assert codes[: rate_limit.LOGIN_LIMIT] == [401] * rate_limit.LOGIN_LIMIT
    assert set(codes[rate_limit.LOGIN_LIMIT :]) == {429}
    assert "Retry-After" in res.headers


async def test_login_window_resets(
    client: AsyncClient, john: User, john_data: UserCreate
):
    for i in range(rate_limit.LOGIN_LIMIT):
        await client.post(
            "/auth/login",
            json={"username": f"sprayed-{i}", "password": "wrong-password"},
        )

    blocked = await client.post(
        "/auth/login",
        json={"username": john_data.username, "password": john_data.password},
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


async def _fail(client: AsyncClient, username: str, n: int) -> list[int]:
    codes = []
    for _ in range(n):
        res = await client.post(
            "/auth/login", json={"username": username, "password": "wrong-password"}
        )
        codes.append(res.status_code)
    return codes


async def test_account_locks_after_threshold_failures(
    client: AsyncClient, john_data: UserCreate
):
    codes = await _fail(client, john_data.username, rate_limit.FAILURE_THRESHOLD + 1)

    assert codes[: rate_limit.FAILURE_THRESHOLD] == [401] * rate_limit.FAILURE_THRESHOLD
    assert codes[rate_limit.FAILURE_THRESHOLD] == 429


async def test_locked_account_keeps_reporting_the_same_delay(
    client: AsyncClient, john_data: UserCreate
):
    """Blocked requests never reach register_failure, so the penalty is flat
    within one burst. Escalation happens across lockout cycles instead."""
    delays = []
    for _ in range(rate_limit.FAILURE_THRESHOLD + 3):
        res = await client.post(
            "/auth/login",
            json={"username": john_data.username, "password": "wrong-password"},
        )
        if res.status_code == 429:
            delays.append(int(res.headers["Retry-After"]))

    assert delays == [1, 1, 1], delays


def test_lock_delay_doubles_and_then_caps():
    for _ in range(rate_limit.FAILURE_THRESHOLD):
        rate_limit.register_failure("victim")

    delays = []
    for _ in range(8):
        state = rate_limit._accounts["victim"]
        delays.append(round(state.locked_until - state.last_failure))
        rate_limit.register_failure("victim")

    assert delays[:4] == [1, 2, 4, 8], delays
    assert max(delays) == rate_limit.MAX_DELAY


async def test_account_lock_expires(
    client: AsyncClient, john: User, john_data: UserCreate
):
    await _fail(client, john_data.username, rate_limit.FAILURE_THRESHOLD)
    blocked = await client.post(
        "/auth/login",
        json={"username": john_data.username, "password": john_data.password},
    )
    assert blocked.status_code == 429, blocked.text

    rate_limit._accounts[john_data.username].locked_until = monotonic() - 1

    allowed = await client.post(
        "/auth/login",
        json={"username": john_data.username, "password": john_data.password},
    )
    assert allowed.status_code == 200, allowed.text


async def test_successful_login_clears_failure_count(
    client: AsyncClient, john: User, john_data: UserCreate
):
    await _fail(client, john_data.username, rate_limit.FAILURE_THRESHOLD - 1)
    assert rate_limit._accounts[john_data.username].failures == (
        rate_limit.FAILURE_THRESHOLD - 1
    )

    ok = await client.post(
        "/auth/login",
        json={"username": john_data.username, "password": john_data.password},
    )
    assert ok.status_code == 200, ok.text
    assert john_data.username not in rate_limit._accounts


async def test_failures_outside_window_do_not_accumulate(
    client: AsyncClient, john_data: UserCreate
):
    await _fail(client, john_data.username, rate_limit.FAILURE_THRESHOLD - 1)
    state = rate_limit._accounts[john_data.username]
    state.last_failure = monotonic() - rate_limit.FAILURE_WINDOW - 1

    await _fail(client, john_data.username, 1)
    assert rate_limit._accounts[john_data.username].failures == 1
