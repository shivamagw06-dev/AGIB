"""Business Analyst quality checks before Investment Committee handoff."""

from __future__ import annotations

from typing import Any, Dict, List


def check_contradictions(strengths: List[str], weaknesses: List[str]) -> List[str]:
    issues: List[str] = []
    s_set = {s.lower().strip() for s in strengths if s}
    for w in weaknesses:
        if w and w.lower().strip() in s_set:
            issues.append(f"Contradiction: '{w}' listed as both strength and weakness")
    return issues


def check_missing_evidence(claims: List[str], evidence: List[Dict[str, Any]]) -> List[str]:
    if claims and not evidence:
        return ["Missing evidence for business claims"]
    return []


def check_outdated_information(freshness: float) -> List[str]:
    if float(freshness or 0.0) < 0.45:
        return ["Outdated information risk: freshness below institutional threshold"]
    return []


def check_low_confidence(overall: float) -> List[str]:
    if float(overall or 0.0) < 0.4:
        return ["Low overall confidence — flag for committee challenge"]
    return []


def check_weak_assumptions(assumptions: List[str], evidence_count: int) -> List[str]:
    issues: List[str] = []
    if len(assumptions) >= 3 and evidence_count < 2:
        issues.append("Weak assumptions: multiple assumptions with thin evidence base")
    return issues


def check_incomplete_coverage(
    *,
    moat_assessment: Dict[str, Any],
    competitive_outlook: Dict[str, Any],
    business_quality: Dict[str, Any],
) -> List[str]:
    issues: List[str] = []
    if not (moat_assessment or {}).get("summary"):
        issues.append("Incomplete coverage: moat assessment summary missing")
    if not (competitive_outlook or {}).get("summary"):
        issues.append("Incomplete coverage: competitive outlook summary missing")
    if not (business_quality or {}).get("grade"):
        issues.append("Incomplete coverage: business quality grade missing")
    return issues


def run_quality_checks(
    *,
    strengths: List[str],
    weaknesses: List[str],
    claims: List[str],
    evidence: List[Dict[str, Any]],
    assumptions: List[str],
    freshness: float,
    overall_confidence: float,
    moat_assessment: Dict[str, Any],
    competitive_outlook: Dict[str, Any],
    business_quality: Dict[str, Any],
) -> Dict[str, Any]:
    issues: List[str] = []
    issues.extend(check_contradictions(strengths, weaknesses))
    issues.extend(check_missing_evidence(claims, evidence))
    issues.extend(check_outdated_information(freshness))
    issues.extend(check_low_confidence(overall_confidence))
    issues.extend(check_weak_assumptions(assumptions, len(evidence)))
    issues.extend(
        check_incomplete_coverage(
            moat_assessment=moat_assessment,
            competitive_outlook=competitive_outlook,
            business_quality=business_quality,
        )
    )
    return {
        "passed": len(issues) == 0,
        "issues": issues,
        "issue_count": len(issues),
        "ready_for_committee": len([i for i in issues if "Low overall" not in i]) <= 2,
    }
