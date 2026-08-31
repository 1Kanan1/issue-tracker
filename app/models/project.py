from __future__ import annotations  # avoids using quotes in type annotations

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.enums import ProjectStatus
from app.models.issue import Issue
from app.models.user import User

project_members = Table(
    "project_members",
    Base.metadata,
    Column("project_id", ForeignKey("projects.id"), primary_key=True),
    Column("user_id", ForeignKey("users.id"), primary_key=True),
)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(5000))
    status: Mapped[ProjectStatus] = mapped_column(default=ProjectStatus.ACTIVE)

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )  # to infer a relationship between User and Project; otherwise, the database won't bind them
    owner: Mapped[User] = relationship(
        back_populates="owned_projects"
    )  # uses User.projects

    issues: Mapped[list[Issue]] = relationship(back_populates="project")
    members: Mapped[list[User]] = relationship(
        secondary=project_members, back_populates="joined_projects"
    )
