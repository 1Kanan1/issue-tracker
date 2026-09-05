import pytest
from httpx import AsyncClient

from app.schemas.user import UserCreate


@pytest.mark.asyncio
async def test_login_returns_token(client: AsyncClient, john_token: str, john_data: UserCreate):
    res = await client.post(
        "/auth/login",
        json={"username": john_data.username, "password": john_data.password}
    )
    assert res.status_code == 200, res.text

    assert res.json() is not None
    assert "access_token" in res.json()
    assert res.json()["access_token"] == john_token
