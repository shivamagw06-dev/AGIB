"""Internal KAIP APIs — Knowledge Objects only. No public endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

router = APIRouter()


def _app_state(request: Request):
    return request.app.state


@router.get("/healthz")
def healthz(request: Request) -> dict:
    settings = _app_state(request).settings
    return {"status": "ok", "service": settings.service_name, "version": settings.version}


@router.get("/readyz")
def readyz(request: Request) -> dict:
    store = _app_state(request).store
    return {
        "status": "ready",
        "raw_events": store.count_raw_events(),
        "published_knowledge_objects": store.count_published_kos(),
    }


@router.get("/v1/knowledge/company/{symbol}")
def get_company(symbol: str, request: Request) -> dict:
    profile = _app_state(request).store.get_company_profile(symbol)
    if not profile:
        raise HTTPException(status_code=404, detail="company_profile_not_found")
    return {"object_type": "CompanyProfile", **profile}


@router.get("/v1/knowledge/market/{symbol}")
def get_market(symbol: str, request: Request) -> dict:
    snap = _app_state(request).store.get_latest_market(symbol)
    if not snap:
        raise HTTPException(status_code=404, detail="market_snapshot_not_found")
    return {"object_type": "MarketSnapshot", **snap}


@router.get("/v1/knowledge/events/{symbol}")
def get_events(symbol: str, request: Request) -> dict:
    events = _app_state(request).store.list_events(symbol)
    return {"object_type": "CorporateEvent", "company_symbol": symbol.upper(), "items": events}


@router.get("/v1/knowledge/financials/{symbol}")
def get_financials(symbol: str, request: Request) -> dict:
    items = _app_state(request).store.list_financials(symbol)
    return {"object_type": "FinancialStatement", "company_symbol": symbol.upper(), "items": items}


@router.get("/v1/knowledge/learning/{symbol}")
def get_learning(symbol: str, request: Request) -> dict:
    items = _app_state(request).store.list_learning(symbol)
    return {"company_symbol": symbol.upper(), "items": items}


@router.get("/v1/internal/jobs")
def list_jobs(request: Request) -> dict:
    scheduler = _app_state(request).scheduler
    return {"jobs": scheduler.list_jobs() if scheduler else []}


@router.get("/v1/internal/metrics")
def metrics(request: Request) -> dict:
    from app.metrics.metrics import METRICS

    return METRICS.snapshot()


@router.post("/v1/internal/run/{collector_id}")
def run_collector(collector_id: str, request: Request) -> dict:
    """Ops-only: run one registered collector immediately."""
    state = _app_state(request)
    collectors = state.collectors
    collector = collectors.get(collector_id)
    if not collector:
        raise HTTPException(status_code=404, detail="collector_not_found")
    result = state.pipeline.run_collector(collector)
    from app.metrics.metrics import METRICS

    METRICS.record_run(
        collector_id,
        accepted=len(result.accepted),
        rejected=len(result.rejected),
        duplicates=len(result.duplicates),
        published=len(result.knowledge_objects),
        learning=len(result.learning_events),
    )
    return {
        "collector_id": collector_id,
        "accepted": len(result.accepted),
        "rejected": len(result.rejected),
        "duplicates": len(result.duplicates),
        "published_objects": len(result.knowledge_objects),
        "learning_events": len(result.learning_events),
    }
