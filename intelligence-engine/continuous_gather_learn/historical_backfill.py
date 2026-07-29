"""CGL Historical Backfill workflow — resumable institutional depth builder."""

from __future__ import annotations

import os
from typing import Any

from continuous_gather_learn import persist as cgl_persist
from continuous_gather_learn.knowledge_extract import extract_from_hd_series


def backfill_enabled() -> bool:
    return str(os.getenv("CONTINUOUS_HISTORICAL_BACKFILL", "true")).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def run_historical_backfill(*, batch_size: int | None = None) -> dict[str, Any]:
    """Oldest-available → download → validate → store → extract → archive."""
    if not backfill_enabled():
        return {"ok": False, "skipped": True, "reason": "CONTINUOUS_HISTORICAL_BACKFILL=false"}
    from knowledge_factory.historical_depth.backfill import coverage_progress, run_backfill_batch

    report = run_backfill_batch(batch_size=batch_size, derive=True)
    extracts = []
    for row in report.get("rows") or []:
        ent = str(row.get("entity") or "")
        if not ent or row.get("skipped"):
            continue
        try:
            extracts.append(extract_from_hd_series(ent))
        except Exception as exc:  # noqa: BLE001
            extracts.append({"entity": ent, "error": str(exc)[:160]})
    progress = coverage_progress()
    cgl_persist.put_checkpoint(
        "historical_backfill",
        {
            "last_ok": bool(report.get("ok")),
            "processed": report.get("processed"),
            "completed_total": report.get("completed_total"),
            "remaining": report.get("remaining"),
            "dashboard": report.get("dashboard"),
            "progress": progress,
            "extracts": len(extracts),
        },
    )
    return {
        "ok": True,
        "backfill": report,
        "knowledge_extracts": extracts,
        "progress": progress,
        "resumable": True,
    }
