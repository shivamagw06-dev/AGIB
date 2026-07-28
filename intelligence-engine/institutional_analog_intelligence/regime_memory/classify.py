"""Classify question/context into regime tags for analog search."""

from __future__ import annotations

import re
from typing import Any


_RULES: list[tuple[str, str]] = [
    ("rate cut", "rate_cutting_cycle"),
    ("repo cut", "rate_cutting_cycle"),
    ("easing", "rate_cutting_cycle"),
    ("rate hike", "rate_hiking_cycle"),
    ("repo hike", "rate_hiking_cycle"),
    ("tightening", "liquidity_tightening"),
    ("inflation", "high_inflation"),
    ("stagflation", "high_inflation"),
    ("covid", "pandemic"),
    ("pandemic", "pandemic"),
    ("lockdown", "pandemic"),
    ("oil spike", "oil_spike"),
    ("crude", "oil_spike"),  # refined below
    ("oil fall", "oil_collapse"),
    ("oil prices fall", "oil_collapse"),
    ("fall by 25%", "oil_collapse"),
    ("rupee", "fx_depreciation"),
    ("currency", "fx_depreciation"),
    ("liquidity", "liquidity_tightening"),
    ("nbfc", "credit_stress"),
    ("gst", "fiscal_expansion"),
    ("budget", "fiscal_expansion"),
    ("capex", "fiscal_expansion"),
    ("pli", "fiscal_expansion"),
    ("import duty", "import_shock"),
    ("recovery", "recovery"),
    ("slowdown", "demand_slowdown"),
]


def classify_regimes(
    *,
    question: str,
    evidence_graph: dict[str, Any] | None = None,
    playbook_id: str | None = None,
) -> list[str]:
    low = (question or "").lower()
    out: list[str] = []
    for cue, regime in _RULES:
        if " " in cue:
            hit = cue in low
        else:
            hit = re.search(rf"(?<![a-z0-9]){re.escape(cue)}(?![a-z0-9])", low) is not None
        if hit and regime not in out:
            out.append(regime)

    # Oil direction disambiguation
    if "crude" in low or "oil" in low:
        if any(k in low for k in ("fall", "falls", "collapse", "drop", "down")):
            if "oil_collapse" not in out:
                out.append("oil_collapse")
            out = [r for r in out if r != "oil_spike"]
        elif any(k in low for k in ("rise", "spike", "surge", "up")):
            if "oil_spike" not in out:
                out.append("oil_spike")

    pb = (playbook_id or "").lower()
    if "rate" in pb and "rate_cutting_cycle" not in out and "cut" in low:
        out.append("rate_cutting_cycle")
    if "inflation" in pb and "high_inflation" not in out:
        out.append("high_inflation")

    # Evidence graph entity hints
    for ent in (evidence_graph or {}).get("entities") or []:
        e = str(ent).lower()
        if e == "crude_oil" and "oil_collapse" not in out and "oil_spike" not in out:
            out.append("oil_spike")
        if e == "interest_rates" and "rate_cutting_cycle" not in out and "cut" in low:
            out.append("rate_cutting_cycle")

    return out[:8]
