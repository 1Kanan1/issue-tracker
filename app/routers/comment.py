from fastapi import APIRouter, status

from app.deps import CommentServiceDep, CurrentUserDep
from app.schemas.comment import CommentCreate, CommentResponse, CommentUpdate

router = APIRouter(tags=["comments"])

@router.post(
    "/issues/{issue_id}/comments",
    status_code=status.HTTP_201_CREATED,
    response_model=CommentResponse
)
async def create_comment(
    issue_id: int,
    current_user: CurrentUserDep,
    service: CommentServiceDep,
    data: CommentCreate
):
    return await service.create(current_user, issue_id, data)


@router.get("/issues/{issue_id}/comments", response_model=list[CommentResponse])
async def get_comments(
    issue_id: int,
    current_user: CurrentUserDep,
    service: CommentServiceDep,
    skip: int = 0,
    limit : int = 20
):
    return await service.list_for_issue(current_user, issue_id, skip, limit)


@router.patch(
    "/comments/{comment_id}",
    response_model=CommentResponse
)
async def update_comment(
    comment_id: int,
    current_user: CurrentUserDep,
    service: CommentServiceDep,
    data: CommentUpdate
):
    return await service.update(current_user, comment_id, data)


@router.delete(
    "/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_comment(
    comment_id: int,
    current_user: CurrentUserDep,
    service: CommentServiceDep,
):
    return await service.delete(current_user, comment_id)
