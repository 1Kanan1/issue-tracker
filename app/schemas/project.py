from pydantic import BaseModel, Field

from app.enums import ProjectStatus
from app.schemas.user import UserResponse


class ProjectCreate(BaseModel):
    # Bound to the column width: raising these needs a migration.
    name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=5000)
    status: ProjectStatus = ProjectStatus.ACTIVE


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=5000)
    status: ProjectStatus | None = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str | None
    status: ProjectStatus
    owner: UserResponse
    members: list[UserResponse]
