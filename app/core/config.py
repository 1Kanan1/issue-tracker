import os
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    secret_key: str
    access_token_expire_minutes: int = 30

    database_url: str = "postgresql+asyncpg://postgres@localhost:5432/issue_tracker"

    admin_username: str = ""
    admin_password: str = ""

    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", ".env"), extra="ignore"
    )

    @field_validator("secret_key")
    @classmethod
    def long_enough(cls, v: str) -> str:
        # No default on purpose: a missing key is a required-field error, and the
        # old "secret_key" literal was 10 bytes, so the length check catches it too.
        if len(v.encode()) < 32:
            raise ValueError("SECRET_KEY must be at least 32 bytes (RFC 7518 3.2)")
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
