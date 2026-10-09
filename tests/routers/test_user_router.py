from httpx import AsyncClient

from app.models import User
from app.schemas.user import UserCreate


async def test_get_me(client: AsyncClient, alice_token: str, alice: User):
    res = await client.get(
        "/users/me", headers={"Authorization": f"Bearer {alice_token}"}
    )
    assert res.status_code == 200, res.text

    user = res.json()
    assert user is not None
    assert user["username"] == alice.username
    assert user["email"] == alice.email
    assert "password_hash" not in user


async def test_get_user(client: AsyncClient, john_token: str, john: User):
    res = await client.get(
        "/users/me", headers={"Authorization": f"Bearer {john_token}"}
    )
    user = res.json()

    res = await client.get(
        f"/users/{user['id']}", headers={"Authorization": f"Bearer {john_token}"}
    )
    assert res.status_code == 200, res.text

    user = res.json()
    assert user is not None
    assert user["username"] == john.username
    assert user["email"] == john.email
    assert "password_hash" not in user


async def test_get_user_not_found(client: AsyncClient, john_token: str):
    res = await client.get(
        "/users/999999", headers={"Authorization": f"Bearer {john_token}"}
    )

    assert res.status_code == 404, res.text
    assert "not found" in res.json()["detail"].lower()


async def test_get_users(client: AsyncClient, admin_token: str, alice_token: str):
    res = await client.get("/users", headers={"Authorization": f"Bearer {alice_token}"})
    assert res.status_code == 403, res.text

    res = await client.get("/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200, res.text

    users = res.json()
    assert type(users) == list


async def test_post_user(client: AsyncClient, alice_data: UserCreate):
    res = await client.post(
        "/users",
        json={
            "username": alice_data.username,
            "email": alice_data.email,
            "password": alice_data.password,
        },
    )

    assert res.status_code == 201, res.text
    assert res.json() is not None
    assert "password_hash" not in res.json()


async def test_post_user_duplicate(client: AsyncClient, alice_data: UserCreate):
    json_data = {
        "username": alice_data.username,
        "email": alice_data.email,
        "password": alice_data.password,
    }

    await client.post("/users", json=json_data)
    res = await client.post("/users", json=json_data)

    assert res.status_code == 409, res.text
    assert res.json() is not None

    result = res.json()

    assert "detail" in result
    assert "already exists" in result["detail"]


async def test_update_me(client: AsyncClient, john_data: UserCreate, john_token: str):
    new_data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "newsecret123",
    }

    res = await client.patch(
        "/users/me", json=new_data, headers={"Authorization": f"Bearer {john_token}"}
    )
    assert res.status_code == 200, res.text

    upd_user = res.json()
    assert upd_user["username"] != john_data.username
    assert upd_user["email"] != john_data.email
    assert "password_hash" not in upd_user


async def test_update_me_password_too_short_rejected(
    client: AsyncClient, john_token: str
):
    res = await client.patch(
        "/users/me",
        json={"password": "short"},
        headers={"Authorization": f"Bearer {john_token}"},
    )

    assert res.status_code == 422, res.text


async def test_admin_can_promote_another_user(
    client: AsyncClient, admin_token: str, john: User
):
    res = await client.patch(
        f"/users/{john.id}",
        json={"role": "manager"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert res.status_code == 200, res.text
    assert res.json()["role"] == "manager"


async def test_admin_cannot_change_own_role(
    client: AsyncClient, admin_token: str, admin: User
):
    res = await client.patch(
        f"/users/{admin.id}",
        json={"role": "member"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert res.status_code == 422, res.text


async def test_member_cannot_set_own_role_via_me(
    client: AsyncClient, john_token: str, john: User
):
    """Role is not in UserUpdate, so the request is accepted but ignored."""
    res = await client.patch(
        "/users/me",
        json={"role": "admin"},
        headers={"Authorization": f"Bearer {john_token}"},
    )

    assert res.status_code == 200, res.text
    assert res.json()["role"] == "member"


async def test_update_me_empty_password_rejected(
    client: AsyncClient, john_token: str, john_data: UserCreate
):
    res = await client.patch(
        "/users/me",
        json={"password": ""},
        headers={"Authorization": f"Bearer {john_token}"},
    )
    assert res.status_code == 422, res.text

    # The rejection has to hold at the credential check too, not just at the
    # request body, or the account is left with a blank-password login.
    login = await client.post(
        "/auth/login", json={"username": john_data.username, "password": ""}
    )
    assert login.status_code == 401, login.text


async def test_update_me_password_containing_stored_username_rejected(
    client: AsyncClient, john_token: str, john_data: UserCreate
):
    # No username in the payload, so only the service can see that "john" is
    # the account's actual username.
    res = await client.patch(
        "/users/me",
        json={"password": f"xx{john_data.username}xx"},
        headers={"Authorization": f"Bearer {john_token}"},
    )

    assert res.status_code == 422, res.text


async def test_update_me_password_and_username_checked_together(
    client: AsyncClient, john_token: str
):
    res = await client.patch(
        "/users/me",
        json={"username": "newuser", "password": "newuser123"},
        headers={"Authorization": f"Bearer {john_token}"},
    )

    assert res.status_code == 422, res.text


async def test_update_me_valid_password_is_applied(
    client: AsyncClient, john_token: str, john_data: UserCreate
):
    res = await client.patch(
        "/users/me",
        json={"password": "brandnewpass99"},
        headers={"Authorization": f"Bearer {john_token}"},
    )
    assert res.status_code == 200, res.text

    login = await client.post(
        "/auth/login",
        json={"username": john_data.username, "password": "brandnewpass99"},
    )
    assert login.status_code == 200, login.text

    stale = await client.post(
        "/auth/login",
        json={"username": john_data.username, "password": john_data.password},
    )
    assert stale.status_code == 401, stale.text


async def test_update_me_null_password_leaves_it_unchanged(
    client: AsyncClient, john_token: str, john_data: UserCreate
):
    res = await client.patch(
        "/users/me",
        json={"password": None},
        headers={"Authorization": f"Bearer {john_token}"},
    )
    assert res.status_code == 200, res.text

    login = await client.post(
        "/auth/login",
        json={"username": john_data.username, "password": john_data.password},
    )
    assert login.status_code == 200, login.text


async def test_disable_user(
    client: AsyncClient, admin_token: str, john: User, john_data: UserCreate
):
    res = await client.patch(
        f"/users/{john.id}/disable", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 204, res.text

    res = await client.post(
        "/auth/login",
        json={"username": john_data.username, "password": john_data.password},
    )
    assert res.status_code == 401, res.text


async def test_delete_user(
    client: AsyncClient, john: User, john_token: str, admin_token: str
):
    res = await client.delete(
        f"/users/{john.id}", headers={"Authorization": f"Bearer {john_token}"}
    )
    assert res.status_code == 403, res.text

    res = await client.delete(
        f"/users/{john.id}", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 204, res.text
