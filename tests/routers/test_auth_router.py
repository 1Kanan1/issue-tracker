import jwt
from httpx import AsyncClient

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
