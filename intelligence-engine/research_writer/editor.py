"""IRW editor — publication writing after CIO. Never changes votes/scores/confidence/evidence."""

from __future__ import annotations

from typing import Any

from research_writer.chart_recommender import recommend_charts
from research_writer.citation_builder import build_citations
from research_writer.consistency import consistency_check, enforce_consistency, extract_context
from research_writer.formatter import format_report
from research_writer.language_quality import scrub_leaks, word_count
from research_writer import narrative
from research_writer.schema import IMMUTABLE_FIELDS, SECTION_ORDER
from research_writer.table_builder import build_tables
from research_writer.tone import tone_report
from research_writer.transition import with_transitions


def _immutable_snapshot(pack: dict[str, Any]) -> dict[str, Any]:
    """Capture intelligence the writer must not alter."""
    committee = pack.get("committee") if isinstance(pack.get("committee"), dict) else {}
    cio = pack.get("cio") if isinstance(pack.get("cio"), dict) else {}
    return {
        "confidence": pack.get("confidence") if pack.get("confidence") is not None else cio.get("confidence"),
        "committee_vote": pack.get("committee_vote") or committee.get("vote"),
        "committee_decision": pack.get("committee_decision") or committee.get("decision"),
        "disagreement_matrix": pack.get("disagreement_matrix") or committee.get("disagreement_matrix"),
        "recommendation_readiness": (
            committee.get("recommendation_readiness_label")
            or committee.get("recommendation_readiness")
            or (
                (pack.get("committee_decision") or {}).get("recommendation_readiness")
                if isinstance(pack.get("committee_decision"), dict)
                else None
            )
        ),
        "analyst_confidence": {
            role: (op.get("confidence") if isinstance(op, dict) else None)
            for role, op in (pack.get("analyst_opinions") or {}).items()
        },
        "evidence_fingerprints": {
            role: list((op or {}).get("evidence") or [])[:3]
            for role, op in (pack.get("analyst_opinions") or {}).items()
            if isinstance(op, dict)
        },
    }


def write_institutional_report(pack: dict[str, Any], *, query: str = "") -> dict[str, Any]:
    """Convert CIO + analyst + committee intelligence into a publication-ready note."""
    cio = pack.get("cio") if isinstance(pack.get("cio"), dict) else {}
    committee = pack.get("committee") if isinstance(pack.get("committee"), dict) else {}
    opinions = pack.get("analyst_opinions") if isinstance(pack.get("analyst_opinions"), dict) else {}
    # Also accept convenience projections
    if not opinions:
        opinions = {
            "business": pack.get("business_intelligence") or {},
            "financial": pack.get("financial_intelligence") or {},
            "valuation": pack.get("valuation_intelligence") or {},
            "market": pack.get("market_intelligence") or {},
            "sector": pack.get("sector_intelligence_opinion") or {},
            "macro": pack.get("macro_intelligence") or {},
            "risk": pack.get("risk_intelligence") or {},
            "management": pack.get("management_intelligence") or {},
            "ownership": pack.get("ownership_intelligence") or {},
        }

    ctx = extract_context(pack)
    company = ctx["company"]
    ticker = ctx.get("ticker")
    q = query or pack.get("query") or ""
    report_type = narrative.detect_report_type(q)

    sections: dict[str, str] = {
        "executive_summary": narrative.write_executive(cio=cio, committee=committee, company=company, query=q),
        "institutional_view": narrative.write_institutional_view(committee),
        "investment_thesis": narrative.write_thesis(cio, company=company),
        "business_intelligence": narrative.write_business(opinions.get("business") or {}, company=company),
        "financial_intelligence": narrative.write_financial(opinions.get("financial") or {}, company=company),
        "valuation_intelligence": narrative.write_valuation(opinions.get("valuation") or {}, company=company),
        "market_intelligence": narrative.write_market(opinions.get("market") or {}, company=company),
        "sector_intelligence": narrative.write_sector(opinions.get("sector") or {}, company=company),
        "macro_intelligence": narrative.write_macro(opinions.get("macro") or {}, company=company),
        "management": narrative.write_management(opinions.get("management") or {}, company=company),
        "ownership": narrative.write_ownership(opinions.get("ownership") or {}, company=company),
        "catalysts": scrub_leaks(
            "Key catalysts: " + "; ".join(str(c) for c in (cio.get("key_catalysts") or [])[:4]),
            limit=320,
        ),
        "conclusion": narrative.write_conclusion(cio=cio, committee=committee, company=company),
    }

    # Consistency + transitions
    sections = {k: enforce_consistency(v, ctx) for k, v in sections.items()}
    sections = with_transitions(sections, [k for k in SECTION_ORDER if k in sections])

    risks = narrative.write_risks(opinions.get("risk") or {}, cio=cio)
    scenarios = narrative.write_scenarios(cio)
    tables = build_tables(opinions=opinions, cio=cio, committee=committee)
    charts = recommend_charts(opinions, pack=pack)
    citations = build_citations(opinions)

    immutable = _immutable_snapshot(pack)
    quality = output_quality_check(sections, risks=risks, scenarios=scenarios)
    cons = consistency_check(sections, ctx)
    quality["consistency"] = cons

    report = format_report(
        report_type=report_type,
        company=company,
        ticker=ticker,
        query=q,
        sections={**sections, "risks": "see risk_register"},
        risks=risks,
        scenarios=scenarios,
        tables=tables,
        charts=charts,
        citations=citations,
        quality=quality,
        immutable=immutable,
    )

    # Convenience flat fields for Ask AGI / AC (presentation only)
    sec = report.get("sections") or {}
    report["executive_summary"] = sec.get("executive_summary")
    report["investment_thesis"] = sec.get("investment_thesis")
    report["institutional_view"] = sec.get("institutional_view")
    report["business_intelligence"] = sec.get("business_intelligence")
    report["financial_intelligence"] = sec.get("financial_intelligence")
    report["valuation_intelligence"] = sec.get("valuation_intelligence")
    report["market_intelligence"] = sec.get("market_intelligence")
    report["sector_intelligence"] = sec.get("sector_intelligence")
    report["macro_intelligence"] = sec.get("macro_intelligence")
    report["management"] = sec.get("management")
    report["ownership"] = sec.get("ownership")
    report["institutional_conclusion"] = sec.get("conclusion")
    report["bull_case"] = (scenarios.get("bull") or {}).get("assumptions") or []
    report["base_case"] = (scenarios.get("base") or {}).get("assumptions") or []
    report["bear_case"] = (scenarios.get("bear") or {}).get("assumptions") or []
    report["scenarios_structured"] = scenarios
    report["risk_register"] = risks
    report["never_mutates"] = list(IMMUTABLE_FIELDS)
    return report


def output_quality_check(
    sections: dict[str, str],
    *,
    risks: list[dict[str, str]] | None = None,
    scenarios: dict[str, Any] | None = None,
) -> dict[str, Any]:
    leaks = (
        "cid",
        "leo",
        "irp",
        "dvc",
        "yahoo",
        "groww",
        "finnhub",
        "fmp",
        "indianapi",
        "academy",
        "provider",
        "coverage %",
        "knowledge grade",
        "n/a",
        "unknown",
        "placeholder",
    )
    joined = " ".join(str(v) for v in sections.values()).lower()
    found = [x for x in leaks if x in joined]
    tone = tone_report(joined)
    exec_wc = word_count(sections.get("executive_summary") or "")
    conc_wc = word_count(sections.get("conclusion") or "")
    return {
        "passed": not found and tone.get("institutional", True) and exec_wc <= 160 and conc_wc <= 260,
        "no_provider_names": "yahoo" not in found and "groww" not in found and "finnhub" not in found,
        "no_engine_names": "cid" not in found and "leo" not in found and "irp" not in found,
        "no_placeholders": "n/a" not in found and "unknown" not in found and "placeholder" not in found,
        "no_grade_spam": "knowledge grade" not in found and "coverage %" not in found,
        "executive_word_count": exec_wc,
        "conclusion_word_count": conc_wc,
        "tone": tone,
        "leak_hits": found,
        "risk_register_complete": bool(risks)
        and all(r.get("description") and r.get("monitoring_trigger") for r in (risks or [])),
        "scenarios_structured": bool(scenarios)
        and all(k in (scenarios or {}) for k in ("bull", "base", "bear")),
    }
