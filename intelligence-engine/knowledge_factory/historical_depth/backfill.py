"""Resumable Historical Depth backfill — never restarts completed entities."""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Any

from knowledge_factory.historical_depth import store as hd_store
from knowledge_factory.historical_depth.collectors import collect_entity_history, collect_market_history
from knowledge_factory.historical_depth.dashboard import historical_depth_dashboard
from knowledge_factory.historical_depth.fixtures.seed_history import seed_universe
from knowledge_factory.historical_depth.objects.company import compile_historical_company
from knowledge_factory.historical_depth.packs import build_historical_pack
from knowledge_factory.historical_depth.producers.derived import produce_derived
from knowledge_factory.historical_depth.validators import validate_series

BACKFILL_VERSION = "hd-backfill-v1.0.0"
TARGET_YEARS = float(os.getenv("KF_HD_TARGET_YEARS") or "15")
BATCH_DEFAULT = int(os.getenv("KF_HD_BACKFILL_BATCH") or "12")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _entity_years(entity: str) -> float:
    annual = hd_store.get_series("financials_annual", entity) or {}
    prices = hd_store.get_series("prices", entity) or {}
    a_n = float(len(annual.get("records") or []))
    ends = [str(r.get("period_end") or "")[:10] for r in (prices.get("records") or []) if r.get("period_end")]
    p_years = 0.0
    if len(ends) >= 2:
        try:
            d0 = datetime.fromisoformat(min(ends))
            d1 = datetime.fromisoformat(max(ends))
            p_years = (d1 - d0).days / 365.25
        except Exception:
            p_years = float(len({e[:4] for e in ends}))
    return max(a_n, p_years)


def is_complete(entity: str, *, target_years: float = TARGET_YEARS) -> bool:
    return _entity_years(entity) >= target_years


def load_checkpoint() -> dict[str, Any]:
    return hd_store.get_report("historical_backfill_checkpoint") or {
        "completed": [],
        "failed": {},
        "cursor": 0,
        "updated_at": None,
    }


def save_checkpoint(ck: dict[str, Any]) -> None:
    ck = {**ck, "updated_at": _now(), "backfill_version": BACKFILL_VERSION}
    hd_store.put_report("historical_backfill_checkpoint", ck)


def pending_entities(entities: list[str] | None = None, *, target_years: float = TARGET_YEARS) -> list[str]:
    universe = entities or seed_universe()
    ck = load_checkpoint()
    done = {str(x).upper() for x in (ck.get("completed") or [])}
    out = []
    for e in universe:
        eu = e.upper()
        if eu in done:
            continue
        if is_complete(eu, target_years=target_years):
            done.add(eu)
            continue
        out.append(eu)
    # Persist newly discovered completes without work
    if len(done) > len(ck.get("completed") or []):
        ck["completed"] = sorted(done)
        save_checkpoint(ck)
    return out


def run_backfill_batch(
    *,
    entities: list[str] | None = None,
    batch_size: int | None = None,
    target_years: float = TARGET_YEARS,
    derive: bool = True,
) -> dict[str, Any]:
    """Download → validate → normalise → store → extract-ready packs for one batch."""
    t0 = time.perf_counter()
    batch_size = max(1, int(batch_size or BATCH_DEFAULT))
    pending = pending_entities(entities, target_years=target_years)
    batch = pending[:batch_size]
    ck = load_checkpoint()
    completed = {str(x).upper() for x in (ck.get("completed") or [])}
    failed = dict(ck.get("failed") or {})
    rows: list[dict[str, Any]] = []
    validation_failures: list[dict[str, Any]] = []

    collect_market_history()

    for e in batch:
        # Retry budget: skip hot failures for a few cycles
        fail_meta = failed.get(e) or {}
        if int(fail_meta.get("streak") or 0) >= 5 and fail_meta.get("cooldown_until"):
            if str(fail_meta["cooldown_until"]) > _now():
                rows.append({"entity": e, "status": "cooldown", "skipped": True})
                continue
        try:
            # Force live prefer for backfill
            os.environ.setdefault("KF_HD_LIVE_COLLECTORS", "true")
            row = collect_entity_history(e, prefer_live=True)
            for kind in ("financials_annual", "financials_quarterly", "prices"):
                series = hd_store.get_series(kind, e)
                verdict = validate_series(series) if series else {"ok": True}
                if series and not verdict.get("ok"):
                    validation_failures.append({"entity": e, "kind": kind, **verdict})
            if derive:
                produce_derived(e)
                compile_historical_company(e)
                build_historical_pack(e)
            years = _entity_years(e)
            row["history_years"] = years
            row["complete"] = years >= target_years
            if row.get("complete"):
                completed.add(e)
                failed.pop(e, None)
            else:
                # Partial progress still OK — clear fail streak
                failed.pop(e, None)
            rows.append(row)
        except Exception as exc:  # noqa: BLE001
            streak = int((failed.get(e) or {}).get("streak") or 0) + 1
            failed[e] = {
                "streak": streak,
                "error": str(exc)[:200],
                "at": _now(),
                "cooldown_until": _now() if streak < 5 else _now(),  # simple marker
            }
            rows.append({"entity": e, "status": "error", "error": str(exc)[:200]})

    ck["completed"] = sorted(completed)
    ck["failed"] = failed
    ck["cursor"] = int(ck.get("cursor") or 0) + len(batch)
    ck["last_batch"] = [r.get("entity") for r in rows]
    save_checkpoint(ck)

    dash = historical_depth_dashboard(entities=entities or seed_universe())
    remaining = len(pending) - len([r for r in rows if r.get("complete")])
    # Recompute pending after this batch
    remaining = len(pending_entities(entities, target_years=target_years))
    report = {
        "backfill_version": BACKFILL_VERSION,
        "ok": True,
        "batch_size": batch_size,
        "processed": len(rows),
        "completed_total": len(completed),
        "remaining": remaining,
        "target_years": target_years,
        "rows": rows,
        "validation_failures": validation_failures,
        "dashboard": {
            "average_history_years": dash.get("average_history_years"),
            "historical_completeness_pct": dash.get("historical_completeness_pct"),
            "companies_gt_10y": dash.get("companies_gt_10y"),
            "universe_n": dash.get("universe_n"),
        },
        "runtime_seconds": round(time.perf_counter() - t0, 2),
        "generated_at": _now(),
        "resumable": True,
        "note": "Never restarts completed entities; checkpointed under historical_backfill_checkpoint",
    }
    hd_store.put_report("historical_backfill_last", report)
    return report


def coverage_progress(*, entities: list[str] | None = None) -> dict[str, Any]:
    universe = entities or seed_universe()
    ck = load_checkpoint()
    dash = historical_depth_dashboard(entities=universe)
    remaining = len(pending_entities(universe))
    completed = len(ck.get("completed") or [])
    n = len(universe) or 1
    # Growth estimate: last batch runtime → entities/day rough
    last = hd_store.get_report("historical_backfill_last") or {}
    processed = int(last.get("processed") or 0)
    runtime = float(last.get("runtime_seconds") or 0) or 1.0
    per_day = (processed / runtime) * 86400.0 if processed else 0.0
    eta_days = (remaining / per_day) if per_day > 0 else None
    return {
        "universe_n": n,
        "companies_fully_backfilled": completed,
        "remaining_backlog": remaining,
        "average_history_years": dash.get("average_history_years"),
        "historical_coverage_pct": dash.get("historical_completeness_pct"),
        "companies_gt_10y": dash.get("companies_gt_10y"),
        "companies_gt_15y": dash.get("companies_gt_15y"),
        "estimated_completion_days": round(eta_days, 1) if eta_days is not None else None,
        "historical_growth_per_day_entities": round(per_day, 1) if per_day else 0,
        "last_backfill_at": last.get("generated_at") or ck.get("updated_at"),
        "target_years": TARGET_YEARS,
    }
