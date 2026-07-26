"""Process-local Mission Control cache + acknowledged alerts."""

from __future__ import annotations

from copy import deepcopy
from threading import Lock
from typing import Any


_LOCK = Lock()
_DASH: dict[str, Any] | None = None
_ACK: set[str] = set()


def put_dashboard(row: dict[str, Any]) -> dict[str, Any]:
    global _DASH
    with _LOCK:
        _DASH = deepcopy(row)
    return row


def get_dashboard() -> dict[str, Any] | None:
    with _LOCK:
        return deepcopy(_DASH) if _DASH else None


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
    global _DASH
    with _LOCK:
        _DASH = None
        _ACK.clear()
