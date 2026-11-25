"""Typed application settings, validated once at startup (fail fast).

Sources, highest priority first: real environment variables, then `.env.<APP_ENV>` if that
file exists. Production values come from the secret store / `podman secret`, never a file.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["dev", "test", "prod"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR"]


class Settings(BaseSettings):
    """Every setting the service reads. Unknown variables are ignored; invalid ones fail."""

    # env_ignore_empty: a blank value such as `APP_TITLE=` (common in older .env files) counts as
    # unset, so the default applies. min_length still rejects an empty string passed in code.
    model_config = SettingsConfigDict(extra="ignore", frozen=True, env_ignore_empty=True)

    app_env: Environment = "dev"
    app_title: str = Field(default="Template Sample App", min_length=1)
    app_version: str = Field(default="0.1.0", min_length=1)
    log_level: LogLevel = "INFO"
    log_json: bool = True
    http_port: int = Field(default=8000, ge=1024, le=65535)


def _env_file() -> Path | None:
    path = Path(f".env.{os.environ.get('APP_ENV', 'dev')}")
    return path if path.is_file() else None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load and validate settings once; raises pydantic.ValidationError on bad values."""
    return Settings(_env_file=_env_file())
