from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.enums import Role
from app.exceptions.base import ForbiddenError, NotFoundError
from app.models import Comment, Issue, Project, User
from app.schemas.comment import CommentCreate, CommentUpdate


class CommentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _verify_issue_access(self, current_user: User, issue_id: int):
        query = (
            select(Issue)
            .options(
                joinedload(Issue.project)
                .selectinload(Project.members)
            )
            .where(Issue.id == issue_id)
        )
        issue = (await self.db.execute(query)).scalar_one_or_none()

        if not issue:
            raise NotFoundError("Issue", issue_id)

        is_project_member = (
            current_user.id == issue.project.owner_id
            or any(m.id == current_user.id for m in issue.project.members)
        )

        if current_user.role != Role.ADMIN and not is_project_member:
            raise ForbiddenError("You do not have access to this project")

    async def create(self, current_user: User, issue_id: int, data: CommentCreate):
        await self._verify_issue_access(current_user, issue_id)

        new_comment = Comment(
            content=data.content,
            author_id=current_user.id,
            issue_id=issue_id
        )

        self.db.add(new_comment)
        await self.db.commit()
        await self.db.refresh(new_comment, ["author"])

        return new_comment

    async def list_for_issue(self, current_user: User, issue_id: int, skip: int = 0, limit: int = 20) -> list[Comment]:
        await self._verify_issue_access(current_user, issue_id)

        query = (
            select(Comment)
            .options(joinedload(Comment.author))
            .where(Comment.issue_id == issue_id)
            .order_by(Comment.created_at.asc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)

        return list(result.scalars().all())

    async def get_by_id(self, current_user: User, comment_id: int):
        query = (
            select(Comment)
            .options(
                joinedload(Comment.author),
                joinedload(Comment.issue).joinedload(Issue.project)
            )
            .where(Comment.id == comment_id)
        )

        result = await self.db.execute(query)
        comment = result.scalar_one_or_none()

        if comment is None:
            raise NotFoundError("Comment", comment_id)

        await self._verify_issue_access(current_user, comment.issue_id)

        return comment

    async def update(self, current_user: User, comment_id: int, data: CommentUpdate):
        comment = await self.get_by_id(current_user, comment_id)

        if current_user.role != Role.ADMIN and comment.author_id != current_user.id:
            raise ForbiddenError("Only the author or admin can edit this comment")

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(comment, field, value)

        await self.db.commit()
        await self.db.refresh(comment, ["author", "issue", "updated_at"])

        return comment

    async def delete(self, current_user: User, comment_id: int):
        comment = await self.get_by_id(current_user, comment_id)

        can_delete = (
            current_user.role == Role.ADMIN
            or comment.author_id == current_user.id
            or current_user.id == comment.issue.project.owner_id
        )
        if not can_delete:
            raise ForbiddenError("Only author, project owner, or admin can delete this comment")

        await self.db.delete(comment)
        await self.db.commit()
