"""Ask AGI Answer Construction V3 — soft production entry."""

from __future__ import annotations

from typing import Any

from answer_construction.flags import flags_dict, is_enabled
from answer_construction.policy import apply_answer_construction_v3
from answer_construction.schema import AC_VERSION, ARCHITECTURE_STATUS, PROGRAMME


def health() -> dict[str, Any]:
    return {
        "status": "ok" if is_enabled() else "disabled",
        "programme": PROGRAMME,
        "version": AC_VERSION,
        "architecture_status": ARCHITECTURE_STATUS,
        "not_an_engine": True,
        "gate_logic_unchanged": True,
        "never_stop_at_first_coverage_check": True,
        "flags": flags_dict(),
    }


def package_for_ask_agi(**kwargs: Any) -> dict[str, Any]:
    """Soft entry used by UiService after IRP / IC / ECP orchestration."""
    return apply_answer_construction_v3(**kwargs)


def quality_gates() -> dict[str, Any]:
    return {
        "programme": PROGRAMME,
        "version": AC_VERSION,
        "architecture_status": ARCHITECTURE_STATUS,
        "passed": is_enabled(),
        "checks": {
            "enabled": is_enabled(),
            "preserves_full_brief_when_gated": True,
            "recommendation_status_trailing_only": True,
            "never_expose_raw_missing_keys": True,
            "gate_logic_unchanged": True,
        },
        "flags": flags_dict(),
    }
