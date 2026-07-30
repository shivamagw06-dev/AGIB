"""FAA background collector — never runs on the Ask request path.

Architecture:
  FAA Collector (this module) → FRE/FAA in-memory snapshot → Ask reads index only

Enable with ``FAA_BACKGROUND_COLLECTOR=1`` (default on). Interval via
``FAA_COLLECTOR_INTERVAL_SEC`` (default 300).
"""

from __future__ import annotations

import logging
import os
import threading
import time
from typing import Any, Callable

log = logging.getLogger("agi.faa.background")

_STOP = threading.Event()
_THREAD: threading.Thread | None = None


def _env_truthy(name: str, default: str = "1") -> bool:
    return str(os.environ.get(name, default)).strip().lower() in {"1", "true", "yes", "on"}


def _interval_sec() -> float:
    try:
        return max(60.0, float(os.environ.get("FAA_COLLECTOR_INTERVAL_SEC") or "300"))
    except ValueError:
        return 300.0


def _limit() -> int:
    try:
        return max(2, min(16, int(os.environ.get("FAA_COLLECTOR_LIMIT") or "6")))
    except ValueError:
        return 6


def collector_enabled() -> bool:
    return _env_truthy("FAA_BACKGROUND_COLLECTOR", "1")


def run_collector_once(faa: Any) -> dict[str, Any]:
    """One background refresh cycle. Safe to call from a worker thread."""
    if faa is None:
        return {"ok": False, "error": "faa_unbound"}
    if hasattr(faa, "refresh_snapshots"):
        return faa.refresh_snapshots(limit_per_query=_limit())
    if hasattr(faa, "run_jobs"):
        return faa.run_jobs()
    return {"ok": False, "error": "no_refresh_method"}


def _loop(faa_factory: Callable[[], Any]) -> None:
    # Stagger first run so boot/health stay responsive.
    time.sleep(min(45.0, _interval_sec() / 4))
    while not _STOP.is_set():
        if not collector_enabled():
            _STOP.wait(30.0)
            continue
        try:
            faa = faa_factory()
            result = run_collector_once(faa)
            log.info(
                "faa_background_cycle",
                extra={
                    "ok": bool(result.get("ok", True)),
                    "queries": result.get("queries") or len(result.get("runs") or []),
                    "errors": len(result.get("errors") or []),
                },
            )
        except Exception as exc:  # noqa: BLE001 — never kill the collector thread
            log.warning("faa_background_cycle_failed", extra={"error": str(exc)[:200]})
        _STOP.wait(_interval_sec())


def start_background_collector(faa_factory: Callable[[], Any]) -> dict[str, Any]:
    """Start daemon collector thread once. Idempotent."""
    global _THREAD
    if not collector_enabled():
        return {"started": False, "reason": "disabled"}
    if _THREAD is not None and _THREAD.is_alive():
        return {"started": False, "reason": "already_running"}
    _STOP.clear()
    _THREAD = threading.Thread(
        target=_loop,
        args=(faa_factory,),
        name="faa-background-collector",
        daemon=True,
    )
    _THREAD.start()
    return {
        "started": True,
        "interval_sec": _interval_sec(),
        "limit": _limit(),
    }


def stop_background_collector() -> None:
    _STOP.set()
