"""Feature flags for Continuous Gather → Learn (Ask-safe)."""

from __future__ import annotations

import os


def _truthy(name: str, default: str = "false") -> bool:
    return str(os.getenv(name, default)).strip().lower() in {"1", "true", "yes", "on"}


def is_enabled() -> bool:
    """Master switch — background loop + ops APIs."""
    return _truthy("CONTINUOUS_GATHER_LEARN", "true")


def morning_dag_enabled() -> bool:
    return is_enabled() and _truthy("CONTINUOUS_MORNING_DAG", "true")


def lidi_enabled() -> bool:
    return is_enabled() and _truthy("CONTINUOUS_LIDI", "true")


def kf_hd_enabled() -> bool:
    return is_enabled() and _truthy("CONTINUOUS_KF_HD", "true")


def faa_in_loop_enabled() -> bool:
    """Optional FAA refresh inside CGL post-market phase (independent of Ask)."""
    return is_enabled() and _truthy("CONTINUOUS_FAA_REFRESH", "true")


def learning_loop_enabled() -> bool:
    return is_enabled() and _truthy("CONTINUOUS_LEARNING_LOOP", "true")


def director_learning_inject() -> bool:
    return _truthy("CONTINUOUS_DIRECTOR_LEARNING", "true")


def interval_sec() -> float:
    try:
        return max(120.0, float(os.getenv("CONTINUOUS_GATHER_LEARN_INTERVAL_SEC") or "1800"))
    except ValueError:
        return 1800.0


def flags_dict() -> dict[str, bool | float]:
    return {
        "CONTINUOUS_GATHER_LEARN": is_enabled(),
        "CONTINUOUS_MORNING_DAG": morning_dag_enabled(),
        "CONTINUOUS_LIDI": lidi_enabled(),
        "CONTINUOUS_KF_HD": kf_hd_enabled(),
        "CONTINUOUS_FAA_REFRESH": faa_in_loop_enabled(),
        "CONTINUOUS_LEARNING_LOOP": learning_loop_enabled(),
        "CONTINUOUS_DIRECTOR_LEARNING": director_learning_inject(),
        "CONTINUOUS_GATHER_LEARN_INTERVAL_SEC": interval_sec(),
        "FAA_BACKGROUND_COLLECTOR": _truthy("FAA_BACKGROUND_COLLECTOR", "false"),
    }
