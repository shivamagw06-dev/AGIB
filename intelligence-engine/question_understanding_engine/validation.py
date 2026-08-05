"""QUE quality gates and validation."""

from __future__ import annotations

from typing import Any

REQUIRED_FIELDS: tuple[str, ...] = (
    "literal_question",
    "investor_meaning",
    "decision_type",
    "research_objective",
    "primary_investment_question",
    "response_objective",
    "expected_deliverable",
)


def validate_understanding(qu: dict[str, Any]) -> dict[str, Any]:
    """QUE fails if any required field is missing."""
    missing = [f for f in REQUIRED_FIELDS if not qu.get(f)]
    checks = {f: bool(qu.get(f)) for f in REQUIRED_FIELDS}
    checks["decision_not_unknown"] = qu.get("decision_type") not in (None, "", "Unknown")
    checks["confidence_gt_zero"] = (qu.get("confidence") or 0) > 0
    return {
        "passed": len(missing) == 0 and checks["confidence_gt_zero"],
        "missing_fields": missing,
        "checks": checks,
    }
