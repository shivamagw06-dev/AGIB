"""Golden-universe evaluation constants — IEL company-level runner."""

from __future__ import annotations

GOLDEN_EVAL_VERSION = "iel-golden-eval-v1.0.0"
SUITE_ID = "phase1_golden_200"
PROGRAMME = "AGIB_INSTITUTIONAL_EVALUATION_LAB_GOLDEN"

# Governance floors (aligned with readiness gate philosophy)
HIGH_CONVICTION_READINESS_FLOOR = 80.0
HIGH_CONVICTION_BANDS = frozenset({"high_conviction_allowed"})
CONSTRUCTIVE_DECISIONS = frozenset(
    {"constructive", "accumulate", "high conviction", "high_conviction", "buy_biased"}
)

DRIFT_CLASSES = (
    "expected_new_evidence",
    "expected_algorithm_improvement",
    "unexpected_possible_regression",
    "no_change",
)

EVIDENCE_BUCKETS = ("Complete", "Partial", "Insufficient")
