import pytest
import pytest_asyncio

from app.models import Comment, Issue, User
from app.schemas.comment import CommentCreate
from app.services.comment import CommentService


@pytest.fixture
def john_comment_data() -> CommentCreate:
    return CommentCreate(content="Sample comment text")


@pytest_asyncio.fixture
async def john_comment(
    comment_service: CommentService,
    john: User,
    john_issue: Issue,
    john_comment_data: CommentCreate,
) -> Comment:
    return await comment_service.create(john, john_issue.id, john_comment_data)
