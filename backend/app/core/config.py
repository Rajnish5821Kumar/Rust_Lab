"""Application settings loaded from environment variables.

Secrets (database password, JWT secret, tokens) are never given defaults here;
they must be supplied through the environment or a local, git-ignored `.env` file.
"""

import os
from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

RoleName = Literal["admin", "developer", "viewer"]
Environment = Literal["development", "test", "production"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # The repository-root .env is shared with Docker Compose; a backend/.env overrides it.
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "devvault"
    environment: Environment = "development"
    log_level: str = "INFO"
    log_json: bool = True

    database_url: str = Field(description="SQLAlchemy async URL, e.g. postgresql+asyncpg://...")
    database_echo: bool = False
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: SecretStr = Field(min_length=32)
    jwt_algorithm: Literal["HS256", "HS384", "HS512"] = "HS256"
    jwt_issuer: str = "devvault"
    access_token_expire_minutes: int = Field(default=15, ge=1, le=24 * 60)
    refresh_token_expire_days: int = Field(default=7, ge=1, le=90)

    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]
    default_user_role: RoleName = "viewer"
    bootstrap_admin_email: str | None = None

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("bootstrap_admin_email", mode="before")
    @classmethod
    def _normalize_email(cls, value: object) -> object:
        if isinstance(value, str):
            value = value.strip().lower()
            return value or None
        return value

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    # Tests must not pick up a developer's local .env file.
    if os.environ.get("ENVIRONMENT") == "test":
        return Settings(_env_file=None)
    return Settings()
