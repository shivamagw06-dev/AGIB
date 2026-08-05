"""Response planner — Research → Plan → Write."""

from __future__ import annotations

from typing import Any

from institutional_writing_constitution.assembler import infer_answer_length
from institutional_writing_constitution.templates import DEFAULT_TEMPLATE, RESPONSE_TEMPLATES, resolve_template, template_sections


def plan_response(
    pack: dict[str, Any],
    *,
    query: str = "",
    ticker: str | None = None,
    company: str | None = None,
    category: str | None = None,
) -> dict[str, Any]:
    """Decide template, prioritization, and section emphasis before writing."""
    template_id = resolve_template(query, category=category)
    template = RESPONSE_TEMPLATES.get(template_id) or RESPONSE_TEMPLATES[DEFAULT_TEMPLATE]
    sections = template_sections(template_id)
    length_class = infer_answer_length(query)

    assertions = pack.get("institutional_assertions") or []
    if not assertions:
        sel = pack.get("ikr_selection") or {}
        assertions = sel.get("assertions") or []
    supported = [
        a for a in assertions
        if isinstance(a, dict) and str(a.get("status") or a.get("state")) in {"SUPPORTED", "PARTIAL", "ANSWERED"}
    ]

    top_insights: list[str] = []
    for a in supported[:3]:
        stmt = str(a.get("statement") or "").strip()
        if stmt:
            top_insights.append(stmt)
    if not top_insights:
        top_insights = [
            "Business quality and competitive positioning",
            "Earnings trajectory versus market expectations",
            "Valuation relative to growth and capital allocation",
        ]

    expand: list[str] = []
    if template_id == "investment_assessment":
        expand = ["investment_debate", "key_uncertainties"]
    elif template_id == "earnings_review":
        expand = ["what_changed", "market_implications"]
    elif template_id == "valuation":
        expand = ["current_expectations", "historical_context"]
    elif template_id == "peer_comparison":
        expand = ["business_comparison", "competitive_position"]
    elif template_id == "risk_review":
        expand = ["primary_risks", "probability"]
    else:
        expand = ["what_matters_most", "investment_debate"]

    omit = [
        "Raw data dumps without interpretation",
        "Low-impact facts that do not change investment understanding",
        "Repeated sector generalities without company specificity",
    ]

    detail_map = {
        "simple_question": "concise",
        "research_request": "standard",
        "deep_research": "expanded",
    }

    return {
        "enabled": True,
        "resolved_question": query or f"Institutional research on {company or ticker or 'this entity'}",
        "template_id": template_id,
        "template_label": template["label"],
        "section_order": list(sections),
        "top_insights": top_insights[:3],
        "omit": omit,
        "expand_sections": expand,
        "detail_level": detail_map.get(length_class, "standard"),
        "answer_length_class": length_class,
        "entity": {"ticker": ticker, "company": company},
    }
