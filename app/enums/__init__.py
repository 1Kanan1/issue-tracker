from enum import StrEnum

from app.enums.priority import Priority
from app.enums.status import IssueStatus, ProjectStatus


class Role(StrEnum):
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"


__all__ = ["IssueStatus", "Priority", "ProjectStatus", "Role"]
