import pytest_asyncio

from app.models import Project, User
from app.schemas.project import ProjectCreate
from app.services.project import ProjectService


@pytest_asyncio.fixture
async def john_project_data() -> ProjectCreate:
    return ProjectCreate(name="Project1", description="")

@pytest_asyncio.fixture
async def alice_project_data() -> ProjectCreate:
    return ProjectCreate(name="Project2", description="")

@pytest_asyncio.fixture
async def john_project(
    project_service: ProjectService,
    john: User,
    john_project_data: ProjectCreate
) -> Project:
    return await project_service.create(john.id, john_project_data)

@pytest_asyncio.fixture
async def alice_project(
    project_service: ProjectService,
    alice: User,
    alice_project_data: ProjectCreate
) -> Project:
    return await project_service.create(alice.id, alice_project_data)
