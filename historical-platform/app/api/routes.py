"""Internal HIP / HAP / HKO APIs — historical retrieval never hits external providers."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.timeline.builder import TimelineBuilder

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
        "timeline_events": store.count_timeline_events(),
    }


# ----- Sprint 8.2 History / Timeline Intelligence -----


@router.get("/v1/history/company/{symbol}")
def history_company(symbol: str, request: Request) -> dict:
    return _state(request).gateway.company_history(symbol)


# Static timeline paths must precede /timeline/{symbol}
@router.get("/v1/history/timeline/sector/{sector}")
def history_sector_timeline(sector: str, request: Request) -> dict:
    return _state(request).gateway.sector_timeline(sector)


@router.get("/v1/history/timeline/market")
def history_market_timeline(request: Request) -> dict:
    return _state(request).gateway.market_timeline()


@router.get("/v1/history/timeline/macro")
def history_macro_timeline(request: Request) -> dict:
    return _state(request).gateway.macro_timeline()


@router.get("/v1/history/timeline/{symbol}")
def history_timeline(symbol: str, request: Request) -> dict:
    return _state(request).gateway.timeline(symbol)


@router.get("/v1/history/financials/{symbol}")
def history_financials(symbol: str, request: Request, period_kind: str | None = None) -> dict:
    return {
        "company_symbol": symbol.upper(),
        "items": _state(request).gateway.financials(symbol, period_kind=period_kind),
        "providers_queried": [],
    }


@router.get("/v1/history/events/{symbol}")
def history_events(symbol: str, request: Request) -> dict:
    return {
        "company_symbol": symbol.upper(),
        "items": _state(request).gateway.events(symbol),
        "providers_queried": [],
    }


class CompareRequest(BaseModel):
    symbol: str = Field(..., examples=["INFY"])
    as_of_period: str = Field(default="FY2018", examples=["FY2018"])
    include_current_tip: bool = True


@router.post("/v1/history/compare")
def history_compare(body: CompareRequest, request: Request) -> dict:
    return _state(request).gateway.compare(
        body.symbol,
        as_of_period=body.as_of_period,
        include_current_tip=body.include_current_tip,
    )


@router.get("/v1/history/mission-control")
def history_mission_control(request: Request) -> dict:
    return _state(request).gateway.mission_control()


# ----- Sprint 8.1 legacy historical paths -----


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
    rows = _state(request).gateway.financials(symbol, period_kind=period_kind)
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
        "items": _state(request).gateway.events(symbol),
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
    rebuild_timelines: bool = True


@router.post("/v1/internal/bootstrap")
def bootstrap(request: Request, body: BootstrapRequest | None = None) -> dict:
    """Ops-only: bulk historical bootstrap + timeline rebuild. Never called by Ask."""
    payload = body or BootstrapRequest()
    state = _state(request)
    collectors = state.collectors
    if payload.collectors:
        collectors = {k: v for k, v in collectors.items() if k in payload.collectors}
    symbols = payload.symbols or list(state.settings.watchlist)
    summary = state.pipeline.bootstrap_all(collectors, symbols=symbols)
    timelines = None
    if payload.rebuild_timelines:
        builder = TimelineBuilder(state.store)
        timelines = builder.rebuild_all(symbols)
    return {
        "status": "ok",
        "summary": summary,
        "timelines": timelines,
        "raw_archive": state.store.count_raw(),
        "historical_objects": state.store.count_objects(),
        "timeline_events": state.store.count_timeline_events(),
    }


@router.post("/v1/internal/timelines/rebuild")
def rebuild_timelines(request: Request, body: BootstrapRequest | None = None) -> dict:
    """Ops-only: regenerate company/sector/market/macro timelines from HKO + seeds."""
    state = _state(request)
    payload = body or BootstrapRequest()
    symbols = payload.symbols or list(state.settings.watchlist)
    out = TimelineBuilder(state.store).rebuild_all(symbols)
    return {"status": "ok", "timelines": out, "timeline_events": state.store.count_timeline_events()}


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
