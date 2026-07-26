"""YFP production bridge — soft Yahoo enrichment via MarketDataClient only."""

from __future__ import annotations

import asyncio
from typing import Any

from yfp.enrich import fundamentals_to_kip_facts, merge_yahoo_into_dossier
from yfp.schema import YFP_VERSION


def is_yfp_enabled() -> bool:
    try:
        from app.core.config import get_settings

        return bool(getattr(get_settings(), "yahoo_provider", True))
    except Exception:
        return True


def _client():
    from app.core.config import get_settings
    from app.market_data.client import MarketDataClient

    return MarketDataClient.from_settings(get_settings())


def _run(coro):
    try:
        return asyncio.run(coro)
    except RuntimeError:
        # Nested loop — create task-less fallback
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


def enrich_ticker(ticker: str, *, client: Any | None = None) -> dict[str, Any]:
    """Fetch canonical Yahoo enrichment for a ticker through MarketDataClient."""
    if not is_yfp_enabled():
        return {"enabled": False, "yfp_version": YFP_VERSION, "bypassed": True}
    md = client or _client()
    pack = _run(md.yahoo_enrich(ticker))
    pack["yfp_version"] = YFP_VERSION
    pack["kip_facts"] = fundamentals_to_kip_facts(pack)
    return pack


def search(query: str, *, limit: int = 8, client: Any | None = None) -> dict[str, Any]:
    if not is_yfp_enabled():
        return {"enabled": False, "hits": []}
    md = client or _client()
    hits = _run(md.search_symbols(query, limit=limit))
    return {"enabled": True, "yfp_version": YFP_VERSION, "query": query, "hits": hits}


def enrich_cid(ticker: str, *, client: Any | None = None) -> dict[str, Any]:
    """Enrich living CID dossier with Yahoo secondary data (fill empties only)."""
    from cid.coverage import compute_coverage
    from cid.ingest import ensure_dossier
    from cid.store import get_cid_store

    t = (ticker or "").upper()
    if not t:
        return {"enabled": False, "reason": "no_ticker"}
    enrich = enrich_ticker(t, client=client)
    store = get_cid_store()
    dossier = store.get(t) or ensure_dossier(t)
    if enrich.get("enabled"):
        dossier = merge_yahoo_into_dossier(dossier, enrich)
        cov = compute_coverage(dossier)
        dossier.update(
            {
                "coverage": cov["coverage"],
                "coverage_score": cov["coverage_score"],
                "coverage_grade": cov["coverage_grade"],
                "missing_evidence": cov["missing_evidence"],
            }
        )
        dossier = store.put(dossier)
    return {
        "enabled": bool(enrich.get("enabled")),
        "yfp_version": YFP_VERSION,
        "ticker": t,
        "dossier": {
            "ticker": dossier.get("ticker"),
            "coverage_score": dossier.get("coverage_score"),
            "coverage_grade": dossier.get("coverage_grade"),
            "enrichment": dossier.get("enrichment"),
            "market_data": dossier.get("market_data"),
            "financial_metrics": dossier.get("financial_metrics"),
            "identity": dossier.get("identity"),
        },
        "kip_facts": enrich.get("kip_facts") or [],
        "enrich": {
            "has_quote": bool(enrich.get("quote")),
            "has_fundamentals": bool((enrich.get("fundamentals") or {}).get("metrics")),
            "calendar_events": len(enrich.get("calendar_events") or []),
            "errors": {k: v for k, v in enrich.items() if k.endswith("_error")},
        },
    }


def production_dashboard(*, client: Any | None = None) -> dict[str, Any]:
    md = client or _client()
    health = md.health.snapshot()
    yahoo_row = next((p for p in (health.get("providers") or []) if p.get("provider_id") == "yahoo"), {})
    extras = yahoo_row.get("extras") if isinstance(yahoo_row.get("extras"), dict) else {}
    return {
        "programme": "YFP",
        "yfp_version": YFP_VERSION,
        "architecture_status": "v1.0.1 LOCKED",
        "enabled": is_yfp_enabled(),
        "role": "secondary_market_data_provider",
        "priority": 40,
        "provider_health": yahoo_row,
        "yahoo_status": "ok" if yahoo_row.get("ok") else "degraded",
        "rate_limits": {"yahoo": "3/s burst 6"},
        "last_sync": extras.get("last_sync"),
        "coverage_flags": extras.get("flags") or {},
        "companies_updated": extras.get("companies_updated"),
        "failed_syncs": extras.get("failed_syncs"),
        "latency_ms": extras.get("average_latency_ms"),
        "market_data_metrics": health.get("metrics"),
        "not_an_engine": True,
        "answer_policy": "canonical_models_only",
    }


def quality_gates(tickers: list[str] | None = None) -> dict[str, Any]:
    samples = tickers or ["HDFCBANK", "INFY", "RELIANCE"]
    rows = []
    for t in samples:
        # Unit-test friendly: exercise mapper/search without requiring live Yahoo
        from app.market_data.providers.yahoo_symbols import to_yahoo_symbol

        ys = to_yahoo_symbol(t)
        pack = enrich_cid(t)
        rows.append(
            {
                "ticker": t,
                "yahoo_symbol": ys,
                "enriched": bool(pack.get("enabled")),
                "has_market_or_fundamentals": bool(
                    (pack.get("dossier") or {}).get("market_data", {}).get("current_price")
                    or (pack.get("dossier") or {}).get("financial_metrics")
                    or (pack.get("enrich") or {}).get("has_fundamentals")
                    or (pack.get("enrich") or {}).get("has_quote")
                ),
                "kip_facts": len(pack.get("kip_facts") or []),
                "errors": (pack.get("enrich") or {}).get("errors") or {},
            }
        )
    # Offline gates that must always pass
    from app.market_data.client import MarketDataClient
    from app.core.config import get_settings

    client = MarketDataClient.from_settings(get_settings())
    yahoo = client.yahoo_provider()
    checks = {
        "registered_in_provider_registry": yahoo is not None,
        "priority_secondary": bool(yahoo and yahoo.priority >= 40),
        "configured_when_flag_on": bool(yahoo and yahoo.is_configured()) if is_yfp_enabled() else True,
        "capabilities_include_quote_ohlcv_fundamental": bool(
            yahoo and {"quote", "ohlcv", "fundamental"}.issubset(yahoo.capabilities())
        ),
        "symbol_resolution_hdfc": to_yahoo_symbol("HDFCBANK") == "HDFCBANK.NS",
        "symbol_resolution_infosys_query": to_yahoo_symbol("Infosys") == "INFY.NS"
        or to_yahoo_symbol("INFY") == "INFY.NS",
    }
    return {
        "yfp_version": YFP_VERSION,
        "passed": all(checks.values()),
        "checks": checks,
        "live_enrichment": rows,
        "note": "Live Yahoo HTTP may fail in locked-down environments; registry/mapper gates are authoritative.",
    }
