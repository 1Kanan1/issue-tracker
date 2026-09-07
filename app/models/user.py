from pydantic import EmailStr
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.enums import Role


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    email: Mapped[EmailStr] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[Role] = mapped_column(default=Role.MEMBER)
    is_disabled: Mapped[bool] = mapped_column(Boolean, default=False)

    owned_projects: Mapped[list["Project"]] = relationship( # noqa: F821 # ty: ignore[unresolved-reference]
        back_populates="owner"
    )  # uses Project.owner
    joined_projects: Mapped[list["Project"]] = relationship( # noqa: F821 # ty: ignore[unresolved-reference]
        secondary="project_members", back_populates="members"
    )

    created_issues: Mapped[list["Issue"]] = relationship( # noqa: F821 # ty: ignore[unresolved-reference]
        foreign_keys="Issue.creator_id", back_populates="creator"
    )
    assigned_issues: Mapped[list["Issue"]] = relationship( # noqa: F821 # ty: ignore[unresolved-reference]
        foreign_keys="Issue.assignee_id", back_populates="assignee"
    )

    comments: Mapped[list["Comment"]] = relationship(back_populates="author") # noqa: F821 # ty: ignore[unresolved-reference]
