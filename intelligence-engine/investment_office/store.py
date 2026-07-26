"""Process-local IO desk cache."""

from __future__ import annotations

from copy import deepcopy
from threading import Lock
from typing import Any


_LOCK = Lock()
_DESK: dict[str, Any] | None = None


def put_desk(desk: dict[str, Any]) -> dict[str, Any]:
    global _DESK
    with _LOCK:
        _DESK = deepcopy(desk)
    return desk


def get_desk() -> dict[str, Any] | None:
    with _LOCK:
        return deepcopy(_DESK) if _DESK else None


def reset_for_tests() -> None:
    global _DESK
    with _LOCK:
        _DESK = None
