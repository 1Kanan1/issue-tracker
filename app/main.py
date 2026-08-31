from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

from app.exceptions.user import UserNotFoundError
from app.routers import api

app = FastAPI()
app.include_router(api.router)


@app.exception_handler(UserNotFoundError)
async def user_not_found_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND, content={"detail": "User not found"}
    )
