from __future__ import annotations  # avoids using quotes in type annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.enums import IssueStatus, Priority

if TYPE_CHECKING:
    from app.models.comment import Comment
    from app.models.project import Project
    from app.models.user import User


class Issue(Base):
    __tablename__ = "issues"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String(5000), unique=False)
    status: Mapped[IssueStatus] = mapped_column(default=IssueStatus.OPEN)
    priority: Mapped[Priority] = mapped_column(default=Priority.LOW)

    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id"),
        nullable=False,
    )
    project: Mapped[Project] = relationship(
        foreign_keys=[project_id], back_populates="issues"
    )

    comments: Mapped[list[Comment]] = relationship(back_populates="issue")

    creator_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )
    creator: Mapped[User] = relationship(
        foreign_keys=[creator_id], back_populates="created_issues"
    )

    assignee_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )
    assignee: Mapped[User | None] = relationship(
        foreign_keys=[assignee_id], back_populates="assigned_issues"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    due_date: Mapped[date | None] = mapped_column(
        nullable=True,
    )
