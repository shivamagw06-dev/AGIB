"""Release observability — presentation only. No engine / governance changes."""

from __future__ import annotations

OBSERVABILITY_VERSION = "release-observability-v1.0.0"
PROGRAMME = "AGIB_RELEASE_OBSERVABILITY"

# Explicit freeze: this module must not alter decision/governance logic.
SCOPE_LOCKS = {
    "decision_engine": "read_only",
    "constitution": "read_only",
    "governance_spec": "read_only",
    "scoring": "read_only",
    "weights": "read_only",
    "reasoning": "read_only",
    "valuation_models": "read_only",
    "technical_models": "read_only",
    "presentation_only": True,
}

DECISION_BUCKETS = (
    "High Conviction",
    "Constructive",
    "Neutral",
    "Watchlist",
    "Deferred",
    "Inconclusive",
    "Cautious",
    "Other",
)
