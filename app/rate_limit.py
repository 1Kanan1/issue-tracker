from collections import defaultdict, deque
from time import monotonic

from fastapi import HTTPException, Request, status

LOGIN_LIMIT = 10
LOGIN_WINDOW = 60.0

# Sliding window per client. Process-local, so `--workers N` multiplies the
# effective limit by N.
_attempts: dict[str, deque[float]] = defaultdict(deque)


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
