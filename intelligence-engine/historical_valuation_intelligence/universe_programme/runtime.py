"""Continuous HVIE universe bootstrap runtime — drains persisted queue until done."""

from __future__ import annotations

import os
import threading
import time
from datetime import datetime, timezone
from typing import Any, Optional

from historical_valuation_intelligence.models import ENGINE_CODE, VERSION
from historical_valuation_intelligence.universe_programme import aggregates, pipeline, queue
from historical_valuation_intelligence.universe_programme.models import (
    PROGRAMME_CODE,
    PROGRAMME_VERSION,
    QUEUE_PENDING,
    QUEUE_RETRY,
)

_LOCK = threading.Lock()
_THREAD: Optional[threading.Thread] = None
_STATE: dict[str, Any] = {
    "status": "idle",  # idle | running | stopped
    "started_at": None,
    "stopped": False,
    "last_tick": None,
    "last_error": None,
    "last_batch": None,
    "completed_this_session": 0,
    "failed_this_session": 0,
    "processed_this_session": 0,
    "started_mono": None,
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _truthy(name: str, default: str = "true") -> bool:
    return str(os.getenv(name, default)).strip().lower() in {"1", "true", "yes", "on"}


def ensure_classified() -> dict[str, Any]:
    return queue.sync_universe()


def process_batch(*, batch: int = 15) -> dict[str, Any]:
    """Claim and process one batch from the persisted queue."""
    sync = queue.sync_universe()
    # Periodically re-promote waiting names when raw data arrives.
    if int(sync.get("queue_total") or 0) % 17 == 0:
        pipeline.requeue_waiting(limit=50)

    claimed = queue.next_batch(batch=batch)
    results = []
    ok = 0
    failed = 0
    skipped = 0
    completed = 0
    t0 = time.time()
    for row in claimed:
        sym = str(row.get("symbol") or "").upper()
        try:
            out = pipeline.process_company(sym)
        except Exception as exc:
            out = {"ok": False, "symbol": sym, "error": str(exc)[:200], "queue_status": "RETRY"}
            queue.upsert_queue_row(
                sym,
                queue_status=QUEUE_RETRY,
                lifecycle="READY",
                last_error=str(exc)[:280],
                next_retry_at=_now(),
            )
        results.append(out)
        status = str(out.get("queue_status") or "").upper()
        if out.get("ok") and status == "COMPLETED":
            completed += 1
            ok += 1
        elif status == "SKIPPED":
            skipped += 1
            ok += 1
        elif status == "FAILED":
            failed += 1
        elif status == "RETRY":
            failed += 1
        else:
            ok += 1

    elapsed = max(0.001, time.time() - t0)
    counts = queue.pipeline_counts()
    with _LOCK:
        _STATE["last_tick"] = _now()
        _STATE["last_batch"] = {
            "attempted": len(claimed),
            "completed": completed,
            "failed": failed,
            "skipped": skipped,
            "elapsed_seconds": round(elapsed, 2),
        }
        _STATE["completed_this_session"] += completed
        _STATE["failed_this_session"] += failed
        _STATE["processed_this_session"] += len(claimed)

    return {
        "ok": True,
        "mode": "universe_bootstrap",
        "attempted": len(claimed),
        "completed": completed,
        "failed": failed,
        "skipped": skipped,
        "elapsed_seconds": round(elapsed, 2),
        "companies_per_hour": round(len(claimed) * 3600.0 / elapsed, 1) if claimed else 0.0,
        "pipeline": counts,
        "sync": sync,
        "engine": ENGINE_CODE,
        "programme": PROGRAMME_CODE,
        "version": PROGRAMME_VERSION,
        "results": results,
    }


def throughput() -> dict[str, Any]:
    counts = queue.pipeline_counts()
    with _LOCK:
        processed = int(_STATE.get("processed_this_session") or 0)
        started = _STATE.get("started_mono")
        session_completed = int(_STATE.get("completed_this_session") or 0)
    elapsed_h = 0.0
    if started:
        elapsed_h = max(0.001, (time.time() - float(started)) / 3600.0)
    speed = (processed / elapsed_h) if started and processed else 0.0
    remaining = int(counts.get("pending") or 0) + int(counts.get("retry") or 0) + int(counts.get("running") or 0)
    eta_hours = (remaining / speed) if speed > 0 else None
    return {
        "ok": True,
        "universe": counts.get("universe"),
        "completed": counts.get("complete"),
        "remaining": remaining,
        "speed_per_hour": round(speed, 1),
        "eta_hours": round(eta_hours, 1) if eta_hours is not None else None,
        "session_processed": processed,
        "session_completed": session_completed,
        "pipeline": counts,
    }


def status() -> dict[str, Any]:
    with _LOCK:
        snap = {k: v for k, v in _STATE.items() if k != "started_mono"}
    pipe = queue.pipeline_counts()
    qcounts = queue.queue_counts()
    thr = throughput()
    return {
        "ok": True,
        "engine": ENGINE_CODE,
        "programme": PROGRAMME_CODE,
        "version": PROGRAMME_VERSION,
        "hvie_version": VERSION,
        "runtime": snap,
        "queue": qcounts,
        "pipeline": pipe,
        "throughput": thr,
        "completion": {
            "pending": pipe.get("pending"),
            "running": pipe.get("running"),
            "retry": pipe.get("retry"),
            "done": (
                int(pipe.get("pending") or 0) == 0
                and int(pipe.get("running") or 0) == 0
                and int(pipe.get("retry") or 0) == 0
            ),
        },
        "schedules": {
            "bootstrap": "continuous until pending=running=retry=0",
            "daily": "append one observation after bootstrap complete",
            "statement": "forward reconstruct release→today",
            "corporate_action": "full reconstruct on structural CA",
        },
    }


def pipeline_dashboard() -> dict[str, Any]:
    pipe = queue.pipeline_counts()
    return {
        "ok": True,
        "title": "HVIE Pipeline",
        "stages": [
            {"name": "Universe", "count": pipe.get("universe"), "pct": 100.0},
            {"name": "Eligible", "count": pipe.get("eligible")},
            {"name": "Seeded / History Built", "count": pipe.get("seeded_history")},
            {"name": "Statistics", "count": pipe.get("statistics")},
            {"name": "Percentiles", "count": pipe.get("percentiles")},
            {"name": "Bands", "count": pipe.get("bands")},
            {"name": "Regimes", "count": pipe.get("regimes")},
            {"name": "Research Timeline", "count": pipe.get("research")},
            {"name": "Complete", "count": pipe.get("complete")},
        ],
        "queue": queue.queue_counts(),
        "lifecycle": queue.lifecycle_counts(),
        "throughput": throughput(),
        "engine": ENGINE_CODE,
        "programme": PROGRAMME_CODE,
        "version": PROGRAMME_VERSION,
    }


def failures(*, limit: int = 100) -> dict[str, Any]:
    rows = [
        r for r in queue.all_queue_rows()
        if str(r.get("queue_status") or "").upper() in {"FAILED", "RETRY", "SKIPPED"}
    ]
    rows.sort(key=lambda r: str(r.get("last_run_at") or ""), reverse=True)
    return {
        "ok": True,
        "count": len(rows),
        "rows": rows[: max(1, min(int(limit), 500))],
    }


def company_status(symbol: str) -> dict[str, Any]:
    row = queue.get_queue_row(symbol)
    return {
        "ok": bool(row),
        "symbol": str(symbol or "").upper(),
        "row": row or None,
        "engine": ENGINE_CODE,
        "programme": PROGRAMME_CODE,
    }


def retry_symbol(symbol: str) -> dict[str, Any]:
    ticker = str(symbol or "").strip().upper()
    queue.upsert_queue_row(
        ticker,
        queue_status=QUEUE_PENDING,
        lifecycle="READY",
        next_retry_at=None,
        last_error=None,
        reason="manual_retry",
    )
    out = pipeline.process_company(ticker)
    return {"ok": True, "result": out}


def reconstruct_symbol(symbol: str) -> dict[str, Any]:
    ticker = str(symbol or "").strip().upper()
    queue.upsert_queue_row(
        ticker,
        queue_status=QUEUE_PENDING,
        lifecycle="READY",
        attempts=0,
        next_retry_at=None,
        last_error=None,
        reason="manual_reconstruct",
    )
    return pipeline.process_company(ticker)


def persist_aggregates(*, metric: str = "pe") -> dict[str, Any]:
    return aggregates.persist_cross_section_medians(metric=metric)


def start(*, interval_seconds: Optional[float] = None, batch: Optional[int] = None) -> dict[str, Any]:
    global _THREAD
    if not _truthy("HVIE_UNIVERSE_RUNTIME", "true"):
        return {"ok": True, "enabled": False, "reason": "HVIE_UNIVERSE_RUNTIME=false"}
    if _THREAD and _THREAD.is_alive():
        return {"ok": True, "enabled": True, "already_running": True, "status": status()}

    interval = float(interval_seconds or os.getenv("HVIE_UNIVERSE_INTERVAL_SECONDS") or 90)
    batch_n = int(batch or os.getenv("HVIE_UNIVERSE_BATCH") or 12)

    def _loop() -> None:
        with _LOCK:
            _STATE["status"] = "running"
            _STATE["started_at"] = _now()
            _STATE["started_mono"] = time.time()
            _STATE["stopped"] = False
            _STATE["completed_this_session"] = 0
            _STATE["failed_this_session"] = 0
            _STATE["processed_this_session"] = 0
        ensure_classified()
        while True:
            with _LOCK:
                if _STATE.get("stopped"):
                    break
            try:
                out = process_batch(batch=batch_n)
                done = (
                    int((out.get("pipeline") or {}).get("pending") or 0) == 0
                    and int((out.get("pipeline") or {}).get("retry") or 0) == 0
                    and int((out.get("pipeline") or {}).get("running") or 0) == 0
                )
                if done:
                    # Bootstrap complete — persist aggregates once, then idle lightly.
                    try:
                        persist_aggregates(metric="pe")
                    except Exception:
                        pass
                    # Keep loop alive for requeue of waiting names + new listings.
                    pipeline.requeue_waiting(limit=100)
                    time.sleep(max(60.0, interval))
                    continue
            except Exception as exc:
                with _LOCK:
                    _STATE["last_error"] = str(exc)[:300]
            time.sleep(max(15.0, interval))
        with _LOCK:
            _STATE["status"] = "stopped"

    _THREAD = threading.Thread(target=_loop, name="hvie-universe-runtime", daemon=True)
    _THREAD.start()
    return {
        "ok": True,
        "enabled": True,
        "interval_seconds": interval,
        "batch": batch_n,
        "programme": PROGRAMME_CODE,
        "version": PROGRAMME_VERSION,
    }


def stop() -> dict[str, Any]:
    with _LOCK:
        _STATE["stopped"] = True
        _STATE["status"] = "stopped"
    return {"ok": True, "stopped": True}


def resume() -> dict[str, Any]:
    """Alias for start — recovers RUNNING→RETRY via sync_universe."""
    ensure_classified()
    return start()
