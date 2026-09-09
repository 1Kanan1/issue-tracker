import pytest
import pytest_asyncio

from app.enums import Priority
from app.models import Issue, Project, User
from app.schemas.issue import IssueCreate
from app.services.issue import IssueService


@pytest.fixture
def john_issue_data() -> IssueCreate:
    return IssueCreate(
        title="Sample Issue",
        description="Sample Description",
        priority=Priority.MEDIUM,
    )


@pytest_asyncio.fixture
async def john_issue(
    issue_service: IssueService,
    john: User,
    john_project: Project,
    john_issue_data: IssueCreate,
) -> Issue:
    return await issue_service.create(john, john_project.id, john_issue_data)
