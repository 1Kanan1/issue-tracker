from fastapi import APIRouter

from app.core.constants import API_VER
from app.routers import auth, issue, project, user

router = APIRouter(prefix=API_VER, tags=["api"])

router.include_router(user.router)
router.include_router(auth.router)
router.include_router(project.router)
router.include_router(issue.router)
