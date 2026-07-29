"""Part C — Institutional question battery (not only 'Should I buy?')."""

from __future__ import annotations

from typing import Any

QUESTION_BATTERY: tuple[dict[str, Any], ...] = (
    {
        "id": "TEST_1",
        "prompt": "Can I buy this company today?",
        "intent": "recommendation_timing",
        "expects_gate": True,
    },
    {
        "id": "TEST_2",
        "prompt": "Is this suitable for a long-term institutional portfolio?",
        "intent": "portfolio_suitability",
        "expects_gate": True,
    },
    {
        "id": "TEST_3",
        "prompt": "What is the investment thesis?",
        "intent": "thesis",
        "expects_gate": False,
    },
    {
        "id": "TEST_4",
        "prompt": "What evidence prevents a recommendation?",
        "intent": "missing_evidence",
        "expects_gate": True,
    },
    {
        "id": "TEST_5",
        "prompt": "What would change your view?",
        "intent": "view_change_catalysts",
        "expects_gate": False,
    },
    {
        "id": "TEST_6",
        "prompt": "Why is the gate failing?",
        "intent": "gate_diagnostics",
        "expects_gate": True,
        "note": "Applicable when Institutional Readiness Gate status is FAILED; else record N/A with reason.",
    },
)


def question_board() -> dict[str, Any]:
    return {
        "part": "C",
        "title": "Institutional questions",
        "n": len(QUESTION_BATTERY),
        "questions": list(QUESTION_BATTERY),
        "rule": "Do not ask only 'Should I buy?' — use the full institutional battery.",
    }
