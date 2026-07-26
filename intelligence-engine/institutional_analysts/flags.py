"""IAF / IAI feature flags — soft defaults on; Answer Construction only."""

from __future__ import annotations


def _flag(name: str, default: bool = True) -> bool:
    try:
        from app.core.config import get_settings

        return bool(getattr(get_settings(), name, default))
    except Exception:
        return default


def is_enabled() -> bool:
    return _flag("institutional_analysts", True) and _flag("ask_agi_iaf", True)


def is_iai_business_enabled() -> bool:
    """Phase 3 IAI — Business Analyst institutional brain (soft; no redesign)."""
    return is_enabled() and _flag("institutional_analyst_intelligence", True) and _flag(
        "iai_business_analyst", True
    )


def flags_dict() -> dict[str, bool]:
    return {
        "INSTITUTIONAL_ANALYSTS": _flag("institutional_analysts", True),
        "ASK_AGI_IAF": _flag("ask_agi_iaf", True),
        "IAF_ENABLED": is_enabled(),
        "INSTITUTIONAL_ANALYST_INTELLIGENCE": _flag("institutional_analyst_intelligence", True),
        "IAI_BUSINESS_ANALYST": _flag("iai_business_analyst", True),
        "IAI_BUSINESS_ENABLED": is_iai_business_enabled(),
    }
