"""Internal HIP / HAP APIs — historical retrieval never hits external providers."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter()


def _state(request: Request):
    return request.app.state


@router.get("/healthz")
def healthz(request: Request) -> dict:
    settings = _state(request).settings
    return {"status": "ok", "service": settings.service_name, "version": settings.version}


@router.get("/readyz")
def readyz(request: Request) -> dict:
    store = _state(request).store
    return {
        "status": "ready",
        "raw_archive": store.count_raw(),
        "historical_objects": store.count_objects(),
    }


@router.get("/v1/historical/coverage/policy")
def coverage_policy(request: Request) -> dict:
    return _state(request).gateway.policy()


@router.get("/v1/historical/coverage/{symbol}")
def coverage(symbol: str, request: Request) -> dict:
    return _state(request).gateway.coverage(symbol)


@router.get("/v1/historical/company/{symbol}")
def company_history(symbol: str, request: Request) -> dict:
    return _state(request).gateway.company_history(symbol)


@router.get("/v1/historical/company/{symbol}/prices")
def company_prices(symbol: str, request: Request, period_kind: str = "daily") -> dict:
    rows = _state(request).store.list_prices(symbol, period_kind=period_kind)
    return {"company_symbol": symbol.upper(), "period_kind": period_kind, "items": rows, "providers_queried": []}


@router.get("/v1/historical/company/{symbol}/financials")
def company_financials(symbol: str, request: Request, period_kind: str | None = None) -> dict:
    rows = _state(request).store.list_financials(symbol, period_kind=period_kind)
    return {"company_symbol": symbol.upper(), "items": rows, "providers_queried": []}


@router.get("/v1/historical/company/{symbol}/revenue")
def company_revenue(
    symbol: str,
    request: Request,
    from_period: str = "FY2015",
    to_period: str = "FY2025",
) -> dict:
    """Success path: revenue growth + valuation across earnings cycles from store only."""
    return _state(request).gateway.revenue_growth(
        symbol, from_period=from_period, to_period=to_period
    )


@router.get("/v1/historical/company/{symbol}/events")
def company_events(symbol: str, request: Request) -> dict:
    return {
        "company_symbol": symbol.upper(),
        "items": _state(request).store.list_events(symbol),
        "providers_queried": [],
    }


@router.get("/v1/historical/company/{symbol}/actions")
def company_actions(symbol: str, request: Request) -> dict:
    return {
        "company_symbol": symbol.upper(),
        "items": _state(request).store.list_actions(symbol),
        "providers_queried": [],
    }


@router.get("/v1/historical/company/{symbol}/reports")
def company_reports(symbol: str, request: Request) -> dict:
    return {
        "company_symbol": symbol.upper(),
        "items": _state(request).store.list_reports(symbol),
        "providers_queried": [],
    }


@router.get("/v1/historical/company/{symbol}/entity")
def company_entity(symbol: str, request: Request) -> dict:
    entity = _state(request).store.get_entity(symbol)
    if not entity:
        raise HTTPException(status_code=404, detail="entity_not_found")
    return {"company_symbol": symbol.upper(), "entity": entity}


@router.get("/v1/internal/runs")
def list_runs(request: Request) -> dict:
    return {"runs": _state(request).store.list_runs()}


class BootstrapRequest(BaseModel):
    symbols: list[str] | None = None
    collectors: list[str] | None = None


@router.post("/v1/internal/bootstrap")
def bootstrap(request: Request, body: BootstrapRequest | None = None) -> dict:
    """Ops-only: bulk historical bootstrap. Never called by Ask."""
    payload = body or BootstrapRequest()
    state = _state(request)
    collectors = state.collectors
    if payload.collectors:
        collectors = {k: v for k, v in collectors.items() if k in payload.collectors}
    # Optionally narrow symbols by rebuilding collectors is out of scope —
    # Sprint 8.1 bootstraps the configured watchlist collectors.
    _ = payload.symbols
    summary = state.pipeline.bootstrap_all(collectors)
    return {
        "status": "ok",
        "summary": summary,
        "raw_archive": state.store.count_raw(),
        "historical_objects": state.store.count_objects(),
    }


@router.post("/v1/internal/run/{collector_id}")
def run_collector(collector_id: str, request: Request) -> dict:
    state = _state(request)
    collector = state.collectors.get(collector_id)
    if not collector:
        raise HTTPException(status_code=404, detail="collector_not_found")
    result = state.pipeline.run_collector(collector, mode="bootstrap")
    return {
        "collector_id": collector_id,
        "run_id": result.run_id,
        "accepted": len(result.accepted),
        "rejected": len(result.rejected),
        "duplicates": len(result.duplicates),
        "objects": len(result.objects),
    }
