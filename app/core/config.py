import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    secret_key: str = "secret_key"
    access_token_expire_minutes: int = 30

    database_url: str = "postgresql+asyncpg://postgres@localhost:5432/issue_tracker"

    admin_username: str = ""
    admin_password: str = ""

    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", ".env"),
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
