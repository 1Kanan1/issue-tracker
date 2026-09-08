from fastapi import APIRouter, status

from app.deps import CurrentUserDep, IssueServiceDep
from app.schemas.issue import IssueCreate, IssueResponse, IssueUpdate

router = APIRouter(tags=["issues"])


@router.post(
    "/projects/{project_id}/issues",
    status_code=status.HTTP_201_CREATED,
    response_model=IssueResponse
)
async def create_issue(project_id: int, current_user: CurrentUserDep, service: IssueServiceDep, data: IssueCreate):
    return await service.create(current_user, project_id, data)

@router.get("/projects/{project_id}/issues", response_model=list[IssueResponse])
async def list_issues(
    project_id: int,
    current_user: CurrentUserDep,
    service: IssueServiceDep,
    skip: int = 0,
    limit: int = 20,
):
    return await service.list_for_project(current_user, project_id, skip, limit)

@router.get("/issues/{issue_id}", response_model=IssueResponse)
async def get_issue(issue_id: int, current_user: CurrentUserDep, service: IssueServiceDep):
    return await service.get_by_id(current_user, issue_id)

@router.patch("/issues/{issue_id}", response_model=IssueResponse)
async def update_issue(
    issue_id: int,
    current_user: CurrentUserDep,
    service: IssueServiceDep,
    data: IssueUpdate
):
    return await service.update(current_user, issue_id, data)

@router.delete("/issues/{issue_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_issue(issue_id: int, current_user: CurrentUserDep, service: IssueServiceDep):
    return await service.delete(current_user, issue_id)
