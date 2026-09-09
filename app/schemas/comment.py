from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.user import UserResponse


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)

class CommentUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)

class CommentResponse(BaseModel):
    id: int
    content: str
    author: UserResponse
    issue_id: int
    created_at: datetime
    updated_at: datetime
