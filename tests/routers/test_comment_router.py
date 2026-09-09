import pytest
from httpx import AsyncClient

from app.models import Issue, Project, User
from app.services.project import ProjectService


@pytest.mark.asyncio
async def test_create_comment_member_success(
    client: AsyncClient,
    john: User,
    john_project: Project,
    john_issue: Issue,
    alice: User,
    alice_token: str,
    project_service: ProjectService,
):
    await project_service.add_member(john, john_project.id, alice.id)

    response = await client.post(
        f"/issues/{john_issue.id}/comments",
        json={"content": "Alice's comment on the issue"},
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["content"] == "Alice's comment on the issue"
    assert data["author"]["id"] == alice.id
    assert data["issue_id"] == john_issue.id
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_comment_non_member_forbidden(
    client: AsyncClient,
    john_issue: Issue,
    alice_token: str,
):
    response = await client.post(
        f"/issues/{john_issue.id}/comments",
        json={"content": "Intruder comment"},
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_create_comment_issue_not_found(
    client: AsyncClient,
    john_token: str,
):
    response = await client.post(
        "/issues/9999/comments",
        json={"content": "Ghost comment"},
        headers={"Authorization": f"Bearer {john_token}"},
    )
    assert response.status_code == 404, response.text


@pytest.mark.asyncio
async def test_list_comments_chronological(
    client: AsyncClient,
    john: User,
    john_token: str,
    john_project: Project,
    john_issue: Issue,
    alice: User,
    alice_token: str,
    project_service: ProjectService,
):
    await project_service.add_member(john, john_project.id, alice.id)

    await client.post(
        f"/issues/{john_issue.id}/comments",
        json={"content": "First comment"},
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    await client.post(
        f"/issues/{john_issue.id}/comments",
        json={"content": "Second comment"},
        headers={"Authorization": f"Bearer {john_token}"},
    )

    response = await client.get(
        f"/issues/{john_issue.id}/comments",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data) == 2
    assert data[0]["content"] == "First comment"
    assert data[0]["author"]["id"] == alice.id
    assert data[1]["content"] == "Second comment"
    assert data[1]["author"]["id"] == john.id


@pytest.mark.asyncio
async def test_list_comments_non_member_forbidden(
    client: AsyncClient,
    john_issue: Issue,
    alice_token: str,
):
    response = await client.get(
        f"/issues/{john_issue.id}/comments",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_update_comment_author_success(
    client: AsyncClient,
    john_token: str,
    john_issue: Issue,
):
    res_create = await client.post(
        f"/issues/{john_issue.id}/comments",
        json={"content": "Original comment"},
        headers={"Authorization": f"Bearer {john_token}"},
    )
    comment_id = res_create.json()["id"]

    response = await client.patch(
        f"/comments/{comment_id}",
        json={"content": "Edited comment content"},
        headers={"Authorization": f"Bearer {john_token}"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["content"] == "Edited comment content"


@pytest.mark.asyncio
async def test_update_comment_non_author_forbidden(
    client: AsyncClient,
    john: User,
    john_token: str,
    john_project: Project,
    john_issue: Issue,
    alice: User,
    alice_token: str,
    project_service: ProjectService,
):
    await project_service.add_member(john, john_project.id, alice.id)

    res_create = await client.post(
        f"/issues/{john_issue.id}/comments",
        json={"content": "Alice's original comment"},
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    comment_id = res_create.json()["id"]

    # Even though John is the project owner, only the author can edit comment content
    response = await client.patch(
        f"/comments/{comment_id}",
        json={"content": "John trying to overwrite Alice's words"},
        headers={"Authorization": f"Bearer {john_token}"},
    )
    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_delete_comment_author_success(
    client: AsyncClient,
    john_token: str,
    john_issue: Issue,
):
    res_create = await client.post(
        f"/issues/{john_issue.id}/comments",
        json={"content": "To be deleted by author"},
        headers={"Authorization": f"Bearer {john_token}"},
    )
    comment_id = res_create.json()["id"]

    response = await client.delete(
        f"/comments/{comment_id}",
        headers={"Authorization": f"Bearer {john_token}"},
    )
    assert response.status_code == 204, response.text


@pytest.mark.asyncio
async def test_delete_comment_project_owner_success(
    client: AsyncClient,
    john: User,
    john_token: str,
    john_project: Project,
    john_issue: Issue,
    alice: User,
    alice_token: str,
    project_service: ProjectService,
):
    await project_service.add_member(john, john_project.id, alice.id)

    res_create = await client.post(
        f"/issues/{john_issue.id}/comments",
        json={"content": "Alice writes something project owner removes"},
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    comment_id = res_create.json()["id"]

    # Project owner (John) moderates and deletes Alice's comment
    response = await client.delete(
        f"/comments/{comment_id}",
        headers={"Authorization": f"Bearer {john_token}"},
    )
    assert response.status_code == 204, response.text


@pytest.mark.asyncio
async def test_delete_comment_other_member_forbidden(
    client: AsyncClient,
    john: User,
    john_project: Project,
    john_issue: Issue,
    alice: User,
    alice_token: str,
    bob: User,
    bob_token: str,
    project_service: ProjectService,
):
    await project_service.add_member(john, john_project.id, alice.id)
    await project_service.add_member(john, john_project.id, bob.id)

    res_create = await client.post(
        f"/issues/{john_issue.id}/comments",
        json={"content": "Alice's comment"},
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    comment_id = res_create.json()["id"]

    # Bob (regular member, not author, not project owner) tries to delete Alice's comment
    response = await client.delete(
        f"/comments/{comment_id}",
        headers={"Authorization": f"Bearer {bob_token}"},
    )
    assert response.status_code == 403, response.text
