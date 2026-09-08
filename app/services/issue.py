from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.enums import Role
from app.exceptions.base import ForbiddenError, NotFoundError
from app.models import Issue, Project, User
from app.schemas.issue import IssueCreate, IssueUpdate


class IssueService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, current_user: User, project_id: int, data: IssueCreate):
        query = (
            select(Project)
            .options(selectinload(Project.members))
            .where(Project.id == project_id)
        )
        project = (await self.db.execute(query)).scalar_one_or_none()

        if not project:
            raise NotFoundError("Project", project_id)

        is_member_or_owner = (
            current_user.id == project.owner_id
            or any(m.id == current_user.id for m in project.members)
        )

        if current_user.role != Role.ADMIN and not is_member_or_owner:
            raise ForbiddenError("You are not a member of this project")

        if data.assignee_id:
            valid_assignee = (
                data.assignee_id == project.owner_id
                or any(m.id == data.assignee_id for m in project.members)
            )
            if not valid_assignee:
                raise ForbiddenError("Assignee must be a member or owner of the project")

        new_issue = Issue(
            title=data.title,
            description=data.description,
            priority=data.priority,
            assignee_id=data.assignee_id,
            due_date=data.due_date,
            creator_id=current_user.id,
            project_id=project_id
        )

        self.db.add(new_issue)
        await self.db.commit()
        await self.db.refresh(new_issue, ["creator", "assignee"])

        return new_issue


    async def get_by_id(self, current_user: User, issue_id: int) -> Issue:
        query = (
            select(Issue)
            .options(
                joinedload(Issue.creator),
                joinedload(Issue.assignee),
                joinedload(Issue.project).selectinload(Project.members),
            )
            .where(Issue.id == issue_id)
        )
        issue = (await self.db.execute(query)).scalar_one_or_none()
        if not issue:
            raise NotFoundError("Issue", issue_id)

        # Admins bypass, but everyone else must be project owner or member
        is_project_member = (
            current_user.id == issue.project.owner_id
            or any(m.id == current_user.id for m in issue.project.members)
        )
        if current_user.role != Role.ADMIN and not is_project_member:
            raise ForbiddenError("You do not have access to this project's issues")

        return issue

    async def list_for_project(self, current_user: User, project_id: int, skip=0, limit=20):
        query = (
            select(Project)
            .options(selectinload(Project.members))
            .where(Project.id == project_id)
        )
        project = (await self.db.execute(query)).scalar_one_or_none()

        if not project:
            raise NotFoundError("Project", project_id)

        is_member_or_owner = (
            current_user.id == project.owner_id
            or any(m.id == current_user.id for m in project.members)
        )

        if current_user.role != Role.ADMIN and not is_member_or_owner:
            raise ForbiddenError("You are not a member of this project")

        query = (
            select(Issue)
            .options(
                joinedload(Issue.creator),
                joinedload(Issue.assignee)
            )
            .where(Issue.project_id == project_id)
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)

        return list(result.scalars().all())

    async def update(self, current_user: User, issue_id: int, data: IssueUpdate):
        issue = await self.get_by_id(current_user, issue_id)

        can_update = (
            current_user.role == Role.ADMIN
            or current_user.id == issue.project.owner_id
            or current_user.id == issue.creator_id
            or current_user.id == issue.assignee_id
        )
        if not can_update:
            raise ForbiddenError("Not authorized to update this issue")

        update_data = data.model_dump(exclude_unset=True)

        if update_data.get("assignee_id") is not None:
            valid_assignee = (
                update_data["assignee_id"] == issue.project.owner_id
                or any(m.id == update_data["assignee_id"] for m in issue.project.members)
            )
            if not valid_assignee:
                raise ForbiddenError("Assignee must be a member or owner of the project")

        for field, value in update_data.items():
            setattr(issue, field, value)

        await self.db.commit()
        await self.db.refresh(issue, ["creator", "assignee", "updated_at", "created_at"])

        return issue

    async def delete(self, current_user: User, issue_id: int) -> None:
        issue = await self.get_by_id(current_user, issue_id)

        can_delete = (
            current_user.role == Role.ADMIN
            or current_user.id == issue.project.owner_id
            or current_user.id == issue.creator_id
        )
        if not can_delete:
            raise ForbiddenError("Only issue creator, project owner, or admin can delete issue")

        await self.db.delete(issue)
        await self.db.commit()
