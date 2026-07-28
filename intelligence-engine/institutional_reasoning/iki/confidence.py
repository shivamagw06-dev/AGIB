"""Framework Confidence Calibration.

Initially IES/benchmark-driven. Later evolves with live outcomes (Phase 7+).
"""

from __future__ import annotations

from typing import Any

CALIBRATION_VERSION = "framework-confidence-v1.0.0"

# Seed profiles — IES accuracy placeholders until continuous learning lands.
_PROFILES: dict[str, dict[str, Any]] = {
    "rel_val_damodaran": {"ies_accuracy": 97.0, "live_success": None, "band": "High"},
    "hist_multiples": {"ies_accuracy": 96.0, "live_success": None, "band": "High"},
    "margin_of_safety": {"ies_accuracy": 88.0, "live_success": None, "band": "Medium"},
    "dcf_applicability": {"ies_accuracy": 99.0, "live_success": None, "band": "High"},
    "dcf_fcff": {"ies_accuracy": 91.0, "live_success": 68.0, "band": "Medium"},
    "residual_income": {"ies_accuracy": 93.0, "live_success": None, "band": "High"},
    "peer_comparison": {"ies_accuracy": 94.0, "live_success": None, "band": "High"},
    "business_quality_roic": {"ies_accuracy": 92.0, "live_success": None, "band": "High"},
    "buffett_quality": {"ies_accuracy": 90.0, "live_success": None, "band": "High"},
    "accounting_quality_screen": {"ies_accuracy": 89.0, "live_success": None, "band": "Medium"},
    "graham_net_net": {"ies_accuracy": 84.0, "live_success": None, "band": "Medium"},
}


def _band(ies: float, live: float | None) -> str:
    score = ies if live is None else (0.7 * ies + 0.3 * live)
    if score >= 93:
        return "High"
    if score >= 85:
        return "Medium"
    return "Low"


def confidence_for(framework_id: str) -> dict[str, Any]:
    p = _PROFILES.get(framework_id) or {"ies_accuracy": 80.0, "live_success": None, "band": "Medium"}
    ies = float(p.get("ies_accuracy") or 80.0)
    live = p.get("live_success")
    live_f = float(live) if live is not None else None
    return {
        "framework_id": framework_id,
        "ies_accuracy": ies,
        "live_success": live_f,
        "band": _band(ies, live_f),
        "weight_multiplier": round(ies / 100.0, 3),
        "calibration_version": CALIBRATION_VERSION,
        "note": "Live success reserved for continuous learning phases.",
    }


def all_profiles() -> dict[str, Any]:
    return {
        "calibration_version": CALIBRATION_VERSION,
        "profiles": {fid: confidence_for(fid) for fid in _PROFILES},
    }
