"""Internal response templates — used when Gemini fails. Never fail the request."""

from __future__ import annotations

from typing import Any


def _join(items: list[str], limit: int = 3) -> str:
    clean = [str(x).strip().rstrip(".") for x in items if str(x).strip()]
    return "; ".join(clean[:limit]) if clean else ""


def template_recommendation(structured: dict[str, Any]) -> str:
    reco = str(structured.get("recommendation") or "Hold").strip()
    conviction = str(structured.get("conviction") or "").strip()
    reasons = structured.get("top_reasons") if isinstance(structured.get("top_reasons"), list) else []
    risks = structured.get("top_risks") if isinstance(structured.get("top_risks"), list) else []
    horizon = str(structured.get("investment_horizon") or "Medium Term").strip()
    head = f"Recommendation: {reco}"
    if conviction:
        head += f" ({conviction})"
    reason = _join([str(r) for r in reasons], 2) or "AGIB structured evidence supports this ownership stance."
    risk = _join([str(r) for r in risks], 1) or "Evidence gaps and execution risk remain material."
    return f"{head}\n\n{reason}. Risk: {risk}. Investment Horizon: {horizon}."


def template_quick_analysis(structured: dict[str, Any]) -> str:
    reco = str(structured.get("recommendation") or "Hold").strip()
    bq = structured.get("business_quality") or "Assessed"
    fq = structured.get("financial_quality") or "Assessed"
    val = structured.get("valuation") or "Assessed"
    reasons = _join(list(structured.get("top_reasons") or []), 2)
    risks = _join(list(structured.get("top_risks") or []), 1)
    horizon = structured.get("investment_horizon") or "Medium Term"
    body = (
        f"Recommendation: {reco}. Business quality {bq}; financial quality {fq}; valuation {val}."
    )
    if reasons:
        body += f" Drivers: {reasons}."
    if risks:
        body += f" Key risk: {risks}."
    body += f" Horizon: {horizon}."
    return body


def template_detailed_analysis(structured: dict[str, Any]) -> str:
    quick = template_quick_analysis(structured)
    company = structured.get("company") or "The issuer"
    reasons = _join(list(structured.get("top_reasons") or []), 3)
    risks = _join(list(structured.get("top_risks") or []), 2)
    extra = f" {company}: {reasons}." if reasons else ""
    if risks:
        extra += f" Monitor {risks}."
    return f"{quick}{extra}".strip()


def render_template(mode: str, structured: dict[str, Any]) -> str:
    if mode == "detailed_analysis":
        return template_detailed_analysis(structured)
    if mode == "quick_analysis":
        return template_quick_analysis(structured)
    return template_recommendation(structured)
