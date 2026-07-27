"""Internal response templates — neutral rewrite only. Never advice."""

from __future__ import annotations

from typing import Any


def _join(items: list[str], limit: int = 3) -> str:
    clean = [str(x).strip().rstrip(".") for x in items if str(x).strip()]
    return "; ".join(clean[:limit]) if clean else ""


def _evidence_note(structured: dict[str, Any]) -> str:
    reasons = structured.get("top_reasons") if isinstance(structured.get("top_reasons"), list) else []
    risks = structured.get("top_risks") if isinstance(structured.get("top_risks"), list) else []
    if not reasons and not risks:
        return "Available evidence is insufficient for a fuller institutional narrative."
    return ""


def template_quick_summary(structured: dict[str, Any]) -> str:
    bq = structured.get("business_quality")
    fq = structured.get("financial_quality")
    val = structured.get("valuation")
    reasons = _join(list(structured.get("top_reasons") or []), 2)
    risks = _join(list(structured.get("top_risks") or []), 1)
    parts: list[str] = []
    labels = []
    if bq:
        labels.append(f"business quality is {bq}")
    if fq:
        labels.append(f"financial quality is {fq}")
    if val:
        labels.append(f"valuation is {val}")
    if labels:
        parts.append("AGIB structured assessment indicates " + ", ".join(labels) + ".")
    if reasons:
        parts.append(f"Key observations include {reasons}.")
    if risks:
        parts.append(f"Principal risk noted is {risks}.")
    note = _evidence_note(structured)
    if note:
        parts.append(note)
    return " ".join(parts).strip() or note


def template_quick_analysis(structured: dict[str, Any]) -> str:
    company = structured.get("company") or "The issuer"
    summary = template_quick_summary(structured)
    horizon = structured.get("investment_horizon")
    extra = f" {company} is framed over a {horizon} horizon in the supplied package." if horizon else ""
    return f"{summary}{extra}".strip()


def template_detailed_analysis(structured: dict[str, Any]) -> str:
    company = structured.get("company") or "The issuer"
    bq = structured.get("business_quality") or "not fully labelled"
    fq = structured.get("financial_quality") or "not fully labelled"
    val = structured.get("valuation") or "not fully labelled"
    reasons = _join(list(structured.get("top_reasons") or []), 3)
    risks = _join(list(structured.get("top_risks") or []), 2)
    horizon = structured.get("investment_horizon") or "the supplied horizon"
    stance = structured.get("stance")
    parts = [
        f"{company}: AGIB's structured package characterises business quality as {bq}, "
        f"financial quality as {fq}, and valuation as {val}."
    ]
    if stance:
        parts.append(f"Analytical stance in the package is {stance}.")
    if reasons:
        parts.append(f"Supporting observations: {reasons}.")
    if risks:
        parts.append(f"Risk observations: {risks}.")
    parts.append(f"Investment horizon noted in the package is {horizon}.")
    if not reasons and not risks:
        parts.append("Available evidence is insufficient for a denser institutional narrative.")
    return " ".join(parts)


def render_template(mode: str, structured: dict[str, Any]) -> str:
    if mode == "detailed_analysis":
        return template_detailed_analysis(structured)
    if mode == "quick_analysis":
        return template_quick_analysis(structured)
    # quick_summary and legacy "recommendation" mode
    return template_quick_summary(structured)
