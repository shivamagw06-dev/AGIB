"""Soft adapter — Evidence Producers may consume KF validated outputs only."""

from __future__ import annotations

from typing import Any


def historical_points_from_kf(entity: str, metric: str) -> tuple[dict[str, float] | None, str, str, dict[str, Any]]:
    """Preferred soft source for institutional_evidence.historical.

    Returns (points, provider, data_class, derivation_meta) or empty.
    """
    try:
        from knowledge_factory.store import repository as store

        obj = store.get_object("company", entity)
        if not obj:
            return None, "", "", {}
        metrics = ((obj.get("historical_valuation") or {}).get("metrics") or {})
        row = metrics.get(metric) or {}
        points = row.get("points") or {}
        if not points:
            return None, "", "", {}
        return (
            {str(k): float(v) for k, v in points.items()},
            "knowledge_factory",
            "derived",
            {
                "formula": row.get("formula"),
                "derived_from": row.get("derived_from"),
                "rejected_periods": row.get("rejected_periods"),
                "reproducible": True,
                "raw_api": False,
            },
        )
    except Exception:
        return None, "", "", {}


def risk_from_kf(entity: str) -> dict[str, Any] | None:
    try:
        from knowledge_factory.store import repository as store

        obj = store.get_object("company", entity)
        if not obj:
            return None
        risk = obj.get("risk") or {}
        if not risk.get("found"):
            return None
        return risk
    except Exception:
        return None
