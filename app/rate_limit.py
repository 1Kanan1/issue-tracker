from collections import defaultdict, deque
from dataclasses import dataclass
from time import monotonic

from fastapi import HTTPException, Request, status

LOGIN_LIMIT = 10
LOGIN_WINDOW = 60.0

# Per-account lockout, keyed on username rather than source IP: an attacker
# rotating IPs must not get a fresh budget for the same account (CWE-307).
FAILURE_THRESHOLD = 5
BASE_DELAY = 1.0
MAX_DELAY = 60.0
FAILURE_WINDOW = 900.0

# Sliding window per client. Process-local, so `--workers N` multiplies the
# effective limit by N.
_attempts: dict[str, deque[float]] = defaultdict(deque)


@dataclass
class _Account:
    failures: int = 0
    locked_until: float = 0.0
    last_failure: float = 0.0


_accounts: dict[str, _Account] = {}


async def rate_limit_login(request: Request) -> None:
    client = request.client.host if request.client else "unknown"

    now = monotonic()
    hits = _attempts[client]

    while hits and now - hits[0] > LOGIN_WINDOW:
        hits.popleft()

    if len(hits) >= LOGIN_LIMIT:
        retry_after = int(LOGIN_WINDOW - (now - hits[0])) + 1
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts, try again later",
            headers={"Retry-After": str(retry_after)},
        )

    hits.append(now)


def check_account_locked(username: str) -> None:
    state = _accounts.get(username)

    if state is None:
        return

    now = monotonic()

    if now < state.locked_until:
        retry_after = int(state.locked_until - now) + 1
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Account temporarily locked after too many failed attempts",
            headers={"Retry-After": str(retry_after)},
        )

    if now - state.last_failure > FAILURE_WINDOW:
        state.failures = 0


def register_failure(username: str) -> None:
    now = monotonic()
    state = _accounts.setdefault(username, _Account())

    if now - state.last_failure > FAILURE_WINDOW:
        state.failures = 0

    state.failures += 1
    state.last_failure = now

    if state.failures >= FAILURE_THRESHOLD:
        delay = min(BASE_DELAY * 2 ** (state.failures - FAILURE_THRESHOLD), MAX_DELAY)
        state.locked_until = now + delay


def clear_failures(username: str) -> None:
    _accounts.pop(username, None)
