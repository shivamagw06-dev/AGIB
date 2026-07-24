"""AGI Intelligence Engine — FastAPI multi-agent research service."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.agents.registry import bootstrap_registry

configure_logging()
log = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    bootstrap_registry()
    log.info(
        "intelligence_engine_started",
        extra={"env": settings.app_env, "agib_base": settings.agib_api_base_url},
    )
    yield
    log.info("intelligence_engine_stopped")


app = FastAPI(
    title="AGI Intelligence Engine",
    version="0.1.0",
    description="Multi-agent institutional research engine for Agarwal Global Investments.",
    lifespan=lifespan,
)
app.include_router(router)


@app.get("/")
async def root():
    return {
        "service": "agi-intelligence-engine",
        "status": "running",
        "docs": "/docs",
    }
