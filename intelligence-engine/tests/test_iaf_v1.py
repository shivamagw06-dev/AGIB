"""Institutional Analyst Framework V1 — orchestration / ownership tests."""

from __future__ import annotations

from answer_construction.production import package_for_ask_agi as ac_package
from institutional_analysts.base import scrub_public
from institutional_analysts.production import health, package_for_ask_agi, quality_gates
from institutional_analysts.schema import ANALYST_ROLES, IAF_VERSION, SECTION_OWNERS


INTERNAL_LEAKS = (
    "CID",
    "LEO",
    "IRP",
    "DVC",
    "ECP",
    "Yahoo",
    "Groww",
    "IndianAPI",
    "MarketDataClient",
    "Capital IQ",
    "Company Analysis",
    "Financial Intelligence",
)


def _hdfc_ctx() -> dict:
    return {
        "query": "Should I invest in HDFC Bank?",
        "ticker": "HDFCBANK",
        "company_analysis": {
            "enabled": True,
            "ticker": "HDFCBANK",
            "company_name": "HDFC Bank",
            "identity": {"company_name": "HDFC Bank", "business_model": "Universal bank franchise"},
            "business_quality": {
                "business_quality_score": 78,
                "revenue_drivers": ["Deposit franchise", "Retail credit"],
                "competitive_advantages": ["Distribution scale", "Brand trust"],
                "confidence": 0.72,
            },
            "financial_intelligence": {
                "narrative": "Earnings quality supported by NIMs and fee income.",
                "roe": "16%",
                "confidence": 0.7,
            },
            "valuation_intelligence": {
                "pe": 18.5,
                "pb": 2.6,
                "narrative": "Trades near historical mid-band versus growth.",
                "confidence": 0.62,
            },
            "risks": ["Credit cycle", "Regulatory capital"],
            "catalysts": ["Next quarterly results"],
            "bull_case": ["Franchise share gains"],
            "bear_case": ["Asset-quality stress"],
        },
        "company_dossier": {
            "ticker": "HDFCBANK",
            "identity": {"company_name": "HDFC Bank"},
            "market_data": {"trend": "Constructive bias", "liquidity": "High"},
            "shareholding": {"promoters": "Stable", "fiis": "Material", "diis": "Rising"},
            "management": {"governance": "Institutional-grade board oversight"},
        },
        "finance_academy": {"applied_concepts": ["Franchise economics", "Cost of capital"]},
        "sector_intelligence": {
            "sector_id": "private_banks",
            "priority_metrics": ["NIM", "GNPA", "CASA"],
            "structure": "Oligopolistic private banking set",
        },
        "company_monitor": {"what_changed": {"risks": ["Deposit competition"], "monitor": ["NIM"]}},
        "valuation": {"pe": 18.5, "pb": 2.6, "margin_of_safety": "Modest"},
        "data_validation": {"confidence": 0.68, "checks": ["Statements validated"]},
        "knowledge_foundation": {"themes": ["Indian banking cycle"]},
        "institutional_briefing": {
            "macro_drivers": ["Policy rates", "Credit growth"],
            "macro_transmission": "Rates and liquidity transmit via NIMs and loan demand.",
        },
        "irp": {"macro": {"interest_rates": "Stable-to-easing bias", "inflation": "Moderating"}},
        "live_evidence": {"documents_used": ["Annual report commentary"], "sources_used": ["Policy updates"]},
        "decision_engine": {
            "active": True,
            "layers": [
                {"id": "macro", "score": 62, "reasoning": "Macro mildly supportive"},
                {"id": "technical", "score": 58, "reasoning": "Tape constructive but not decisive"},
                {"id": "risk", "score": 55, "reasoning": "Credit and regulatory risks remain live"},
                {"id": "management", "score": 70, "reasoning": "Execution track record solid"},
            ],
            "summary": {"confidence_pct": 68, "expected_return_12m_pct": 11},
        },
    }


def test_health_and_gates():
    h = health()
    assert h["status"] == "ok"
    assert h["version"] == IAF_VERSION
    assert h["not_an_engine"] is True
    assert h["orchestration_only"] is True
    assert h["no_new_data"] is True
    assert set(h["analysts"]) == set(ANALYST_ROLES)
    g = quality_gates()
    assert g["passed"] is True
    assert g["checks"]["committee_reads_opinions_only"] is True
    assert g["checks"]["cio_reads_committee_only"] is True


def test_scrub_public_hides_internal_names():
    text = scrub_public("CID and LEO plus Yahoo and Groww and Company Analysis")
    lowered = text.lower()
    for leak in ("cid", "leo", "yahoo", "groww", "company analysis"):
        assert leak not in lowered


def test_hdfc_nine_opinions_committee_cio():
    pkg = package_for_ask_agi(**_hdfc_ctx())
    assert pkg["enabled"] is True
    assert pkg["orchestration_only"] is True
    opinions = pkg["analyst_opinions"]
    assert set(opinions) == set(ANALYST_ROLES)
    for role in ANALYST_ROLES:
        op = opinions[role]
        assert op["headline"]
        assert op["question"]
        assert op["evidence"]
        assert 0 < float(op["confidence"]) <= 1
        blob = " ".join(
            [
                str(op.get("headline") or ""),
                str(op.get("question") or ""),
                " ".join(str(x) for x in (op.get("evidence") or [])),
                str(op.get("sections") or ""),
            ]
        )
        for leak in INTERNAL_LEAKS:
            assert leak.lower() not in blob.lower(), f"{role} leaked {leak}"

    committee = pkg["committee"]
    assert committee["owner"] == "committee"
    assert committee["committee_summary"]
    assert committee["consensus"]
    assert committee["recommendation_readiness"] in {"ready", "partial", "not_ready"}

    cio = pkg["cio"]
    assert cio["owner"] == "cio"
    assert "HDFC" in (cio["executive_summary"] or "")
    assert cio["investment_thesis"]
    assert cio["bull_case"] and cio["base_case"] and cio["bear_case"]
    assert cio["institutional_conclusion"]
    assert pkg["section_owners"] == SECTION_OWNERS


def test_answer_construction_consumes_iaf():
    ctx = _hdfc_ctx()
    out = ac_package(
        query=ctx["query"],
        ticker=ctx["ticker"],
        company_analysis=ctx["company_analysis"],
        company_dossier=ctx["company_dossier"],
        finance_academy=ctx["finance_academy"],
        sector_intelligence=ctx["sector_intelligence"],
        company_monitor=ctx["company_monitor"],
        valuation=ctx["valuation"],
        data_validation=ctx["data_validation"],
        knowledge_foundation=ctx["knowledge_foundation"],
        institutional_briefing=ctx["institutional_briefing"],
        irp=ctx["irp"],
        live_evidence=ctx["live_evidence"],
        decision_engine=ctx["decision_engine"],
        executive="Placeholder executive",
        thesis="Placeholder thesis",
        house_label="Neutral",
        bull=[],
        bear=[],
        risks=[],
        catalysts=[],
        why=[],
    )
    assert out["enabled"] is True
    assert out["institutional_analysts_active"] is True
    iaf = out["institutional_analysts"]
    assert iaf.get("enabled") is True
    assert set(iaf.get("analyst_opinions") or {}) == set(ANALYST_ROLES)
    assert "HDFC" in (out["executive"] or "")
    assert out["bull"] and out["base"] and out["bear"]
    assert out["section_owners"]
    assert out["answer_policy"] == "institutional_analyst_framework_cio_report"
    joined = " ".join(
        [
            out.get("executive") or "",
            out.get("thesis") or "",
            out.get("decision_conclusion") or "",
            " ".join(out.get("why") or []),
        ]
    )
    for leak in INTERNAL_LEAKS:
        assert leak.lower() not in joined.lower(), f"AC leaked {leak}"
