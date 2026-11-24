"""Environment loading: .env.<APP_ENV> locally; real environment variables always win."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


def load_env() -> str:
    """Load .env.<APP_ENV> if it exists and return the active environment name."""
    env = os.environ.get("APP_ENV", "dev")
    path = Path(f".env.{env}")
    if path.exists():
        load_dotenv(path, override=False)
    return env
