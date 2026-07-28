"""Internal KAIP APIs — Institutional Knowledge Objects only. No public endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.contracts.iko import company_knowledge_view
from app.contracts.models import KnowledgeObjectType, Source

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
    meta = profile.get("metadata") or {}
    source = Source(meta["source"]) if meta.get("source") in {s.value for s in Source} else Source.DERIVED
    view = company_knowledge_view(profile["knowledge"], source=source, version=int(profile["version"]))
    return {
        "object_type": "CompanyProfile",
        **profile,
        "company_knowledge": view.get("CompanyKnowledge"),
    }


@router.get("/v1/knowledge/company/{symbol}/versions")
def get_company_versions(symbol: str, request: Request) -> dict:
    versions = _app_state(request).store.list_versions(KnowledgeObjectType.COMPANY_PROFILE, symbol)
    return {"object_type": "CompanyProfile", "company_symbol": symbol.upper(), "versions": versions}


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


@router.get("/v1/knowledge/sector/{sector_key}")
def get_sector(sector_key: str, request: Request) -> dict:
    item = _app_state(request).store.get_sector_knowledge(sector_key)
    if not item:
        raise HTTPException(status_code=404, detail="sector_knowledge_not_found")
    return {"object_type": "SectorKnowledge", **item}


@router.get("/v1/knowledge/market-regime/{market_key}")
def get_market_knowledge(market_key: str, request: Request) -> dict:
    item = _app_state(request).store.get_market_knowledge(market_key)
    if not item:
        raise HTTPException(status_code=404, detail="market_knowledge_not_found")
    return {"object_type": "MarketKnowledge", **item}


@router.get("/v1/knowledge/relationships/{symbol}")
def get_relationships(symbol: str, request: Request) -> dict:
    edges = _app_state(request).store.list_relationships("Company", symbol.upper())
    entity = _app_state(request).store.get_entity(symbol)
    return {
        "company_symbol": symbol.upper(),
        "entity": entity.model_dump() if entity else None,
        "edges": edges,
    }


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
        "envelope": result.published.envelope.model_dump(mode="json") if result.published and result.published.envelope else None,
    }
