from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings
from app.core.constants import ALGORITHM

settings = get_settings()

password_hash = PasswordHash.recommended()


def verify_password(plain_password: str | bytes, hashed_password: str | bytes) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def hash_password(password: str | bytes) -> str:
    return password_hash.hash(password)


def create_access_token(user_id: int) -> str:
    expires_at = datetime.now(UTC) + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    payload = {
        "sub": str(user_id),
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=ALGORITHM,
    )
