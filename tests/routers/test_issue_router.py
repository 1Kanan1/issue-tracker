import pytest
from httpx import AsyncClient

from app.enums import IssueStatus, Priority
from app.models import Issue, Project, User
from app.services.project import ProjectService


@pytest.mark.asyncio
async def test_create_issue_owner(
    client: AsyncClient,
    john: User,
    john_token: str,
    john_project: Project,
):
    res = await client.post(
        f"/projects/{john_project.id}/issues",
        json={
            "title": "Bug in checkout",
            "description": "Payment gateway timeout",
            "priority": Priority.HIGH.value,
        },
        headers={"Authorization": f"Bearer {john_token}"},
    )
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["title"] == "Bug in checkout"
    assert data["priority"] == Priority.HIGH.value
    assert data["status"] == IssueStatus.OPEN.value
    assert data["project_id"] == john_project.id
    assert data["creator"]["id"] == john.id
    assert data["assignee"] is None


@pytest.mark.asyncio
async def test_create_issue_with_member_assignee(
    client: AsyncClient,
    john_token: str,
    john_project: Project,
    alice: User,
    project_service: ProjectService,
    john: User,
):
    await project_service.add_member(john, john_project.id, alice.id)

    res = await client.post(
        f"/projects/{john_project.id}/issues",
        json={
            "title": "Task for Alice",
            "assignee_id": alice.id,
        },
        headers={"Authorization": f"Bearer {john_token}"},
    )
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["assignee"]["id"] == alice.id


@pytest.mark.asyncio
async def test_create_issue_assignee_not_member_forbidden(
    client: AsyncClient,
    john_token: str,
    john_project: Project,
    alice: User,
):
    res = await client.post(
        f"/projects/{john_project.id}/issues",
        json={
            "title": "Invalid assignment",
            "assignee_id": alice.id,
        },
        headers={"Authorization": f"Bearer {john_token}"},
    )
    assert res.status_code == 403, res.text


@pytest.mark.asyncio
async def test_create_issue_non_member_forbidden(
    client: AsyncClient,
    alice_token: str,
    john_project: Project,
):
    res = await client.post(
        f"/projects/{john_project.id}/issues",
        json={"title": "Intruder issue"},
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert res.status_code == 403, res.text


@pytest.mark.asyncio
async def test_create_issue_project_not_found(
    client: AsyncClient,
    admin_token: str,
):
    res = await client.post(
        "/projects/9999/issues",
        json={"title": "Ghost project issue"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 404, res.text


@pytest.mark.asyncio
async def test_get_issue_success(
    client: AsyncClient,
    john_token: str,
    john_issue: Issue,
):
    res = await client.get(
        f"/issues/{john_issue.id}",
        headers={"Authorization": f"Bearer {john_token}"},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["id"] == john_issue.id
    assert data["title"] == john_issue.title


@pytest.mark.asyncio
async def test_get_issue_forbidden_for_non_member(
    client: AsyncClient,
    alice_token: str,
    john_issue: Issue,
):
    res = await client.get(
        f"/issues/{john_issue.id}",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert res.status_code == 403, res.text


@pytest.mark.asyncio
async def test_list_issues_for_project(
    client: AsyncClient,
    john_token: str,
    john_project: Project,
):
    await client.post(
        f"/projects/{john_project.id}/issues",
        json={"title": "Issue 1"},
        headers={"Authorization": f"Bearer {john_token}"},
    )
    await client.post(
        f"/projects/{john_project.id}/issues",
        json={"title": "Issue 2"},
        headers={"Authorization": f"Bearer {john_token}"},
    )

    res = await client.get(
        f"/projects/{john_project.id}/issues",
        headers={"Authorization": f"Bearer {john_token}"},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert len(data) == 2
    assert {item["title"] for item in data} == {"Issue 1", "Issue 2"}


@pytest.mark.asyncio
async def test_update_issue_status_and_assignee(
    client: AsyncClient,
    john_token: str,
    john_project: Project,
    john_issue: Issue,
    alice: User,
    john: User,
    project_service: ProjectService,
):
    await project_service.add_member(john, john_project.id, alice.id)

    res = await client.patch(
        f"/issues/{john_issue.id}",
        json={
            "status": IssueStatus.IN_PROGRESS.value,
            "priority": Priority.CRITICAL.value,
            "assignee_id": alice.id,
        },
        headers={"Authorization": f"Bearer {john_token}"},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["status"] == IssueStatus.IN_PROGRESS.value
    assert data["priority"] == Priority.CRITICAL.value
    assert data["assignee"]["id"] == alice.id


@pytest.mark.asyncio
async def test_delete_issue(
    client: AsyncClient,
    john_token: str,
    alice_token: str,
    john_issue: Issue,
):
    # Non-member cannot delete
    res_forbidden = await client.delete(
        f"/issues/{john_issue.id}",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert res_forbidden.status_code == 403, res_forbidden.text

    # Owner can delete
    res_delete = await client.delete(
        f"/issues/{john_issue.id}",
        headers={"Authorization": f"Bearer {john_token}"},
    )
    assert res_delete.status_code == 204, res_delete.text

    # Verify deleted
    res_get = await client.get(
        f"/issues/{john_issue.id}",
        headers={"Authorization": f"Bearer {john_token}"},
    )
    assert res_get.status_code == 404, res_get.text
