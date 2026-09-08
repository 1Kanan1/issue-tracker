from datetime import date, datetime

from pydantic import BaseModel

from app.enums import IssueStatus, Priority
from app.schemas.user import UserResponse


class IssueCreate(BaseModel):
    title: str
    description: str | None = None
    priority: Priority = Priority.LOW
    assignee_id: int | None = None
    due_date: date | None = None

class IssueUpdate(BaseModel): 
    title: str | None = None
    description: str | None = None
    status: IssueStatus | None = None
    priority: Priority | None = None
    assignee_id: int | None = None
    due_date: date | None = None

class IssueResponse(BaseModel):
    id: int
    title: str
    description: str | None
    status: IssueStatus
    priority: Priority
    project_id: int
    creator: UserResponse
    assignee: UserResponse | None
    due_date: date | None
    created_at: datetime
    updated_at: datetime
