"""CGL Historical Backfill — continuous until 100% coverage, then maintenance."""

from __future__ import annotations

import os
from typing import Any

from continuous_gather_learn import persist as cgl_persist


def backfill_enabled() -> bool:
    return str(os.getenv("CONTINUOUS_HISTORICAL_BACKFILL", "true")).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def until_complete_enabled() -> bool:
    return str(os.getenv("CONTINUOUS_BACKFILL_UNTIL_COMPLETE", "true")).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def run_historical_backfill(*, batch_size: int | None = None, max_batches: int | None = None) -> dict[str, Any]:
    """Drain prioritised backlog batches; do not stop after a single successful cycle."""
    if not backfill_enabled():
        return {"ok": False, "skipped": True, "reason": "CONTINUOUS_HISTORICAL_BACKFILL=false"}

    from knowledge_factory.historical_depth.backfill import coverage_progress, run_until_batch_budget
    from knowledge_factory.historical_depth import queue as bf_queue

    if until_complete_enabled():
        budget = run_until_batch_budget(max_batches=max_batches, batch_size=batch_size, stop_when_empty=True)
    else:
        from knowledge_factory.historical_depth.backfill import run_backfill_batch

        single = run_backfill_batch(batch_size=batch_size, derive=True)
        budget = {
            "ok": True,
            "batches_run": 1,
            "batches": [{"processed": single.get("processed"), "remaining": single.get("remaining")}],
            "remaining": single.get("remaining"),
            "fully_backfilled": single.get("completed_total"),
            "mode": single.get("mode"),
            "last": single,
        }

    progress = coverage_progress()
    cgl_persist.put_checkpoint(
        "historical_backfill",
        {
            "last_ok": True,
            "continues_until_complete": until_complete_enabled() and not progress.get("maintenance_only"),
            "batches_run": budget.get("batches_run"),
            "completed_total": progress.get("companies_fully_backfilled"),
            "remaining": progress.get("remaining_backlog"),
            "queue_length": progress.get("queue_length"),
            "mode": progress.get("mode"),
            "maintenance_only": progress.get("maintenance_only"),
            "completed_at": progress.get("completed_at"),
            "progress": progress,
            "engine": bf_queue.load_engine_state(),
        },
    )
    # Surface extracts from last batch rows when available
    last = __import__(
        "knowledge_factory.historical_depth.store", fromlist=["get_report"]
    ).get_report("historical_backfill_last") or {}
    extracts = []
    for row in last.get("rows") or []:
        if row.get("extract_ok") or (row.get("evaluation") or {}).get("dimensions", {}).get(
            "knowledge_extract", {}
        ).get("status") == "complete":
            extracts.append({"entity": row.get("entity"), "ok": True})

    return {
        "ok": True,
        "backfill": budget,
        "knowledge_extracts": extracts,
        "progress": progress,
        "resumable": True,
        "continues_until_complete": bool(progress.get("continues_until_complete")),
        "maintenance_only": bool(progress.get("maintenance_only")),
    }
