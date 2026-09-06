from pydantic import BaseModel

from app.enums import ProjectStatus
from app.schemas.user import UserResponse


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    status: ProjectStatus = ProjectStatus.ACTIVE

class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: ProjectStatus | None = None

class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    status: ProjectStatus
    owner: UserResponse
    members: list[UserResponse]
