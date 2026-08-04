"""Warehouse-persisted HVIE universe queue — never in-memory-only."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any, Optional

from historical_valuation_intelligence.models import ENGINE_CODE
from historical_valuation_intelligence.universe_programme.models import (
    LIFE_NOT_STARTED,
    LIFE_READY,
    PROGRAMME_CODE,
    QUEUE_COMPLETED,
    QUEUE_FAILED,
    QUEUE_PENDING,
    QUEUE_RETRY,
    QUEUE_RUNNING,
    QUEUE_SKIPPED,
    STAGE_CLASSIFY,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _paged_rows(tab_id: str, *, max_rows: int = 100_000) -> list[dict[str, Any]]:
    from institutional_warehouse import store

    page_size = 5000
    offset = 0
    out: list[dict[str, Any]] = []
    while offset < max_rows:
        try:
            page = store.fetch(tab_id, limit=page_size, offset=offset)
        except Exception:
            break
        rows = page.get("rows") or []
        if not rows:
            break
        out.extend(rows)
        total = int(page.get("total") or 0)
        offset += len(rows)
        if offset >= total or len(rows) < page_size:
            break
    return out


def _clean(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    for k in list(out.keys()):
        if str(k).startswith("sys_") or k in {"row_id", "_meta"}:
            out.pop(k, None)
    return out


def upsert_queue_row(symbol: str, **fields: Any) -> dict[str, Any]:
    from institutional_warehouse import gateway, store

    ticker = str(symbol or "").strip().upper()
    existing = {}
    try:
        rows = store.fetch("hvie_universe_queue", filters={"symbol": ticker}, limit=1).get("rows") or []
        existing = rows[0] if rows else {}
    except Exception:
        existing = {}
    row = _clean({**existing, "symbol": ticker, **fields})
    gateway.write(
        "hvie_universe_queue",
        [row],
        source=ENGINE_CODE,
        actor=PROGRAMME_CODE,
        reason="hvie_universe_queue_upsert",
    )
    return row


def get_queue_row(symbol: str) -> dict[str, Any]:
    from institutional_warehouse import store

    ticker = str(symbol or "").strip().upper()
    try:
        rows = store.fetch("hvie_universe_queue", filters={"symbol": ticker}, limit=1).get("rows") or []
        return rows[0] if rows else {}
    except Exception:
        return {}


def all_queue_rows() -> list[dict[str, Any]]:
    return _paged_rows("hvie_universe_queue", max_rows=50_000)


def sync_universe(*, force_reclassify: bool = False) -> dict[str, Any]:
    """Ensure every company_master symbol has a queue row. Nothing unclassified."""
    masters = _paged_rows("company_master", max_rows=20_000)
    existing = {
        str(r.get("symbol") or "").strip().upper(): r
        for r in all_queue_rows()
        if r.get("symbol")
    }
    created = 0
    updated = 0
    for m in masters:
        sym = str(m.get("symbol") or "").strip().upper()
        if not sym:
            continue
        prev = existing.get(sym)
        if prev and not force_reclassify:
            # Keep identity fields fresh; never leave unclassified.
            if not prev.get("queue_status") or not prev.get("lifecycle"):
                upsert_queue_row(
                    sym,
                    queue_status=prev.get("queue_status") or QUEUE_PENDING,
                    lifecycle=prev.get("lifecycle") or LIFE_NOT_STARTED,
                    stage=prev.get("stage") or STAGE_CLASSIFY,
                    sector=m.get("sector") or prev.get("sector"),
                    industry=m.get("industry") or m.get("industry_dna") or prev.get("industry"),
                )
                updated += 1
            continue
        if prev and str(prev.get("queue_status") or "").upper() in {
            QUEUE_COMPLETED, QUEUE_RUNNING, QUEUE_FAILED, QUEUE_SKIPPED, QUEUE_RETRY, QUEUE_PENDING,
        } and not force_reclassify:
            # Refresh sector/industry only.
            upsert_queue_row(
                sym,
                sector=m.get("sector") or prev.get("sector"),
                industry=m.get("industry") or m.get("industry_dna") or prev.get("industry"),
            )
            updated += 1
            continue
        upsert_queue_row(
            sym,
            queue_status=QUEUE_PENDING,
            lifecycle=LIFE_NOT_STARTED,
            stage=STAGE_CLASSIFY,
            eligible=None,
            sector=m.get("sector"),
            industry=m.get("industry") or m.get("industry_dna"),
            attempts=0,
            classified_at=None,
        )
        created += 1

    # Recover RUNNING rows stuck after redeploy → RETRY
    recovered = 0
    for r in all_queue_rows():
        if str(r.get("queue_status") or "").upper() == QUEUE_RUNNING:
            upsert_queue_row(
                str(r.get("symbol")),
                queue_status=QUEUE_RETRY,
                lifecycle=LIFE_READY,
                next_retry_at=_now(),
                last_error="recovered_from_running_after_restart",
            )
            recovered += 1

    return {
        "ok": True,
        "universe": len(masters),
        "created": created,
        "updated": updated,
        "recovered_running": recovered,
        "queue_total": len(all_queue_rows()),
    }


def next_batch(*, batch: int = 20, now: Optional[str] = None) -> list[dict[str, Any]]:
    """Claim next PENDING/RETRY rows (eligible or unclassified)."""
    batch = max(1, min(int(batch), 100))
    now_s = now or _now()
    rows = all_queue_rows()
    candidates: list[dict[str, Any]] = []
    for r in rows:
        status = str(r.get("queue_status") or "").upper()
        if status == QUEUE_PENDING:
            candidates.append(r)
        elif status == QUEUE_RETRY:
            nxt = str(r.get("next_retry_at") or "")
            if not nxt or nxt <= now_s:
                candidates.append(r)
    # Prefer never-tried / fewer attempts, then alphabetical for stability.
    candidates.sort(
        key=lambda r: (
            int(r.get("attempts") or 0),
            str(r.get("symbol") or ""),
        )
    )
    claimed: list[dict[str, Any]] = []
    for r in candidates[:batch]:
        sym = str(r.get("symbol") or "").upper()
        row = upsert_queue_row(
            sym,
            queue_status=QUEUE_RUNNING,
            lifecycle=LIFE_RUNNING,
            last_run_at=_now(),
        )
        claimed.append(row)
    return claimed


def queue_counts() -> dict[str, int]:
    c = Counter(str(r.get("queue_status") or "UNKNOWN").upper() for r in all_queue_rows())
    return {k: int(v) for k, v in c.items()}


def lifecycle_counts() -> dict[str, int]:
    c = Counter(str(r.get("lifecycle") or "UNKNOWN").upper() for r in all_queue_rows())
    return {k: int(v) for k, v in c.items()}


def pipeline_counts() -> dict[str, int]:
    rows = all_queue_rows()
    return {
        "universe": len(rows),
        "classified": sum(1 for r in rows if r.get("lifecycle") and r.get("lifecycle") != LIFE_NOT_STARTED),
        "eligible": sum(1 for r in rows if r.get("eligible") is True),
        "seeded_history": sum(1 for r in rows if int(r.get("observations") or 0) > 0),
        "statistics": sum(1 for r in rows if r.get("has_statistics")),
        "percentiles": sum(1 for r in rows if r.get("has_percentile")),
        "bands": sum(1 for r in rows if r.get("has_bands")),
        "regimes": sum(1 for r in rows if r.get("has_regime")),
        "research": sum(1 for r in rows if r.get("has_research")),
        "complete": sum(
            1 for r in rows
            if str(r.get("lifecycle") or "").upper() == "COMPLETE"
            or str(r.get("queue_status") or "").upper() == QUEUE_COMPLETED
        ),
        "failed": sum(1 for r in rows if str(r.get("queue_status") or "").upper() == QUEUE_FAILED),
        "skipped": sum(1 for r in rows if str(r.get("queue_status") or "").upper() == QUEUE_SKIPPED),
        "pending": sum(1 for r in rows if str(r.get("queue_status") or "").upper() == QUEUE_PENDING),
        "retry": sum(1 for r in rows if str(r.get("queue_status") or "").upper() == QUEUE_RETRY),
        "running": sum(1 for r in rows if str(r.get("queue_status") or "").upper() == QUEUE_RUNNING),
    }


def mark_terminal(
    symbol: str,
    *,
    queue_status: str,
    lifecycle: str,
    stage: str,
    reason: Optional[str] = None,
    error: Optional[str] = None,
    **fields: Any,
) -> dict[str, Any]:
    payload = {
        "queue_status": queue_status,
        "lifecycle": lifecycle,
        "stage": stage,
        "last_run_at": _now(),
        **fields,
    }
    if reason is not None:
        payload["reason"] = reason
    if error is not None:
        payload["last_error"] = str(error)[:280]
    if queue_status == QUEUE_COMPLETED:
        payload["completed_at"] = _now()
    return upsert_queue_row(symbol, **payload)
