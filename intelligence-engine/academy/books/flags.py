"""Academy Books feature flags."""

from __future__ import annotations

from typing import Any


def _settings():
    try:
        from app.core.config import get_settings

        return get_settings()
    except Exception:
        return None


def is_academy_enabled() -> bool:
    s = _settings()
    return True if s is None else bool(getattr(s, "academy", True))


def is_books_enabled() -> bool:
    s = _settings()
    if s is None:
        return True
    return bool(getattr(s, "academy", True)) and bool(getattr(s, "academy_books", True))


def flag_frameworks() -> bool:
    s = _settings()
    return True if s is None else bool(getattr(s, "academy_frameworks", True))


def flag_formulas() -> bool:
    s = _settings()
    return True if s is None else bool(getattr(s, "academy_formulas", True))


def flag_graph() -> bool:
    s = _settings()
    return True if s is None else bool(getattr(s, "academy_graph", True))


def flag_spreadsheets() -> bool:
    s = _settings()
    return True if s is None else bool(getattr(s, "academy_spreadsheets", True))


def flag_books_v3() -> bool:
    """Academy Books V3 — institutional knowledge transformation (soft layer)."""
    s = _settings()
    if s is None:
        return True
    return bool(getattr(s, "academy", True)) and bool(getattr(s, "academy_books_v3", True))


def flag_validation_suite() -> bool:
    s = _settings()
    if s is None:
        return True
    return bool(getattr(s, "academy", True)) and bool(
        getattr(s, "academy_validation_suite", True)
    )


def flags_dict() -> dict[str, Any]:
    return {
        "ACADEMY": is_academy_enabled(),
        "ACADEMY_BOOKS": is_books_enabled(),
        "ACADEMY_BOOKS_V3": flag_books_v3(),
        "ACADEMY_VALIDATION_SUITE": flag_validation_suite(),
        "ACADEMY_FRAMEWORKS": flag_frameworks(),
        "ACADEMY_FORMULAS": flag_formulas(),
        "ACADEMY_GRAPH": flag_graph(),
        "ACADEMY_SPREADSHEETS": flag_spreadsheets(),
    }
