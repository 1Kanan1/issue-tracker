from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.exceptions.base import AlreadyExistsError, NotFoundError


async def not_found_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})

async def already_exists_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})

def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(NotFoundError, not_found_handler)
    app.add_exception_handler(AlreadyExistsError, already_exists_handler)
