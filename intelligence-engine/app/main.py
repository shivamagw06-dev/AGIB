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
    # Refuse silent ephemeral KIP in production (unless KIP_ALLOW_EPHEMERAL=1).
    from app.kip.persist import enforce_persistent_kip_or_raise

    persist_cfg = enforce_persistent_kip_or_raise(app_env=settings.app_env)
    if persist_cfg.get("warning"):
        log.warning(
            "kip_persistence_warning",
            extra={
                "durable": persist_cfg.get("durable"),
                "configured": persist_cfg.get("configured"),
                "kip_data_dir": persist_cfg.get("kip_data_dir"),
                "supabase_mirror": persist_cfg.get("supabase_mirror"),
                "warning": persist_cfg.get("warning"),
            },
        )
        # Also emit plain text so Render logs surface it immediately.
        print(persist_cfg["warning"], flush=True)
    else:
        log.info(
            "kip_persistence_ok",
            extra={
                "durable": True,
                "kip_data_dir": persist_cfg.get("kip_data_dir"),
                "supabase_mirror": persist_cfg.get("supabase_mirror"),
            },
        )

    bootstrap_registry()
    # Reload durable KIP snapshot (disk / optional Supabase) before serving traffic.
    try:
        from app.api.routes import _kip

        boot = _kip.reload_snapshot()
        log.info(
            "kip_snapshot_loaded",
            extra={
                "ok": boot.get("ok"),
                "loaded": boot.get("loaded"),
                "source": boot.get("source"),
                "documents": boot.get("documents"),
                "chunks": boot.get("chunks"),
            },
        )
    except Exception as exc:
        log.warning("kip_snapshot_load_failed", extra={"error": str(exc)[:160]})
    # Soft-seed Institutional Stack (FIL corpus + FDI/MII refresh) — never blocks startup
    try:
        if getattr(settings, "institutional_stack", True):
            from institutional_stack.production import bootstrap_stack

            boot = bootstrap_stack()
            log.info(
                "institutional_stack_bootstrapped",
                extra={
                    "ok": boot.get("ok"),
                    "documents": (boot.get("seed") or {}).get("document_count"),
                    "tickers": boot.get("tickers"),
                },
            )
    except Exception as exc:
        log.warning("institutional_stack_bootstrap_failed", extra={"error": str(exc)[:160]})
    # NOTE: Do not auto-download Chromium at startup on free-tier Render — the
    # install can starve CPU/RAM and make /v1/health time out. Bake browsers via
    # buildCommand (`python -m playwright install chromium`) or set
    # FAA_PLAYWRIGHT_AUTO_INSTALL=true only when disk/CPU budget allows.
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
