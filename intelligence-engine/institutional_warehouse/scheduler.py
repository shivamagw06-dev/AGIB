"""Daily refresh scheduler.

The warehouse refreshes once a day after the Indian market close and the
bhavcopy publication — 18:45 IST by default. The thread is deliberately dumb:
it wakes every minute, checks whether the daily slot has passed and whether
today's run has already happened, and calls the pipeline.

Enable with ``WAREHOUSE_DAILY_REFRESH=true``; change the slot with
``WAREHOUSE_REFRESH_AT`` (24h IST, e.g. ``18:45``).
"""

from __future__ import annotations

import os
import threading
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

IST = timezone(timedelta(hours=5, minutes=30))

_THREAD: Optional[threading.Thread] = None
_STOP = threading.Event()
_STATE: dict[str, Any] = {"last_run_date": None, "last_result": None, "runs": 0}


def _truthy(name: str, default: str = "false") -> bool:
    return str(os.getenv(name, default)).strip().lower() in {"1", "true", "yes", "on"}


def refresh_slot() -> tuple[int, int]:
    raw = (os.getenv("WAREHOUSE_REFRESH_AT") or "18:45").strip()
    try:
        hour, minute = raw.split(":")
        return max(0, min(int(hour), 23)), max(0, min(int(minute), 59))
    except Exception:
        return 18, 45


def due(now: Optional[datetime] = None) -> bool:
    moment = (now or datetime.now(timezone.utc)).astimezone(IST)
    hour, minute = refresh_slot()
    if (moment.hour, moment.minute) < (hour, minute):
        return False
    return _STATE.get("last_run_date") != moment.date().isoformat()


def run_once(*, actor: str = "scheduler", days: int = 10) -> dict[str, Any]:
    from institutional_warehouse.refresh import run

    result = run(actor=actor, days=days)
    _STATE["last_run_date"] = datetime.now(IST).date().isoformat()
    _STATE["last_result"] = {
        "run_id": result.get("run_id"),
        "ok": result.get("ok"),
        "finished_at": result.get("finished_at"),
        "errors": result.get("errors"),
    }
    _STATE["runs"] = int(_STATE.get("runs") or 0) + 1
    return result


def _loop(poll_seconds: float) -> None:
    while not _STOP.wait(poll_seconds):
        try:
            if due():
                run_once()
        except Exception:
            # A failed refresh must never kill the scheduler; the run record and
            # the audit trail carry the error.
            continue


def start(*, boot_run: bool = False, poll_seconds: float = 60.0) -> dict[str, Any]:
    global _THREAD
    if not _truthy("WAREHOUSE_DAILY_REFRESH"):
        return {"ok": True, "enabled": False, "reason": "WAREHOUSE_DAILY_REFRESH is off"}
    if _THREAD and _THREAD.is_alive():
        return {"ok": True, "enabled": True, "already_running": True}

    hour, minute = refresh_slot()
    if boot_run:
        try:
            run_once(actor="scheduler_boot")
        except Exception:
            pass

    _STOP.clear()
    _THREAD = threading.Thread(target=_loop, args=(poll_seconds,), name="warehouse-refresh",
                               daemon=True)
    _THREAD.start()
    return {"ok": True, "enabled": True, "slot_ist": f"{hour:02d}:{minute:02d}", "boot_run": boot_run}


def stop() -> dict[str, Any]:
    _STOP.set()
    thread = _THREAD
    if thread and thread.is_alive():
        thread.join(timeout=5.0)
    return {"ok": True, "stopped": True}


def status() -> dict[str, Any]:
    hour, minute = refresh_slot()
    return {
        "ok": True,
        "enabled": _truthy("WAREHOUSE_DAILY_REFRESH"),
        "running": bool(_THREAD and _THREAD.is_alive()),
        "slot_ist": f"{hour:02d}:{minute:02d}",
        "due_now": due(),
        **_STATE,
    }
