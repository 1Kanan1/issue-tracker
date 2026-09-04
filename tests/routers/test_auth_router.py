import pytest
from httpx import AsyncClient

from app.schemas.user import UserCreate
from app.services.user import UserService


@pytest.mark.asyncio
async def test_login_returns_token(client: AsyncClient, service: UserService, user_data: UserCreate):
    await service.create(user_data)
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": user_data.username, "password": user_data.password}
    )

    assert response.status_code == 200
    assert response.json() is not None
    assert "access_token" in response.json()
