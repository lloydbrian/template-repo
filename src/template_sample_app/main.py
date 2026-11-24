"""FastAPI application: a landing route and a health check."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI

from template_sample_app.config import load_env

load_env()

app = FastAPI(
    title=os.getenv("APP_TITLE") or "Sample App",
    version=os.getenv("APP_VERSION") or "0.1.0",
)


@app.get("/health", tags=["system"])
def health() -> dict[str, Any]:
    """Health check for container runtimes and load balancers."""
    return {
        "status": "ok",
        "service": app.title,
        "version": app.version,
        "timestamp_utc": datetime.now(UTC).isoformat(),
    }


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    """Landing route for a quick manual check."""
    return {"message": "Service is running. Try /health or /docs."}
