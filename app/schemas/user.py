from pydantic import BaseModel, EmailStr, Field, model_validator

from app.enums import Role


class User(BaseModel):
    username: str
    email: EmailStr


class UserCreate(User):
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Password must be between 8 and 128 characters"
    )

    @model_validator(mode="after")
    def password_not_username(self):
        if self.username.lower() in self.password.lower():
            raise ValueError("Password cannot contain your username")
        return self


class UserUpdate(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    password: str | None = None


class UserResponse(User):
    id: int
    role: Role
