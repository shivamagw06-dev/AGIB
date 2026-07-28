"""HIP service entrypoint — Historical Acquisition Platform (Sprint 8.1)."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.collectors.bse.historical import BSEHistoricalCollector
from app.collectors.company_ir.historical import CompanyIRHistoricalCollector
from app.collectors.nse.historical import NSEHistoricalCollector
from app.collectors.yahoo.historical import YahooHistoricalCollector
from app.config.settings import Settings, get_settings
from app.pipeline.orchestrator import HistoricalAcquisitionPipeline
from app.retrieval.gateway import HistoricalRetrievalGateway
from app.storage.db import HipStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("hip")


def build_collectors(settings: Settings) -> dict:
    symbols = list(settings.watchlist)
    live = settings.live_collectors_enabled
    collectors = [
        YahooHistoricalCollector(symbols=symbols, live=live),
        NSEHistoricalCollector(symbols=symbols, live=live),
        BSEHistoricalCollector(symbols=symbols, live=live),
        CompanyIRHistoricalCollector(symbols=symbols, live=live),
    ]
    return {c.collector_id: c for c in collectors}


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        store = HipStore(settings.db_path)
        pipeline = HistoricalAcquisitionPipeline(store)
        collectors = build_collectors(settings)
        gateway = HistoricalRetrievalGateway(store, settings)

        app.state.settings = settings
        app.state.store = store
        app.state.pipeline = pipeline
        app.state.collectors = collectors
        app.state.gateway = gateway

        logger.info(
            "HIP/HAP ready watchlist=%s live=%s",
            list(settings.watchlist),
            settings.live_collectors_enabled,
        )
        yield
        store.close()

    app = FastAPI(
        title="AGI Historical Intelligence Platform",
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
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=False)


if __name__ == "__main__":
    main()
