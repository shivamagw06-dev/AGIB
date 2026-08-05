"""Writing quality validation — forbidden language and hierarchy completeness."""

from __future__ import annotations

from typing import Any

from institutional_writing_constitution.schema import (
    EVIDENCE_OBSERVATIONS_MIN,
    EVALUATION_DIMENSIONS,
    EXECUTIVE_SUMMARY_MAX_WORDS,
    FORBIDDEN_PHRASES,
    QUALITY_TEST_QUESTIONS,
    QUESTIONS_MIN,
    RESPONSE_HIERARCHY,
)


def _scan_forbidden(text: str) -> list[str]:
    lower = (text or "").lower()
    return [p for p in FORBIDDEN_PHRASES if p in lower]


def _collect_text(pack: dict[str, Any]) -> str:
    parts: list[str] = []
    iwc = pack.get("institutional_writing_constitution") or {}
    sections = iwc.get("sections") or {}
    for key in RESPONSE_HIERARCHY:
        val = sections.get(key)
        if isinstance(val, str):
            parts.append(val)
        elif isinstance(val, dict):
            parts.append(str(val.get("text") or ""))
            parts.extend(str(x) for x in (val.get("bullets") or val.get("observations") or val.get("questions") or []))
            parts.append(str(val.get("current_evidence_indicates") or ""))
    return " ".join(parts)


def validate_writing_response(pack: dict[str, Any]) -> dict[str, Any]:
    """Validate writing constitution compliance."""
    iwc = pack.get("institutional_writing_constitution") or {}
    sections = iwc.get("sections") or {}
    checks: list[dict[str, Any]] = []

    for key in RESPONSE_HIERARCHY:
        checks.append({
            "rule": f"section_present:{key}",
            "passed": key in sections and bool(sections[key]),
            "detail": f"{key} present" if sections.get(key) else f"Missing {key}",
        })

    exec_sec = sections.get("executive_summary") or {}
    wc = exec_sec.get("word_count") or 0
    checks.append({
        "rule": "executive_summary_length",
        "passed": wc <= EXECUTIVE_SUMMARY_MAX_WORDS,
        "detail": f"Executive summary {wc}/{EXECUTIVE_SUMMARY_MAX_WORDS} words",
    })

    evidence = sections.get("what_evidence_suggests") or {}
    obs = evidence.get("observations") or []
    checks.append({
        "rule": "evidence_observations",
        "passed": len(obs) >= min(EVIDENCE_OBSERVATIONS_MIN, 1),
        "detail": f"{len(obs)} evidence observations",
    })

    qsec = sections.get("questions_before_you_decide") or {}
    qs = qsec.get("questions") or pack.get("questions_before_you_decide") or []
    checks.append({
        "rule": "questions_before_you_decide",
        "passed": len(qs) >= QUESTIONS_MIN,
        "detail": f"{len(qs)} decision questions",
    })

    forbidden = _scan_forbidden(_collect_text(pack))
    checks.append({
        "rule": "no_forbidden_language",
        "passed": len(forbidden) == 0,
        "detail": f"Forbidden: {forbidden}" if forbidden else "Institutional tone preserved",
    })

    rc = sections.get("research_conclusion") or {}
    checks.append({
        "rule": "research_conclusion_not_recommendation",
        "passed": rc.get("never_recommends") is True and rc.get("user_decides") is True,
        "detail": "Research conclusion — not investment instruction",
    })

    passed = sum(1 for c in checks if c["passed"])
    return {
        "constitution": "1.0",
        "passed": passed == len(checks),
        "checks_passed": passed,
        "checks_total": len(checks),
        "checks": checks,
        "forbidden_hits": forbidden,
        "quality_test_questions": list(QUALITY_TEST_QUESTIONS),
        "evaluation_dimensions": list(EVALUATION_DIMENSIONS),
    }
