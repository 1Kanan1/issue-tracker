import logging

from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import Role
from app.exceptions.user import (
    AuthenticationError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.models import User
from app.schemas.user import UserCreate, UserUpdate
from app.security import hash_password, verify_password

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def authenticate(self, username: str, password: str) -> User:
        user = await self.get_by_username(username)

        if (
            user is None
            or user.is_disabled
            or not verify_password(password, user.password_hash)
        ):
            raise AuthenticationError()

        logger.info("authenticate(id=%d, username=%s)", user.id, user.username)
        return user

    async def create(self, data: UserCreate, role: Role = Role.MEMBER) -> User:
        user = await self.get_by_username(data.username)
        email = await self.get_by_email(data.email)

        # To avoid race condition, keep statement conditions for user and email separately
        if user:
            raise UserAlreadyExistsError()
        
        if email:
            raise UserAlreadyExistsError()

        password_hash = hash_password(data.password)

        new_user = User(
            username=data.username,
            email=data.email,
            password_hash=password_hash,
            role=role,
        )

        self.db.add(new_user)
        await self.db.commit()  # Applies transaction to the database
        await self.db.refresh(
            new_user
        )  # Updates Python object using the latest data from database

        logger.info("create(id=%d, username=%s, email=%s, role=%s)", new_user.id, new_user.username, new_user.email, new_user.role)
        return new_user

    async def list(self, skip: int = 0, limit: int = 20) -> list[User]:
        result = await self.db.execute(select(User).offset(skip).limit(limit))

        return list(result.scalars().all())

    async def get_by_id(self, user_id: int) -> User:
        result = await self.db.execute(select(User).where(User.id == user_id))

        user = result.scalar_one_or_none()

        if user is None:
            logger.warning("User not found (id=%s)", user_id)
            raise UserNotFoundError()

        logger.debug("get_by_id(id=%s, username=%s)", user.id, user.username)
        return user

    # Used to check if the username exists
    async def get_by_username(self, username: str) -> User | None:
        result = await self.db.execute(select(User).where(User.username == username))

        # Avoid raising any exception for `UserService.create`
        return result.scalar_one_or_none()

    async def get_by_email(self, email: EmailStr) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))

        return result.scalar_one_or_none()

    async def update(self, user_id: int, data: UserUpdate) -> User:
        user = await self.get_by_id(user_id)

        update_data = data.model_dump(exclude_unset=True)

        if "password" in update_data:
            update_data["password_hash"] = hash_password(update_data.pop("password"))

        for field, value in update_data.items():
            setattr(user, field, value)

        await self.db.commit()  # Applies changes to the database
        await self.db.refresh(
            user
        )  # Updates Python object using the latest data from database

        logger.info("update(id=%d, fields=%s)", user.id, list(update_data.keys()))

        return user

    async def disable(self, user_id: int) -> None:
        user = await self.get_by_id(user_id)

        user.is_disabled = True

        await self.db.commit()
        await self.db.refresh(user)
        logger.info("disable(id=%d, username=%s)", user.id, user.username)

    async def delete(self, user_id: int) -> None:
        user = await self.get_by_id(user_id)
        username, email = user.username, user.email

        await self.db.delete(user)
        await self.db.commit()
        logger.info("delete(id=%s, username=%s, email=%s)", user_id, username, email)
