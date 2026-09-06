import logging

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.enums import Role
from app.exceptions.base import AlreadyExistsError, ForbiddenError, NotFoundError
from app.models import Project, User
from app.schemas.project import ProjectCreate, ProjectUpdate

logger = logging.getLogger(__name__)

class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, owner_id: int, data: ProjectCreate) -> Project:
        project = await self.get_by_name(data.name)

        if project:
            raise AlreadyExistsError("Project", project.id)

        new_project = Project(
            name=data.name,
            description=data.description,
            status=data.status,
            owner_id=owner_id
        )


        self.db.add(new_project)
        await self.db.commit()
        await self.db.refresh(new_project, ["owner", "members"])

        return new_project

    async def get_by_id(self, user: User, project_id: int) -> Project:
        query = select(Project).options(
            joinedload(Project.owner),
            selectinload(Project.members)
        )

        result = await self.db.execute(query.where(Project.id == project_id))

        project = result.scalar_one_or_none()

        if project is None:
            logger.warning("Project not found (id=%s)", project_id)
            raise NotFoundError("Project", project_id)

        if not (
            user.role == Role.ADMIN
            or project.owner_id == user.id
            or any(m.id == user.id for m in project.members)
        ):
            raise ForbiddenError("You do not have access to this project")

        logger.debug("get_by_id(id=%s, owner=%s)", project.id, project.owner.username)
        return project

    async def get_by_name(self, project_name) -> Project | None:
        result = await self.db.execute(
            select(Project).where(Project.name == project_name)
        )
        return result.scalar_one_or_none()

    async def list_for_user(self, user: User, skip: int = 0, limit: int = 20) -> list[Project]:
        query = select(Project).options(
            joinedload(Project.owner),      # loads 1-to-1 owner
            selectinload(Project.members)   # loads M2M members
        ) # prevents N+1 problem

        if user.role != Role.ADMIN:
            query = query.where(
                or_(
                    Project.owner_id == user.id,
                    Project.members.any(User.id == user.id) # EXISTS subquery
                )
            )

        query = query.offset(skip).limit(limit)
        projects = await self.db.execute(query)
        return list(projects.scalars().all())

    async def update(self, current_user: User, project_id: int, data: ProjectUpdate):
        project = await self.get_by_id(current_user, project_id)

        if current_user.role != Role.ADMIN and project.owner_id != current_user.id:
            raise ForbiddenError("Only project owner or admin can update project details")

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(project, field, value)

        await self.db.commit()
        await self.db.refresh(project, ["owner", "members"])

        logger.info("update(id=%d, fields=%s)", current_user.id, list(update_data.keys()))

        return project

    async def add_member(self, current_user: User, project_id: int, user_id: int) -> Project:
        project = await self.get_by_id(current_user, project_id)

        if current_user.role != Role.ADMIN and project.owner_id != current_user.id:
            raise ForbiddenError("Only project owner or admin can manage members")

        if user_id == project.owner_id:
            raise AlreadyExistsError("ProjectOwner", user_id)

        user = await self.db.get(User, user_id)
        if not user:
            raise NotFoundError("User", user_id)

        if user not in project.members:
            project.members.append(user)
            await self.db.commit()

        return project

    async def remove_member(self, current_user: User, project_id: int, user_id: int) -> Project:
        project = await self.get_by_id(current_user, project_id)

        if not (
            current_user.role == Role.ADMIN
            or project.owner_id == current_user.id
            or current_user.id == user_id
        ):
            raise ForbiddenError("You cannot remove members from this project")

        if user_id == project.owner_id:
            raise ForbiddenError("Project owner cannot be removed")
        
        user = await self.db.get(User, user_id)
        if not user:
            raise NotFoundError("User", user_id)

        if user in project.members:
            project.members.remove(user)
            await self.db.commit()

        return project
