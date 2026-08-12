"""Typed application settings loaded from the environment."""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/core/config.py -> backend/app -> backend -> repository root
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]

# Matching this value in production is treated as a configuration error, not a warning.
DEVELOPMENT_SECRET = "dev-secret-not-for-production"  # noqa: S105 - a sentinel, not a credential


class Environment(StrEnum):
    development = "development"
    test = "test"
    production = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: Environment = Environment.development
    database_url: str = "postgresql+psycopg://app:app@db:5432/app"
    secret_key: SecretStr = SecretStr(DEVELOPMENT_SECRET)
    questions_path: Path = REPOSITORY_ROOT / "questions.json"
    cors_origins: list[str] = ["http://localhost:5173"]
    log_level: str = "INFO"

    @property
    def is_production(self) -> bool:
        return self.environment is Environment.production

    @model_validator(mode="after")
    def reject_development_secret_in_production(self) -> Settings:
        if self.is_production and self.secret_key.get_secret_value() == DEVELOPMENT_SECRET:
            raise ValueError("SECRET_KEY must be set to a unique value when ENVIRONMENT=production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
