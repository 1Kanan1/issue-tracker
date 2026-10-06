import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.exc import IntegrityError

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db import SessionLocal
from app.enums import Role
from app.exceptions.base import AlreadyExistsError
from app.exceptions.handlers import register_exception_handlers
from app.routers import api
from app.schemas.user import UserCreate
from app.services.user import UserService

logger = logging.getLogger(__name__)


async def seed_admin() -> None:
    """Create the bootstrap admin from env on startup.

    An existing admin is left alone: editing ADMIN_PASSWORD afterwards will not
    rotate it. Delete the row to re-seed.
    """
    settings = get_settings()

    if not settings.admin_password:
        logger.info("admin seeding skipped: ADMIN_PASSWORD not set")
        return

    data = UserCreate(
        username=settings.admin_username,
        email=settings.admin_email,
        password=settings.admin_password,
    )

    async with SessionLocal() as db:
        try:
            await UserService(db).create(data, role=Role.ADMIN)
        except (AlreadyExistsError, IntegrityError):
            # AlreadyExistsError is the pre-check. IntegrityError is the race:
            # concurrent lifespans under --workers all pass the pre-check, and
            # only the losers fail on the unique index at commit.
            logger.info(
                "admin %r already exists, leaving password unchanged", data.username
            )
            return

    logger.info("seeded admin %r", data.username)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await seed_admin()
    yield


setup_logging()

app = FastAPI(lifespan=lifespan)
app.include_router(api.router)
register_exception_handlers(app)
