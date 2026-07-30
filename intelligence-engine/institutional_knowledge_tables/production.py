"""Production façades for Institutional Knowledge Tables (IKT)."""

from __future__ import annotations

from typing import Any

from institutional_knowledge_tables.schema import IKT_SPEC, IKT_VERSION, IKT_WORKSTREAM_ID, TABLE_DEFS
from institutional_knowledge_tables.store import (
    company_record,
    get_field_history,
    get_table,
    list_companies,
    upsert_fact,
)
from institutional_knowledge_tables.sync import (
    sync_company_master,
    sync_knowledge_metadata,
    sync_universe_company_master,
)


def health() -> dict[str, Any]:
    companies = list_companies()
    return {
        "ok": True,
        "workstream_id": IKT_WORKSTREAM_ID,
        "version": IKT_VERSION,
        "spec": IKT_SPEC,
        "table_count": len(TABLE_DEFS),
        "companies_with_facts": len(companies),
        "mission": (
            "Documents are evidence; these tables are the memory. Never fabricate — "
            "missing fields stay NULL with lineage to the source that would fill them."
        ),
    }


def tables_catalog() -> dict[str, Any]:
    return {
        "ok": True,
        "version": IKT_VERSION,
        "tables": [
            {
                "table": name,
                "label": meta.get("label"),
                "fields": list(meta.get("fields") or []),
                "keyed_by_period": bool(meta.get("keyed_by_period")),
            }
            for name, meta in TABLE_DEFS.items()
        ],
    }


def get_company_tables(ticker: str) -> dict[str, Any]:
    return company_record(ticker)


def get_company_table(ticker: str, table: str, *, period: str | None = None) -> dict[str, Any]:
    return get_table(ticker, table, period=period)


def get_field_timeline(ticker: str, table: str, field: str, *, period: str | None = None) -> dict[str, Any]:
    history = get_field_history(ticker, table, field, period=period)
    return {
        "ok": True,
        "ticker": str(ticker or "").upper(),
        "table": table,
        "field": field,
        "period": period,
        "history": history,
        "version_count": len(history),
    }


def record_fact(
    ticker: str,
    table: str,
    field: str,
    value: Any,
    *,
    source: str,
    effective_date: str | None = None,
    period: str | None = None,
    trigger: str = "manual",
) -> dict[str, Any]:
    """Admin / collector write path — always requires an evidence source."""
    return upsert_fact(
        ticker,
        table,
        field,
        value,
        source=source,
        effective_date=effective_date,
        period=period,
        trigger=trigger,
    )


def soft_slice_for_ask_agi(question: str = "", payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Metadata only — Ask AGI should read structured tables, not raw PDFs."""
    _ = question
    ticker = (payload or {}).get("ticker")
    if not ticker:
        return {"institutional_knowledge_tables": {"enabled": True, "table_count": len(TABLE_DEFS)}}
    rec = company_record(ticker)
    return {
        "institutional_knowledge_tables": {
            "enabled": True,
            "ticker": rec.get("ticker"),
            "populated_tables": rec.get("populated_tables"),
            "coverage_of_24": f"{len(rec.get('populated_tables') or [])}/{len(TABLE_DEFS)}",
        }
    }


def rebuild_company_tables(ticker: str) -> dict[str, Any]:
    """Ops action — refresh company_master (real) + knowledge_metadata (soft) for one ticker."""
    master = sync_company_master(ticker)
    metadata = sync_knowledge_metadata(ticker)
    return {"ok": bool(master.get("ok")), "ticker": str(ticker or "").upper(), "master": master, "metadata": metadata}


def onboard_universe(*, scope: str = "nifty500", limit: int | None = None) -> dict[str, Any]:
    """Onboard every company in the uploaded universe file into IKT company_master."""
    return sync_universe_company_master(scope=scope, limit=limit)


__all__ = [
    "get_company_table",
    "get_company_tables",
    "get_field_timeline",
    "health",
    "onboard_universe",
    "rebuild_company_tables",
    "record_fact",
    "soft_slice_for_ask_agi",
    "tables_catalog",
]
