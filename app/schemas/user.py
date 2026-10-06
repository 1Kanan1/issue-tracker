from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, model_validator

from app.enums import Role
from app.exceptions.base import ValidationError

Password = Annotated[
    str,
    Field(
        min_length=8,
        max_length=128,
        description="Password must be between 8 and 128 characters",
    ),
]


def password_contains_username(username: str, password: str) -> bool:
    return username.lower() in password.lower()


def reject_username_in_password(username: str, password: str) -> None:
    """Raises ValidationError rather than ValueError: callers are services, not
    Pydantic. The model validators below use ValueError so it lands in the
    standard 422 body."""
    if password_contains_username(username, password):
        raise ValidationError("Password cannot contain your username")


class User(BaseModel):
    username: str
    email: EmailStr


class UserCreate(User):
    password: Password

    @model_validator(mode="after")
    def password_not_username(self):
        if password_contains_username(self.username, self.password):
            raise ValueError("Password cannot contain your username")
        return self


class UserUpdate(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    password: Password | None = None

    @model_validator(mode="after")
    def password_not_username(self):
        # Password-only updates are checked in UserService, which can see the stored username.
        if (
            self.username
            and self.password
            and password_contains_username(self.username, self.password)
        ):
            raise ValueError("Password cannot contain your username")
        return self


class UserResponse(User):
    id: int
    role: Role
