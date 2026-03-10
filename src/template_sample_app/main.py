# /src/template_sample_app/main.py
from __future__ import annotations

import os
from datetime import datetime

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(
    title=os.getenv("APP_TITLE", "Sample App"),
    version=os.getenv("APP_VERSION", "0.1.0"),
)


@app.get("/health", tags=["system"])
def health() -> JSONResponse:
    """Simple health check endpoint for docker / load balancers."""
    return JSONResponse(
        content={
            "status": "ok",
            "service": app.title,
            "version": app.version,
            "timestamp_utc": datetime.now(datetime.utc).isoformat(),
        },
        status_code=200,
    )


@app.get("/", tags=["system"])
def root() -> JSONResponse:
    """Root endpoint for testing. Basic landing point"""
    return JSONResponse(
        content={"message": "Service is running! Try /health for more info."},
        # docs= "/docs",
        # openapi="/openapi.json",
        status_code=200,
    )
