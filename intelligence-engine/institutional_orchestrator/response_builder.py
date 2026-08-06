"""UAG-01 response builder — assemble structured answers from retrieved objects."""

from __future__ import annotations

from typing import Any

from institutional_orchestrator.evidence_assembler import assemble_evidence, lineage_for_response
from institutional_orchestrator.models import (
    ExecutionStep,
    InstitutionalQuery,
    InstitutionalResponse,
)


def _value(value: Any, *, decimals: int = 2) -> str:
    try:
        return f"{float(value):,.{decimals}f}"
    except (TypeError, ValueError):
        return "not reported"


def _money(value: Any, row: dict[str, Any]) -> str:
    """Use Indian units only for warehouse rows with verified normalisation."""
    meta = row.get("_meta") if isinstance(row.get("_meta"), dict) else {}
    method = str(meta.get("unit_method") or "").lower()
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return "not reported"
    if "canonical" in method or "normal" in method:
        # Warehouse canonical currency is INR million; 10 million INR = 1 crore.
        return f"₹{amount / 10:,.1f} crore"
    return f"{amount:,.2f} (source units)"


def _comparison_answer(payloads: dict[str, Any]) -> str | None:
    comparison = ((payloads.get("ComparisonEvidence") or {}).get("payload") or {})
    if not comparison.get("available"):
        return None
    lines: list[str] = []
    for company in (comparison.get("companies") or [])[:5]:
        symbol = company.get("symbol") or "Company"
        quarter = company.get("quarter") or {}
        annual = company.get("annual") or {}
        valuation = company.get("valuation") or {}
        period = quarter.get("fiscal_period") or annual.get("fiscal_year") or "latest available period"
        pat = quarter.get("pat") if quarter.get("pat") is not None else annual.get("pat")
        eps = quarter.get("eps") if quarter.get("eps") is not None else annual.get("eps")
        pe = valuation.get("pe") or valuation.get("pe_ratio")
        pb = valuation.get("pb") or valuation.get("pb_ratio")
        sources = ", ".join(company.get("sources") or []) or "institutional warehouse"
        as_of = company.get("as_of") or "not supplied"
        lines.append(
            f"{symbol} ({period}): reported PAT {_money(pat, quarter if quarter.get('pat') is not None else annual)}; EPS {_value(eps)}; "
            f"P/E {_value(pe)}; P/B {_value(pb)}. Source: {sources}; as of {as_of}."
        )
    return "Verified comparison — " + " ".join(lines) + " This is factual research, not an investment recommendation."


def _why_from_objects(payloads: dict[str, Any], intent: str) -> tuple[str, ...]:
    why: list[str] = []

    committee = ((payloads.get("CommitteeResolution") or {}).get("payload") or {}).get("resolution") or {}
    if committee:
        why.append(f"Committee status: {committee.get('status')} — {committee.get('outcome')}")
        for v in (committee.get("votes") or [])[:3]:
            why.append(f"{v.get('desk')} voted {v.get('vote')}: {v.get('rationale')}")

    decision = ((payloads.get("PortfolioDecision") or {}).get("payload") or {}).get("decision") or {}
    if decision:
        why.append(
            f"Portfolio decision: {decision.get('recommendation')} "
            f"(rule: {decision.get('rule_path') or '—'})"
        )
        for a in (decision.get("allocation_actions") or [])[:4]:
            why.append(
                f"Allocation: {a.get('ticker')} "
                f"{float(a.get('from_weight') or 0):.0%} → {float(a.get('to_weight') or 0):.0%}"
            )

    policy = ((payloads.get("PolicyAssessment") or {}).get("payload") or {}).get("assessment") or {}
    if policy:
        why.append(f"Policy status: {policy.get('overall_status')} (score {policy.get('compliance_score')})")
        for v in (policy.get("violations") or [])[:3]:
            why.append(f"Violation: {v.get('name')} — {v.get('required_action')}")

    risk = ((payloads.get("PortfolioRisk") or {}).get("payload") or {}).get("risk") or {}
    if risk:
        conc = risk.get("concentration") or {}
        why.append(
            f"Portfolio risk {risk.get('overall_risk')}: "
            f"concentration {conc.get('level')} HHI={conc.get('hhi')}"
        )

    cd = (payloads.get("CompanyDecision") or {}).get("payload") or {}
    if cd:
        rec = cd.get("recommendation") or (cd.get("decision") or {}).get("recommendation")
        if rec:
            why.append(f"Company decision reference: {cd.get('ticker') or ''} {rec}".strip())
        elif cd.get("note"):
            why.append(str(cd.get("note")))

    if not why:
        why.append(f"Consulted registered objects for intent '{intent}' — see evidence lineage")
    return tuple(why)


def _direct_answer(question: str, intent: str, payloads: dict[str, Any], why: tuple[str, ...]) -> str:
    committee = ((payloads.get("CommitteeResolution") or {}).get("payload") or {}).get("resolution") or {}
    decision = ((payloads.get("PortfolioDecision") or {}).get("payload") or {}).get("decision") or {}
    policy = ((payloads.get("PolicyAssessment") or {}).get("payload") or {}).get("assessment") or {}
    risk = ((payloads.get("PortfolioRisk") or {}).get("payload") or {}).get("risk") or {}

    q = (question or "").lower()

    if intent == "Comparison":
        comparison = _comparison_answer(payloads)
        if comparison:
            return comparison
        return "Verified comparison data is unavailable for every requested company; no conclusion was inferred."

    if intent == "Committee" or committee:
        status = committee.get("status") or "Unavailable"
        outcome = committee.get("outcome") or ""
        rec = committee.get("decision_recommendation") or decision.get("recommendation") or ""
        return (
            f"The investment committee resolved '{status}'. {outcome} "
            f"Referenced portfolio recommendation: {rec or '—'}. "
            "UAG-01 does not invent a new investment recommendation."
        ).strip()

    if intent == "Policy" or ("policy" in q or "violation" in q):
        status = policy.get("overall_status") or "Unavailable"
        n = policy.get("violation_count") or len(policy.get("violations") or [])
        actions = policy.get("required_actions") or []
        action = actions[0] if actions else "No remediation required"
        return f"Policy status is {status} with {n} violation(s). Primary action: {action}."

    if intent == "Risk" or risk:
        return (
            f"Portfolio overall risk is {risk.get('overall_risk') or 'Unavailable'}. "
            f"Concentration: {(risk.get('concentration') or {}).get('level') or '—'}. "
            "Details are sourced from PRE-01; no new risk score was computed by Ask."
        )

    if intent == "Portfolio Analysis" or decision:
        return (
            f"Portfolio recommendation is '{decision.get('recommendation') or 'Unavailable'}' "
            f"with posture {decision.get('investment_posture') or '—'}. "
            "This reflects CIO-01; Universal Ask does not generate portfolio advice."
        )

    if intent == "Company Analysis":
        cd = (payloads.get("CompanyDecision") or {}).get("payload") or {}
        rec = cd.get("recommendation") or (cd.get("decision") or {}).get("recommendation")
        ticker = cd.get("ticker") or ""
        if rec:
            return (
                f"Company decision for {ticker}: {rec}. "
                "Retrieved from the company decision object — not generated by the orchestrator."
            )
        return (
            "Company analysis objects were consulted. "
            "No authoritative company recommendation was available to surface."
        )

    if why:
        return why[0]
    return f"Orchestrated answer for intent '{intent}'. See supporting evidence and lineage."


def _confidence(steps: tuple[ExecutionStep, ...], payloads: dict[str, Any]) -> int:
    if not steps:
        return 0
    ok = sum(1 for s in steps if s.status == "ok")
    base = int(round(100.0 * ok / len(steps)))
    # Bonus when authoritative stack present
    if "PortfolioDecision" in payloads and "PortfolioRisk" in payloads:
        base = min(100, base + 5)
    if "CommitteeResolution" in payloads:
        base = min(100, base + 5)
    return base


def build_response(
    query: InstitutionalQuery,
    *,
    steps: tuple[ExecutionStep, ...],
    payloads: dict[str, Any],
    generated_at: str = "",
) -> InstitutionalResponse:
    evidence = assemble_evidence(payloads)
    lineage = lineage_for_response(payloads)
    why = _why_from_objects(payloads, query.intent)
    answer = _direct_answer(query.question, query.intent, payloads, why)

    risk = ((payloads.get("PortfolioRisk") or {}).get("payload") or {}).get("risk") or {}
    related_risks = tuple(risk.get("warnings") or [])[:6]

    policy = ((payloads.get("PolicyAssessment") or {}).get("payload") or {}).get("assessment") or {}
    related_obs = tuple(policy.get("warnings") or [])[:4]

    committee = ((payloads.get("CommitteeResolution") or {}).get("payload") or {}).get("resolution") or {}
    committee_history = tuple(
        [f"{committee.get('status')}: {committee.get('outcome')}"]
        + list(committee.get("follow_up_items") or [])[:4]
    ) if committee else ()

    impacts: list[str] = []
    decision = ((payloads.get("PortfolioDecision") or {}).get("payload") or {}).get("decision") or {}
    for a in (decision.get("allocation_actions") or [])[:6]:
        impacts.append(
            f"{a.get('ticker')}: {float(a.get('from_weight') or 0):.0%} → "
            f"{float(a.get('to_weight') or 0):.0%}"
        )

    missing = tuple(s.object_type for s in steps if s.status in {"missing", "error"})
    warnings: list[str] = []
    if missing:
        warnings.append(f"Missing/failed objects: {', '.join(missing)}")
    warnings.append("UAG-01 orchestrates only — it does not generate investment recommendations")

    return InstitutionalResponse(
        query_id=query.query_id,
        question=query.question,
        intent=query.intent,
        direct_answer=answer,
        why=why,
        supporting_evidence=evidence,
        related_risks=related_risks,
        related_observations=related_obs,
        committee_history=committee_history,
        related_portfolio_impacts=tuple(impacts),
        confidence=_confidence(steps, payloads),
        evidence_lineage=lineage,
        objects_consulted=tuple(payloads.keys()),
        execution_plan=steps,
        missing_objects=missing,
        warnings=tuple(warnings),
        sections={
            "direct_answer": answer,
            "why": list(why),
            "evidence": [e.to_dict() for e in evidence],
            "lineage": list(lineage),
        },
        diagnostics=None,
        generated_at=generated_at,
        llm=False,
        generates_recommendations=False,
    )
