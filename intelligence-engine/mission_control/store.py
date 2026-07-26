"""Process-local Mission Control cache + acknowledged alerts."""

from __future__ import annotations

from copy import deepcopy
from threading import Lock
from time import monotonic
from typing import Any


_LOCK = Lock()
_DASH: dict[str, Any] | None = None
_DASH_AT: float = 0.0
_ACK: set[str] = set()

# Short TTL keeps the cockpit snappy under parallel health/dashboard/gates calls.
_DASH_TTL_SEC = 20.0


def put_dashboard(row: dict[str, Any]) -> dict[str, Any]:
    global _DASH, _DASH_AT
    with _LOCK:
        _DASH = deepcopy(row)
        _DASH_AT = monotonic()
    return row


def get_dashboard(*, max_age_sec: float | None = None) -> dict[str, Any] | None:
    ttl = _DASH_TTL_SEC if max_age_sec is None else max_age_sec
    with _LOCK:
        if not _DASH:
            return None
        if ttl >= 0 and (monotonic() - _DASH_AT) > ttl:
            return None
        return deepcopy(_DASH)


def acknowledge(alert_id: str, *, actor: str | None = None) -> dict[str, Any]:
    aid = str(alert_id or "").strip()
    with _LOCK:
        if aid:
            _ACK.add(aid)
        return {
            "ok": True,
            "acknowledged": True,
            "alert_id": aid,
            "actor": actor,
            "acknowledged_ids": sorted(_ACK),
        }


def acknowledged_ids() -> set[str]:
    with _LOCK:
        return set(_ACK)


def reset_for_tests() -> None:
    global _DASH, _DASH_AT
    with _LOCK:
        _DASH = None
        _DASH_AT = 0.0
        _ACK.clear()
