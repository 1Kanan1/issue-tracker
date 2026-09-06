import pytest
from httpx import AsyncClient

from app.models import Project, User


@pytest.mark.asyncio
async def test_create_project_admin(client: AsyncClient, admin_token: str):
    res = await client.post(
        "/projects",
        json={"name": "Alpha Project", "description": "Alpha Description"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["name"] == "Alpha Project"
    assert data["description"] == "Alpha Description"
    assert "owner" in data
    assert data["members"] == []


@pytest.mark.asyncio
async def test_create_project_member_forbidden(client: AsyncClient, alice_token: str):
    res = await client.post(
        "/projects",
        json={"name": "Forbidden Project"},
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert res.status_code == 403, res.text


@pytest.mark.asyncio
async def test_list_projects(
    client: AsyncClient,
    admin_token: str,
    john_token: str,
    john_project: Project,
    alice_project: Project,
):
    res_admin = await client.get(
        "/projects",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_admin.status_code == 200, res_admin.text
    admin_list = res_admin.json()
    assert len(admin_list) == 2

    res_john = await client.get(
        "/projects",
        headers={"Authorization": f"Bearer {john_token}"},
    )
    assert res_john.status_code == 200, res_john.text
    john_list = res_john.json()
    assert len(john_list) == 1
    assert john_list[0]["id"] == john_project.id


@pytest.mark.asyncio
async def test_get_project_success(
    client: AsyncClient,
    john_token: str,
    john_project: Project,
):
    res = await client.get(
        f"/projects/{john_project.id}",
        headers={"Authorization": f"Bearer {john_token}"},
    )
    assert res.status_code == 200, res.text
    assert res.json()["id"] == john_project.id


@pytest.mark.asyncio
async def test_get_project_forbidden(
    client: AsyncClient,
    alice_token: str,
    john_project: Project,
):
    res = await client.get(
        f"/projects/{john_project.id}",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert res.status_code == 403, res.text


@pytest.mark.asyncio
async def test_get_project_not_found(client: AsyncClient, admin_token: str):
    res = await client.get(
        "/projects/999999",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 404, res.text


@pytest.mark.asyncio
async def test_update_project(
    client: AsyncClient,
    john_token: str,
    john_project: Project,
):
    res = await client.patch(
        f"/projects/{john_project.id}",
        json={"name": "New Project Title", "description": "New Description"},
        headers={"Authorization": f"Bearer {john_token}"},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["name"] == "New Project Title"
    assert data["description"] == "New Description"


@pytest.mark.asyncio
async def test_update_project_forbidden(
    client: AsyncClient,
    alice_token: str,
    john_project: Project,
):
    res = await client.patch(
        f"/projects/{john_project.id}",
        json={"name": "Hacked Title"},
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert res.status_code == 403, res.text


@pytest.mark.asyncio
async def test_add_and_remove_member(
    client: AsyncClient,
    john_token: str,
    alice_token: str,
    alice: User,
    john_project: Project,
):
    add_res = await client.post(
        f"/projects/{john_project.id}/members/{alice.id}",
        headers={"Authorization": f"Bearer {john_token}"},
    )
    assert add_res.status_code == 200, add_res.text
    member_ids = [m["id"] for m in add_res.json()["members"]]
    assert alice.id in member_ids

    view_res = await client.get(
        f"/projects/{john_project.id}",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert view_res.status_code == 200, view_res.text

    remove_res = await client.delete(
        f"/projects/{john_project.id}/members/{alice.id}",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert remove_res.status_code == 200, remove_res.text
    remaining_ids = [m["id"] for m in remove_res.json()["members"]]
    assert alice.id not in remaining_ids


@pytest.mark.asyncio
async def test_add_member_forbidden(
    client: AsyncClient,
    alice_token: str,
    john: User,
    john_project: Project,
):
    res = await client.post(
        f"/projects/{john_project.id}/members/{john.id}",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert res.status_code == 403, res.text
