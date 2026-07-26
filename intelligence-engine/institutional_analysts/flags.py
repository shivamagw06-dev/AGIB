"""IAF feature flags — soft defaults on; Answer Construction only."""

from __future__ import annotations


def _flag(name: str, default: bool = True) -> bool:
    try:
        from app.core.config import get_settings

        return bool(getattr(get_settings(), name, default))
    except Exception:
        return default


def is_enabled() -> bool:
    return _flag("institutional_analysts", True) and _flag("ask_agi_iaf", True)


def flags_dict() -> dict[str, bool]:
    return {
        "INSTITUTIONAL_ANALYSTS": _flag("institutional_analysts", True),
        "ASK_AGI_IAF": _flag("ask_agi_iaf", True),
        "IAF_ENABLED": is_enabled(),
    }
