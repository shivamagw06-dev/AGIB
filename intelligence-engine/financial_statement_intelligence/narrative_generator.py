"""Analyst Narrative Generator — Module 12.

Turns computed deltas + rule-library findings into professional,
evidence-grounded prose:

    "Revenue increased 18%, driven primarily by ... Gross margins
    expanded 220 basis points ... allowing EBITDA to outpace revenue
    growth."

Every clause in the output traces to a specific computed number or a
finding from ``rule_library`` — nothing is invented. When a detail (like
a named driver: pricing vs volume) isn't available from the input data,
the narrative states the direction and magnitude only, rather than
fabricating a cause.
"""

from __future__ import annotations

from typing import Any, Optional

from financial_statement_intelligence.deltas import compute_deltas
from financial_statement_intelligence.rule_library import Finding, evaluate_rules
from financial_statement_intelligence.schema import FinancialSeries, StatementPeriod


def _bps(delta: Optional[float]) -> Optional[float]:
    return round(delta * 10000, 0) if delta is not None else None


def _find(findings: list[Finding], *rule_id_prefixes: str) -> Optional[Finding]:
    for f in findings:
        if any(f.rule_id.startswith(p) for p in rule_id_prefixes):
            return f
    return None


def _revenue_sentence(prior: StatementPeriod, current: StatementPeriod, drivers: Optional[dict]) -> tuple[str, list[str]]:
    from financial_statement_intelligence.deltas import compute_deltas as _cd

    d = _cd(prior, current)
    rev_pct = d.pct("revenue")
    if rev_pct is None:
        return "Revenue for the period is not comparable to the prior period.", []
    direction = "increased" if rev_pct >= 0 else "declined"
    sentence = f"Revenue {direction} {abs(rev_pct) * 100:.1f}%"
    evidence = [f"revenue: {prior.revenue:,.0f} → {current.revenue:,.0f}"]
    if drivers and (drivers.get("volume_growth") is not None or drivers.get("pricing_growth") is not None):
        parts = []
        if drivers.get("pricing_growth") is not None:
            parts.append(f"higher realisation ({drivers['pricing_growth'] * 100:+.1f}%)")
        if drivers.get("volume_growth") is not None:
            parts.append(f"volume growth ({drivers['volume_growth'] * 100:+.1f}%)")
        sentence += f", driven primarily by {' and '.join(parts)}"
        evidence.append("driver breakdown supplied by caller")
    sentence += "."
    return sentence, evidence


_MARGIN_LEADIN_STRIP = (
    "implies gross margin expansion — ",
    "implies gross margin compression — ",
)


def _margin_sentence(findings: list[Finding], prior: StatementPeriod, current: StatementPeriod) -> tuple[str, list[str]]:
    d = compute_deltas(prior, current)
    gm = d.get("ratio_gross_margin")
    if gm is None or gm.abs_change is None:
        return "", []
    bps = _bps(gm.abs_change)
    direction = "expanded" if bps >= 0 else "contracted"
    sentence = f"Gross margins {direction} {abs(bps):.0f} basis points"
    evidence = [f"gross margin: {gm.prior * 100:.1f}% → {gm.current * 100:.1f}%"]
    gp_finding = _find(findings, "gross_profit_vs_cogs", "revenue_vs_gross_profit")
    if gp_finding:
        # Reuse the rule's own grounded explanation as the driver clause, never inventing a new one.
        clause = gp_finding.explanation.split("—", 1)[-1].strip().rstrip(".")
        for lead_in in _MARGIN_LEADIN_STRIP:
            if clause.startswith(lead_in):
                clause = clause[len(lead_in):]
                break
        sentence += f" — {clause}"
        evidence.append(gp_finding.explanation)
    sentence += "."
    return sentence, evidence


def _profitability_sentence(findings: list[Finding]) -> tuple[str, list[str]]:
    leverage_finding = _find(findings, "revenue_vs_ebitda", "gross_profit_vs_opex", "opex_vs_revenue")
    if not leverage_finding:
        return "", []
    clause = leverage_finding.explanation
    return clause, [clause]


def _cash_flow_sentence(findings: list[Finding], prior: StatementPeriod, current: StatementPeriod) -> tuple[str, list[str]]:
    pat_ocf = _find(findings, "pat_vs_operating_cf")
    if pat_ocf:
        return pat_ocf.explanation, [pat_ocf.explanation]
    fcf = current.free_cash_flow
    if fcf < 0:
        sentence = f"Free Cash Flow was negative at {fcf:,.0f} for the period."
        return sentence, [sentence]
    return "", []


def _leverage_sentence(findings: list[Finding]) -> tuple[str, list[str]]:
    lev = _find(findings, "debt_vs_ebitda", "cash_vs_total_debt", "interest_vs_ebit")
    if not lev:
        return "", []
    return lev.explanation, [lev.explanation]


def generate_narrative(
    series: FinancialSeries, *, drivers: Optional[dict[str, float]] = None
) -> dict[str, Any]:
    """Module 12: analyst-quality narrative for the latest period, fully
    evidence-grounded. ``drivers`` optionally supplies pricing/volume
    breakdown when the caller has it — the narrative never fabricates one."""
    prior, current = series.pair(lag=1)
    if prior is None or current is None:
        return {"available": False, "reason": "Need at least two periods for a narrative."}

    deltas = compute_deltas(prior, current)
    findings = evaluate_rules(deltas)

    sentences: list[str] = []
    evidence: list[str] = []

    for sentence, ev in (
        _revenue_sentence(prior, current, drivers),
        _margin_sentence(findings, prior, current),
        _profitability_sentence(findings),
        _cash_flow_sentence(findings, prior, current),
        _leverage_sentence(findings),
    ):
        if sentence:
            sentences.append(sentence)
            evidence.extend(ev)

    narrative = " ".join(sentences) if sentences else (
        f"{series.company}'s {current.label} results show no material period-over-period change "
        f"in the metrics tracked."
    )
    return {
        "available": True,
        "company": series.company,
        "period": current.label,
        "narrative": narrative,
        "sentence_count": len(sentences),
        "evidence": evidence,
        "underlying_findings": [f.rule_id for f in findings],
    }
