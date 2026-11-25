"""FastAPI application: health endpoints, request IDs and structured access logs."""

from __future__ import annotations

import logging
import re
import time
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, Request, Response

from template_sample_app.config import Settings, get_settings
from template_sample_app.logging_config import configure_logging, request_id_var

log = logging.getLogger("template_sample_app.access")

# Accept caller-supplied IDs only if they are short and plain, so they are safe to log.
_SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def _request_id(header: str | None) -> str:
    if header and _SAFE_REQUEST_ID.fullmatch(header):
        return header
    return uuid.uuid4().hex


def create_app(settings: Settings | None = None) -> FastAPI:
    """Application factory: tests pass their own Settings; uvicorn uses `app` below."""
    settings = settings or get_settings()
    configure_logging(settings.log_level, settings.log_json)
    # Interactive API docs are for development; production does not advertise its full API surface.
    docs = settings.app_env != "prod"
    app = FastAPI(
        title=settings.app_title,
        version=settings.app_version,
        docs_url="/docs" if docs else None,
        redoc_url="/redoc" if docs else None,
        openapi_url="/openapi.json" if docs else None,
    )
    app.state.settings = settings

    @app.middleware("http")
    async def request_context(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        rid = _request_id(request.headers.get("x-request-id"))
        token = request_id_var.set(rid)
        started = time.perf_counter()
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = rid
            log.info(
                "request",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 1),
                },
            )
            return response
        finally:
            request_id_var.reset(token)

    @app.get("/health/live", tags=["system"])
    def live() -> dict[str, str]:
        """Liveness: the process is up. Never checks dependencies (avoids restart storms)."""
        return {"status": "ok"}

    @app.get("/health/ready", tags=["system"])
    def ready() -> dict[str, Any]:
        """Readiness: configuration loaded and dependencies reachable. Add checks here."""
        return {
            "status": "ready",
            "service": settings.app_title,
            "version": settings.app_version,
            "env": settings.app_env,
            "timestamp_utc": datetime.now(UTC).isoformat(),
        }

    @app.get("/", tags=["system"])
    def root() -> dict[str, str]:
        """Landing route for a quick manual check."""
        return {"message": "Service is running. See /health/ready or /docs."}

    return app


app = create_app()
