import pytest

from app.exceptions.base import AlreadyExistsError, ForbiddenError, NotFoundError
from app.models import Project, User
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.project import ProjectService


@pytest.mark.asyncio
async def test_get_project(project_service: ProjectService, john: User, john_project: Project):
    project = await project_service.get_by_id(john, john_project.id)

    assert project.id == john_project.id
    assert project.owner == john

@pytest.mark.asyncio
async def test_project_not_found(project_service: ProjectService, john: User,):
    with pytest.raises(NotFoundError):
        await project_service.get_by_id(john, 999999)

@pytest.mark.asyncio
async def test_project_forbidden(project_service: ProjectService, john: User, alice_project: Project):
    with pytest.raises(ForbiddenError):
        await project_service.get_by_id(john, alice_project.id)

@pytest.mark.asyncio
async def test_get_projects(
    project_service: ProjectService,
    admin: User,
    john_project: Project,
    alice_project: Project
):
    projects = await project_service.list_for_user(admin)

    assert projects is not None
    assert len(projects) == 2
    assert john_project in projects
    assert alice_project in projects

@pytest.mark.asyncio
async def test_create_project(
    project_service: ProjectService,
    john: User,
    john_project_data: ProjectCreate
):
    project = await project_service.create(john.id, john_project_data)
    
    assert project.owner == john
    assert project.name == john_project_data.name
    assert project.description == john_project_data.description
    assert project.status == john_project_data.status


@pytest.mark.asyncio
async def test_project_already_exists(
    project_service: ProjectService,
    john: User,
    john_project: Project,
    john_project_data: ProjectCreate
):
    with pytest.raises(AlreadyExistsError):
        await project_service.create(john.id, john_project_data)


@pytest.mark.asyncio
async def test_list_projects_member_scoped(
    project_service: ProjectService,
    john: User,
    alice: User,
    john_project: Project,
    alice_project: Project
):
    john_projects = await project_service.list_for_user(john)
    assert len(john_projects) == 1
    assert john_projects[0].id == john_project.id

    alice_projects = await project_service.list_for_user(alice)
    assert len(alice_projects) == 1
    assert alice_projects[0].id == alice_project.id


@pytest.mark.asyncio
async def test_update_project(
    project_service: ProjectService,
    john: User,
    john_project: Project
):
    updated = await project_service.update(
        john,
        john_project.id,
        ProjectUpdate(name="Renamed Project", description="Updated description")
    )
    assert updated.name == "Renamed Project"
    assert updated.description == "Updated description"


@pytest.mark.asyncio
async def test_update_project_forbidden(
    project_service: ProjectService,
    alice: User,
    john_project: Project
):
    with pytest.raises(ForbiddenError):
        await project_service.update(
            alice,
            john_project.id,
            ProjectUpdate(name="Hacked Name")
        )


@pytest.mark.asyncio
async def test_add_member(
    project_service: ProjectService,
    john: User,
    alice: User,
    john_project: Project
):
    project = await project_service.add_member(john, john_project.id, alice.id)
    assert any(m.id == alice.id for m in project.members)

    # Alice can now view the project
    fetched = await project_service.get_by_id(alice, john_project.id)
    assert fetched.id == john_project.id


@pytest.mark.asyncio
async def test_add_member_forbidden(
    project_service: ProjectService,
    alice: User,
    john: User,
    john_project: Project
):
    with pytest.raises(ForbiddenError):
        await project_service.add_member(alice, john_project.id, john.id)


@pytest.mark.asyncio
async def test_add_member_user_not_found(
    project_service: ProjectService,
    john: User,
    john_project: Project
):
    with pytest.raises(NotFoundError):
        await project_service.add_member(john, john_project.id, 999999)


@pytest.mark.asyncio
async def test_remove_member_self(
    project_service: ProjectService,
    john: User,
    alice: User,
    john_project: Project
):
    await project_service.add_member(john, john_project.id, alice.id)

    # Alice leaves the project
    project = await project_service.remove_member(alice, john_project.id, alice.id)
    assert not any(m.id == alice.id for m in project.members)


@pytest.mark.asyncio
async def test_remove_member_by_owner(
    project_service: ProjectService,
    john: User,
    alice: User,
    john_project: Project
):
    await project_service.add_member(john, john_project.id, alice.id)

    project = await project_service.remove_member(john, john_project.id, alice.id)
    assert not any(m.id == alice.id for m in project.members)


@pytest.mark.asyncio
async def test_remove_member_forbidden(
    project_service: ProjectService,
    admin: User,
    john: User,
    alice: User,
    john_project: Project
):
    await project_service.add_member(john, john_project.id, alice.id)

    with pytest.raises(ForbiddenError):
        await project_service.remove_member(alice, john_project.id, john.id)

