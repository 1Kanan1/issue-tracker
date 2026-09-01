from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.exceptions.user import UserNotFoundError


async def user_not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND, content={"detail": "User not found"}
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(UserNotFoundError, user_not_found_handler)
