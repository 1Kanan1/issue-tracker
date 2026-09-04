# • POST /api/v1/users → 201 Created + verify password_hash is not in response.
# • POST /api/v1/users (duplicate) → 409 Conflict.
# • GET /api/v1/users/{id} → 200 OK + 404 Not Found.
# • PATCH /api/v1/users/{id} → 200 OK with updated fields.
# • DELETE /api/v1/users/{id} → 204 No Content (verify permissions when admin token is provided).

import pytest
from httpx import AsyncClient

from app.schemas.user import UserCreate
from app.services.user import UserService


@pytest.mark.asyncio
async def test_post_user(client: AsyncClient):
    response = await client.post(
        "/api/v1/users",
        json={"username": "alice", "email": "alice@example.com", "password": "alicesecret"}
    )

    assert response.status_code == 201
    assert response.json() is not None
    assert "password_hash" not in response.json()

@pytest.mark.asyncio
async def test_post_user_duplicate(client: AsyncClient):
    await client.post(
        "/api/v1/users",
        json={"username": "alice", "email": "alice@example.com", "password": "alicesecret"}
    )

    response = await client.post(
        "/api/v1/users",
        json={"username": "alice", "email": "alice@example.com", "password": "alicesecret"}
    )

    assert response.status_code == 409
    assert response.json() is not None

    result = response.json()

    assert "detail" in result
    assert result["detail"] == "User already exists"

@pytest.mark.asyncio
async def test_get_user(client: AsyncClient, service: UserService, user_data: UserCreate):
    user = await service.create(user_data)

    response = await client.get(
        f"/api/v1/users/{user.id}"
    )

    assert response.status_code == 200
    assert response.json() is not None

    result = response.json()

    assert result["id"] == user.id
    assert result["username"] == user.username
    assert "password_hash" not in result
