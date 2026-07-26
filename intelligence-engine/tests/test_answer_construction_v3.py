"""Ask AGI Institutional Answer Construction V3 — soft-wire tests."""

from __future__ import annotations

from answer_construction.knowledge_gaps import (
    filter_why_bullets,
    is_checklist_bullet,
    knowledge_gaps_from_sources,
    looks_like_gate_failure_summary,
    professional_gap,
)
from answer_construction.production import health, package_for_ask_agi, quality_gates
from answer_construction.schema import AC_VERSION
from ecp.merge import withheld_explanation


def test_health_and_gates():
    h = health()
    assert h["status"] == "ok"
    assert h["version"] == AC_VERSION
    assert h["never_stop_at_first_coverage_check"] is True
    g = quality_gates()
    assert g["passed"] is True
    assert g["checks"]["preserves_full_brief_when_gated"] is True


def test_professional_gap_never_exposes_snake_case():
    phrase = professional_gap("financial_statements")
    assert "financial_statements" not in phrase
    assert "financial statement" in phrase.lower()
    assert professional_gap("valuation_metrics")


def test_checklist_detection():
    assert is_checklist_bullet("Missing: financial_statements, market_data")
    assert is_checklist_bullet("Recommendation withheld.\nCoverage: 21%")
    assert is_checklist_bullet("ECP Coverage 21.8% (was 18%). Missing: market_cap")
    assert not is_checklist_bullet("Eternal operates a multi-sided consumer internet platform.")


def test_knowledge_gaps_from_sources():
    gaps = knowledge_gaps_from_sources(
        evidence_completion={
            "quality_panel": {
                "missing_items": ["financial_statements", "valuation_metrics"],
                "must_have_missing": ["market_data"],
                "gate_blocked": True,
            }
        },
        company_dossier={"missing_evidence": ["ownership"]},
    )
    assert gaps
    joined = " ".join(gaps).lower()
    assert "financial_statements" not in joined
    assert "valuation" in joined or "financial" in joined


def test_policy_preserves_brief_when_gated():
    out = package_for_ask_agi(
        query="Should I buy Eternal?",
        executive="Insufficient Evidence view. Insufficient company evidence for institutional recommendation. Confidence 53%.",
        thesis="Recommendation withheld.\nCoverage: 21.8%\nMissing:\n- financial_statements",
        house_label="Insufficient Evidence",
        bull=[],
        bear=[],
        risks=[],
        catalysts=[],
        why=[
            "Recommendation withheld. Coverage: 21.8%. Missing: financial_statements",
            "ECP Coverage 21.8% (was 18%). Missing: market_data",
            "Eternal is a consumer internet holding spanning food delivery and quick commerce.",
        ],
        intelligence_construction={
            "enabled": True,
            "company_name": "Eternal",
            "executive_brief": "Eternal is a consumer internet platform combining food delivery and quick commerce.",
            "answer_enrichment": {
                "executive_summary": "Eternal is a consumer internet platform combining food delivery and quick commerce.",
                "why_bullets": [
                    "Food delivery remains the core demand engine; quick commerce is the growth option.",
                    "Unit economics and competitive intensity remain the key valuation debates.",
                ],
                "current_outlook": "Constructive on category leadership; valuation still needs fuller evidence.",
            },
            "sections": {
                "financial_intelligence": {
                    "narrative": "Financial quality is monitored but statement history remains incomplete."
                },
                "valuation": {"narrative": "Valuation discussion is constrained until multiples history is fuller."},
                "market_performance": {"narrative": "Shares trade with high growth-platform volatility."},
            },
        },
        company_analysis={
            "enabled": True,
            "identity": {"company_name": "Eternal", "business_model": "Multi-sided consumer marketplace"},
            "bull_case": ["Category leadership in food delivery"],
            "bear_case": ["Competitive cash burn risk"],
            "risks": ["Regulatory and competitive intensity"],
            "catalysts": ["Next quarterly results"],
            "recommendation_readiness": {"overall": 22, "gate": "Recommendation Withheld"},
        },
        evidence_completion={
            "quality_panel": {
                "coverage_pct": 21.8,
                "missing_items": ["financial_statements", "valuation_metrics"],
                "gate_blocked": True,
            },
            "withheld_explanation": "Recommendation withheld.\nCoverage: 21.8%\nMissing:\n- financial_statements",
        },
        reco_gate={"blocked": True, "message": "Insufficient company evidence for institutional recommendation."},
        leo_gate={"blocked": True, "must_have_missing": ["financial_statements"]},
    )
    assert out["enabled"] is True
    assert out["gate_blocked"] is True
    assert out["gate_logic_unchanged"] is True
    assert "Insufficient Evidence" not in (out["house_label"] or "")
    assert "Recommendation withheld" not in (out["executive"] or "")
    assert "financial_statements" not in (out["executive"] or "")
    assert "Eternal" in (out["executive"] or "")
    assert out["bull"]
    assert out["bear"]
    assert out["risks"]
    assert out["catalysts"]
    assert not any(is_checklist_bullet(w) for w in out["why"])
    reco = out["recommendation_status"]
    assert reco["blocked"] is True
    assert reco["placement"] == "conclusion_only"
    assert reco["knowledge_gaps"]
    assert "financial_statements" not in " ".join(reco["knowledge_gaps"])


def test_filter_why_removes_coverage_spam():
    cleaned = filter_why_bullets(
        [
            "Missing: market_cap, shares_outstanding",
            "CID coverage: F (21). Missing: valuation_metrics",
            "Platform demand remains resilient into festive season.",
        ]
    )
    assert len(cleaned) == 1
    assert "Platform demand" in cleaned[0]


def test_withheld_explanation_is_professional():
    text = withheld_explanation(
        {
            "coverage_pct": 62,
            "research_grade": "C",
            "data_grade": "C",
            "knowledge_grade": "D",
            "missing_items": ["ROIC", "Market share"],
            "must_have_missing": ["financial_statements"],
        },
        {"leo_missing": ["financial_statements"]},
    )
    assert "Institutional recommendation status" in text
    assert "Current knowledge gaps" in text
    assert "financial_statements" not in text
    assert looks_like_gate_failure_summary(
        "Insufficient Evidence view. Insufficient company evidence. Confidence 53%."
    )
