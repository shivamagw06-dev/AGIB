"""KAIP service entrypoint — Knowledge Acquisition Platform (Sprint 6.1)."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from app.api.routes import router
from app.collectors.bse.corporate_actions import BSECorporateActionCollector
from app.collectors.company_ir.collector import CompanyIRCollector
from app.collectors.nse.announcements import NSEAnnouncementCollector
from app.collectors.nse.bhavcopy import NSEBhavcopyCollector
from app.collectors.yahoo.collector import YahooCollector
from app.config.settings import Settings, get_settings
from app.metrics.metrics import METRICS
from app.pipeline.orchestrator import AcquisitionPipeline
from app.scheduler.scheduler import AcquisitionScheduler
from app.storage.db import KaipStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("kaip")


def build_collectors(settings: Settings) -> dict[str, Any]:
    symbols = list(settings.watchlist)
    live = settings.live_collectors_enabled
    collectors = [
        YahooCollector(symbols=symbols, interval_seconds=settings.yahoo_interval_seconds, live=live),
        NSEAnnouncementCollector(
            symbols=symbols,
            interval_seconds=settings.nse_announcement_interval_seconds,
            live=live,
        ),
        NSEBhavcopyCollector(
            symbols=symbols,
            interval_seconds=settings.nse_bhavcopy_interval_seconds,
            live=live,
        ),
        BSECorporateActionCollector(
            symbols=symbols,
            interval_seconds=settings.bse_corporate_action_interval_seconds,
            live=live,
        ),
        CompanyIRCollector(
            symbols=symbols,
            interval_seconds=settings.company_ir_interval_seconds,
            live=live,
        ),
    ]
    return {c.collector_id: c for c in collectors}


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        store = KaipStore(settings.db_path)
        pipeline = AcquisitionPipeline(store, settings)
        collectors = build_collectors(settings)
        scheduler = AcquisitionScheduler()

        def make_runner(collector_id: str):
            def _run() -> None:
                collector = collectors[collector_id]
                result = pipeline.run_collector(collector)
                METRICS.record_run(
                    collector_id,
                    accepted=len(result.accepted),
                    rejected=len(result.rejected),
                    duplicates=len(result.duplicates),
                    published=len(result.knowledge_objects),
                    learning=len(result.learning_events),
                )

            return _run

        for collector in collectors.values():
            scheduler.register(collector, make_runner(collector.collector_id))

        app.state.settings = settings
        app.state.store = store
        app.state.pipeline = pipeline
        app.state.collectors = collectors
        app.state.scheduler = scheduler

        if settings.scheduler_enabled:
            scheduler.start()
            logger.info("KAIP scheduler started watchlist=%s", list(settings.watchlist))
        yield
        scheduler.stop()
        store.close()

    app = FastAPI(
        title="AGI Knowledge Acquisition Platform",
        version=settings.version,
        docs_url="/internal/docs",
        redoc_url=None,
        openapi_url="/internal/openapi.json",
        lifespan=lifespan,
    )
    app.include_router(router)
    return app


app = create_app()


def main() -> None:
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
