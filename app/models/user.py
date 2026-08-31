from __future__ import annotations  # avoids using quotes in type annotations

from typing import TYPE_CHECKING

from pydantic import EmailStr
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.enums import Role

if TYPE_CHECKING:  # avoid runtime circular imports
    from app.models.comment import Comment
    from app.models.issue import Issue
    from app.models.project import Project


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    email: Mapped[EmailStr] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[Role] = mapped_column(default=Role.MEMBER)
    is_disabled: Mapped[bool] = mapped_column(Boolean, default=False)

    owned_projects: Mapped[list[Project]] = relationship(
        back_populates="owner"
    )  # uses Project.owner
    joined_projects: Mapped[list[Project]] = relationship(
        secondary="project_members", back_populates="members"
    )

    created_issues: Mapped[list[Issue]] = relationship(
        foreign_keys="Issue.creator_id", back_populates="creator"
    )
    assigned_issues: Mapped[list[Issue]] = relationship(
        foreign_keys="Issue.assignee_id", back_populates="assignee"
    )

    comments: Mapped[list[Comment]] = relationship(back_populates="author")
