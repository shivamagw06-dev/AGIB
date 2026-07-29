"""Baseline v1.0 IAT Protocol — Parts A–G (machine-readable)."""

from __future__ import annotations

from typing import Any

from institutional_evaluation_lab.iat.company_types import evaluate_company_types
from institutional_evaluation_lab.iat.questions import question_board
from institutional_evaluation_lab.iat.schema import (
    ARCHITECTURE_VERSION,
    BASELINE_NAME,
    IAT_VERSION,
    PROGRAMME,
    REQUIRED_BUCKETS,
    REQUIRED_UNIVERSE_N,
)

PROTOCOL_VERSION = "iat-baseline-protocol-v1.0.0"

# Part D — per-company evaluation dimensions
EVALUATION_DIMENSIONS: tuple[str, ...] = (
    "Business Quality",
    "Financial Quality",
    "Management",
    "Valuation",
    "Macro",
    "Ownership",
    "Technical",
    "Risk",
    "Opportunity",
    "Readiness",
    "Confidence",
)

DIMENSION_FIELDS = {
    "Business Quality": ["company_quality"],
    "Financial Quality": ["financial_quality"],
    "Management": ["management", "management_quality"],
    "Valuation": ["valuation"],
    "Macro": ["macro"],
    "Ownership": ["ownership", "ownership_quality", "institutional_readiness"],
    "Technical": ["technical"],
    "Risk": ["risk"],
    "Opportunity": ["investment_opportunity", "market_opportunity"],
    "Readiness": ["recommendation_readiness", "institutional_readiness"],
    "Confidence": ["analytical_confidence", "recommendation_readiness"],
}

# Part E — governance checklist
GOVERNANCE_CHECKS: tuple[dict[str, str], ...] = (
    {"id": "CONSTITUTION", "label": "Constitution"},
    {"id": "GOV-001", "label": "GOV-001"},
    {"id": "GOV-002", "label": "GOV-002"},
    {"id": "GOV-003", "label": "GOV-003"},
    {"id": "GOV-004", "label": "GOV-004"},
    {"id": "GOV-005", "label": "GOV-005"},
    {"id": "GOV-006", "label": "GOV-006"},
    {"id": "GOV-007", "label": "GOV-007"},
    {"id": "GOV-008", "label": "GOV-008"},
)

# Part F — operational metrics
OPERATIONAL_METRICS: tuple[str, ...] = (
    "Runtime",
    "Memory",
    "Coverage",
    "Freshness",
    "Replay",
    "Determinism",
)

# Part G — human review rubric (not automated PASS/FAIL)
HUMAN_REVIEW_QUESTIONS: tuple[str, ...] = (
    "Did the analysis actually help?",
    "Was the thesis logical?",
    "Was the reasoning coherent?",
    "Were risks identified?",
    "Were missing evidence items correct?",
    "Was valuation sensible?",
)

HUMAN_REVIEW_SCALE = ("Helpful", "Partial", "Not helpful")


def part_a_coverage() -> dict[str, Any]:
    from knowledge_factory.phase1_golden_test_set import summary as golden_summary

    g = golden_summary()
    buckets = g.get("bucket_counts") or {}
    mismatches = []
    for k, need in REQUIRED_BUCKETS.items():
        got = int(buckets.get(k, 0))
        if got != need:
            mismatches.append({"bucket": k, "expected": need, "actual": got})
    n = int(g.get("n") or 0)
    return {
        "part": "A",
        "title": "Company Coverage",
        "universe": [
            {"label": "Nifty 50", "count": 50, "bucket": "nifty_50"},
            {"label": "Nifty Next 50", "count": 50, "bucket": "nifty_next_50"},
            {"label": "Midcap 150 (sample)", "count": 50, "bucket": "midcap"},
            {"label": "Smallcap 250 (sample)", "count": 25, "bucket": "smallcap"},
            {"label": "Special situations", "count": 25, "bucket": "special_situation"},
        ],
        "total": REQUIRED_UNIVERSE_N,
        "actual_n": n,
        "bucket_counts": buckets,
        "frozen": bool(g.get("frozen")),
        "composition_sha256": g.get("composition_sha256"),
        "mismatches": mismatches,
        "status": "PASS" if n == REQUIRED_UNIVERSE_N and not mismatches else "FAIL",
    }


def part_d_dimensions() -> dict[str, Any]:
    return {
        "part": "D",
        "title": "Evaluation dimensions",
        "dimensions": list(EVALUATION_DIMENSIONS),
        "fields": dict(DIMENSION_FIELDS),
        "rule": (
            "Business Quality, Opportunity, Readiness, and Confidence are distinct "
            "and must not be conflated."
        ),
    }


def part_e_governance() -> dict[str, Any]:
    return {
        "part": "E",
        "title": "Governance",
        "checks": list(GOVERNANCE_CHECKS),
        "rule": "Critical GOV failures must be 0 for baseline qualification.",
    }


def part_f_operational() -> dict[str, Any]:
    return {
        "part": "F",
        "title": "Operational",
        "metrics": list(OPERATIONAL_METRICS),
    }


def part_g_human_review() -> dict[str, Any]:
    return {
        "part": "G",
        "title": "Did the analysis actually help?",
        "automated": False,
        "questions": list(HUMAN_REVIEW_QUESTIONS),
        "scale": list(HUMAN_REVIEW_SCALE),
        "sampling_rule": (
            "Stratified sample: ≥1 company per Part B type, minimum 20 names. "
            "Human review required for institutional sign-off; not a sole freeze gate."
        ),
        "note": "These require human review rather than automated PASS/FAIL.",
    }


def protocol_pack() -> dict[str, Any]:
    """Full Baseline v1.0 IAT protocol declaration."""
    a = part_a_coverage()
    b = evaluate_company_types()
    return {
        "protocol_version": PROTOCOL_VERSION,
        "iat_version": IAT_VERSION,
        "programme": PROGRAMME,
        "baseline": BASELINE_NAME,
        "architecture_version": ARCHITECTURE_VERSION,
        "objective": "Determine whether AGIB today performs like an institutional research platform.",
        "parts": {
            "A": a,
            "B": b,
            "C": question_board(),
            "D": part_d_dimensions(),
            "E": part_e_governance(),
            "F": part_f_operational(),
            "G": part_g_human_review(),
        },
        "automated_parts": ["A", "B", "C", "D", "E", "F"],
        "human_parts": ["G"],
        "certification_rule": (
            "Automated Parts A–F PASS + Part G human review completed + UNKNOWN drift = 0 "
            "⇒ eligible for Baseline freeze / re-affirmation."
        ),
        "doc": "docs/AGIB_IAT_BASELINE_V1_PROTOCOL.md",
        "status": {
            "A": a.get("status"),
            "B": b.get("status"),
            "C": "DEFINED",
            "D": "DEFINED",
            "E": "DEFINED",
            "F": "DEFINED",
            "G": "HUMAN_REVIEW",
        },
    }


def format_protocol_text(pack: dict[str, Any] | None = None) -> str:
    pack = pack or protocol_pack()
    parts = pack.get("parts") or {}
    a = parts.get("A") or {}
    b = parts.get("B") or {}
    c = parts.get("C") or {}
    g = parts.get("G") or {}
    lines = [
        "==========================================================",
        "AGIB Institutional Acceptance Test — Baseline v1.0 Protocol",
        "==========================================================",
        "",
        f"Objective",
        "",
        f"{pack.get('objective')}",
        "",
        f"Baseline  {pack.get('baseline')}",
        f"Protocol  {pack.get('protocol_version')}",
        "",
        "----------------------------------------------------------",
        "Part A — Company Coverage",
        "----------------------------------------------------------",
        f"Status: {a.get('status')}  n={a.get('actual_n')}/{a.get('total')}",
        "",
    ]
    for u in a.get("universe") or []:
        lines.append(f"  {u.get('label'):<28} {u.get('count')}")
    lines += [
        "",
        "----------------------------------------------------------",
        "Part B — Company Types",
        "----------------------------------------------------------",
        f"Status: {b.get('status')}  {b.get('n_types_present')}/{b.get('n_types_required')} types present",
        "",
    ]
    cov = b.get("coverage") or {}
    labels = b.get("labels") or {}
    for tid in b.get("required") or []:
        n = (cov.get(tid) or {}).get("n", 0)
        ex = ", ".join((cov.get(tid) or {}).get("examples") or [])
        mark = "✓" if n else "✗"
        lines.append(f"  {mark} {labels.get(tid, tid):<28} n={n}  {ex}")
    if b.get("missing"):
        lines.append(f"  Missing: {', '.join(b['missing'])}")
    lines += [
        "",
        "----------------------------------------------------------",
        "Part C — Questions",
        "----------------------------------------------------------",
        "",
    ]
    for q in c.get("questions") or []:
        lines.append(f"  {q.get('id')}  {q.get('prompt')}")
    lines += [
        "",
        "----------------------------------------------------------",
        "Part D — Evaluation dimensions",
        "----------------------------------------------------------",
        "",
        "  " + ", ".join((parts.get("D") or {}).get("dimensions") or []),
        "",
        "----------------------------------------------------------",
        "Part E — Governance",
        "----------------------------------------------------------",
        "",
    ]
    for chk in (parts.get("E") or {}).get("checks") or []:
        lines.append(f"  ✓ {chk.get('label')}")
    lines += [
        "",
        "----------------------------------------------------------",
        "Part F — Operational",
        "----------------------------------------------------------",
        "",
        "  " + ", ".join((parts.get("F") or {}).get("metrics") or []),
        "",
        "----------------------------------------------------------",
        "Part G — Human review (not automated PASS/FAIL)",
        "----------------------------------------------------------",
        "",
        f"  {(g.get('sampling_rule') or '')}",
        "",
    ]
    for hq in g.get("questions") or []:
        lines.append(f"  • {hq}")
    lines += [
        "",
        "Scale: " + " / ".join(g.get("scale") or []),
        "",
        "----------------------------------------------------------",
        "Certification rule",
        "----------------------------------------------------------",
        "",
        str(pack.get("certification_rule")),
        "",
        "==========================================================",
    ]
    return "\n".join(lines)


def build_protocol_report_for_release(release_id: str, *, iat_pack: dict[str, Any] | None = None) -> dict[str, Any]:
    """Merge protocol declaration with an automated IAT run (if provided)."""
    proto = protocol_pack()
    overall_auto = None
    if iat_pack and iat_pack.get("found"):
        overall_auto = (iat_pack.get("overall") or {}).get("status")
    return {
        **proto,
        "release_id": release_id,
        "automated_iat_status": overall_auto,
        "part_g_workbook": {
            "instructions": (
                "Complete human review for a stratified sample (≥20 names, ≥1 per Part B type). "
                "Record Helpful / Partial / Not helpful per question."
            ),
            "questions": list(HUMAN_REVIEW_QUESTIONS),
            "scale": list(HUMAN_REVIEW_SCALE),
            "rows_template": [
                {
                    "ticker": None,
                    "company_type": None,
                    "scores": {q: None for q in HUMAN_REVIEW_QUESTIONS},
                    "notes": "",
                }
            ],
        },
        "report_text": format_protocol_text(proto),
    }
