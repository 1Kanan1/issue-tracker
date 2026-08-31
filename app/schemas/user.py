from pydantic import BaseModel, EmailStr

from app.enums import Role


class User(BaseModel):
    username: str
    email: EmailStr


class UserCreate(User):
    password: str


class UserUpdate(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    password: str | None = None


class UserResponse(User):
    id: int
    role: Role
