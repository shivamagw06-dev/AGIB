"""FSE-02 collection subsystem — production façades."""

from __future__ import annotations

from typing import Any

from financial_statements_engine.collection.adapters.nse import discover_nse
from financial_statements_engine.collection.event_bus import get_bus
from financial_statements_engine.collection.pipeline import collect_from_discovery_rows
from financial_statements_engine.collection.schema import (
    ISSUES_RECOMMENDATIONS,
    PROGRAMME,
    RECOMMENDATION_POLICY,
    SUBSYSTEM,
    SUCCESS_TARGETS,
    VERSION,
    WORKSTREAM_ID,
)
from financial_statements_engine.collection.sources import sources_manifest
from financial_statements_engine.schema import GOLD_UNIVERSE
from financial_statements_engine.util import now_iso


def health() -> dict[str, Any]:
    bus = get_bus().stats()
    return {
        "status": "ok",
        "programme": PROGRAMME,
        "workstream_id": WORKSTREAM_ID,
        "subsystem": SUBSYSTEM,
        "version": VERSION,
        "role": "data_sources_collection_pipeline",
        "event_bus": bus,
        "sources": sources_manifest(),
        "success_targets": SUCCESS_TARGETS,
        "issues_recommendations": ISSUES_RECOMMENDATIONS,
        "recommendation_policy": RECOMMENDATION_POLICY,
        "parses_financials": False,
        "writes_warehouse": False,
        "spec": "docs/FSE_02_DATA_SOURCES_COLLECTION_PIPELINE.md",
        "as_of": now_iso(),
    }


def dashboard() -> dict[str, Any]:
    bus = get_bus().stats()
    return {
        "status": "ok",
        "workstream_id": WORKSTREAM_ID,
        "version": VERSION,
        "event_bus": bus,
        "recent_events": get_bus().tail(20),
        "success_targets": SUCCESS_TARGETS,
        "issues_recommendations": False,
        "as_of": now_iso(),
    }


def collect_ticker(
    ticker: str,
    *,
    mode: str = "live",
    rows: list[dict[str, Any]] | None = None,
    bytes_by_url: dict[str, bytes] | None = None,
) -> dict[str, Any]:
    t = ticker.upper().strip()
    discovery_rows = rows if rows is not None else discover_nse(t)
    result = collect_from_discovery_rows(t, discovery_rows, mode=mode, bytes_by_url=bytes_by_url)
    result.update(
        {
            "engine": "financial_statements_engine",
            "workstream_id": WORKSTREAM_ID,
            "version": VERSION,
            "recommendation_policy": RECOMMENDATION_POLICY,
            "issues_recommendations": False,
            "as_of": now_iso(),
        }
    )
    return result


def run_universe(universe: str = "gold", *, mode: str = "live") -> dict[str, Any]:
    tickers = list(GOLD_UNIVERSE) if universe in ("gold", "ic5") else list(GOLD_UNIVERSE)
    rows = [collect_ticker(t, mode=mode) for t in tickers]
    return {
        "ok": True,
        "workstream_id": WORKSTREAM_ID,
        "universe": universe,
        "mode": mode,
        "n": len(rows),
        "rows": rows,
        "issues_recommendations": False,
        "as_of": now_iso(),
    }


def recent_events(limit: int = 50) -> dict[str, Any]:
    return {
        "ok": True,
        "workstream_id": WORKSTREAM_ID,
        "events": get_bus().tail(limit),
        "issues_recommendations": False,
        "as_of": now_iso(),
    }
