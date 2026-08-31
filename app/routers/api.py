from fastapi import APIRouter

from app.routers import auth, user

router = APIRouter(prefix="/api/v1", tags=["api"])

router.include_router(user.router)
router.include_router(auth.router)
