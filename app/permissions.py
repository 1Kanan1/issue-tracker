from enum import StrEnum

from fastapi import HTTPException, status

from app.deps import CurrentUserDep
from app.enums import Role
from app.models import User


class Permission(StrEnum):
    USER_DELETE = "user:delete"
    PROJECT_CREATE = "project:create"
    PROJECT_UPDATE = "project:update"
    PROJECT_DELETE = "project:delete"
    ISSUE_CREATE = "issue:create"
    ISSUE_UPDATE = "issue:update"
    ISSUE_DELETE = "issue:delete"
    COMMENT_CREATE = "comment:create"
    COMMENT_DELETE = "comment:delete"


ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.ADMIN: frozenset({*Permission}),
    Role.MANAGER: frozenset(
        {
            Permission.PROJECT_CREATE,
            Permission.PROJECT_UPDATE,
            Permission.PROJECT_DELETE,
            Permission.ISSUE_CREATE,
            Permission.ISSUE_UPDATE,
            Permission.ISSUE_DELETE,
            Permission.COMMENT_CREATE,
            Permission.COMMENT_DELETE,
        }
    ),
    Role.MEMBER: frozenset(
        {
            Permission.ISSUE_CREATE,
            Permission.ISSUE_UPDATE,
            Permission.COMMENT_CREATE,
        }
    ),
}


def has_permission(user: User, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS[user.role]


def require_permission(permission: Permission):
    async def dependency(current_user: CurrentUserDep) -> User:
        if not has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )

        return current_user

    return dependency
