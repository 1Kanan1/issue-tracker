from fastapi import APIRouter, Depends, status

from app.deps import CurrentUserDep, ProjectServiceDep
from app.permissions import Permission, require_permission
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
        service: ProjectServiceDep,
        current_user: CurrentUserDep,
        skip: int = 0,
        limit: int = 20
):
    return await service.list_for_user(current_user, skip, limit)

@router.post(
    "",
    dependencies=[Depends(require_permission(Permission.PROJECT_CREATE))],
    status_code=status.HTTP_201_CREATED,
    response_model=ProjectResponse
)
async def create_project(data: ProjectCreate, current_user: CurrentUserDep, service: ProjectServiceDep):
    return await service.create(current_user.id, data)

@router.get(
    "/{project_id}",
    response_model=ProjectResponse
)
async def get_project(project_id: int, current_user: CurrentUserDep, service: ProjectServiceDep):
    return await service.get_by_id(current_user, project_id)


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse
)
async def update_project(
    data: ProjectUpdate,
    project_id: int,
    current_user: CurrentUserDep,
    service: ProjectServiceDep
):
    return await service.update(current_user, project_id, data)


@router.post("/{project_id}/members/{user_id}", response_model=ProjectResponse)
async def add_project_member(
    project_id: int,
    user_id: int,
    current_user: CurrentUserDep,
    service: ProjectServiceDep,
):
    return await service.add_member(current_user, project_id, user_id)


@router.delete("/{project_id}/members/{user_id}", response_model=ProjectResponse)
async def remove_project_member(
    project_id: int,
    user_id: int,
    current_user: CurrentUserDep,
    service: ProjectServiceDep,
):
    return await service.remove_member(current_user, project_id, user_id)
