from fastapi import FastAPI

from app.exceptions.handlers import register_exception_handlers
from app.routers import api

app = FastAPI()
app.include_router(api.router)
register_exception_handlers(app)
