"""Editorial Intelligence Layer — writer-only soft-wire tests."""

from __future__ import annotations

from editorial.cache import EditorialCache
from editorial.package import build_structured_package, contains_forbidden_payload, sanitize_structured
from editorial.production import health, package_for_ask_agi, quality_gates
from editorial.service import EditorialService, generateRecommendation, generateQuickAnalysis
from editorial.template_fallback import render_template


SAMPLE = {
    "recommendation": "BUY",
    "conviction": "Medium",
    "business_quality": "Excellent",
    "financial_quality": "Stable",
    "valuation": "Attractive",
    "top_reasons": [
        "Strong deposit franchise",
        "Reasonable valuation",
        "Stable asset quality",
    ],
    "top_risks": ["NIM pressure"],
    "investment_horizon": "3-5 Years",
}


def test_health_and_gates():
    h = health()
    assert h["role"] == "writer_only"
    assert h["agib_is_brain"] is True
    g = quality_gates()
    assert g["checks"]["never_reads_pdfs"] is True
    assert g["checks"]["never_overrides_recommendation"] is True


def test_sanitize_drops_forbidden_document_fields():
    dirty = {
        **SAMPLE,
        "annual_report": "huge pdf text",
        "news": [{"title": "x"}],
        "financial_statements": {"revenue": 1},
        "transcript": "call notes",
    }
    assert contains_forbidden_payload(dirty) is True
    clean = sanitize_structured(dirty)
    assert "annual_report" not in clean
    assert "news" not in clean
    assert "financial_statements" not in clean
    assert clean["recommendation"] == "BUY"
    assert clean["top_reasons"][0] == "Strong deposit franchise"


def test_template_fallback_preserves_recommendation():
    text = render_template("recommendation", SAMPLE)
    assert "Recommendation: BUY" in text
    assert "NIM pressure" in text
    assert "3-5 Years" in text


def test_generate_recommendation_never_fails_without_gemini():
    # No API key in test env → template fallback, request still succeeds.
    out = generateRecommendation(SAMPLE, question="Should I buy HDFC Bank?")
    assert out["enabled"] is True
    assert out["fallback"] is True
    assert out["recommendation_preserved"] is True
    assert "BUY" in out["text"]
    assert out["word_count"] <= 60


def test_generate_quick_analysis_api():
    out = generateQuickAnalysis(SAMPLE, question="Quick view on HDFC Bank")
    assert out["mode"] == "quick_analysis"
    assert "BUY" in out["text"]


def test_cache_identical_recommendation_requests():
    cache = EditorialCache(ttl_seconds=60)
    key = cache.make_key("recommendation", SAMPLE, "Should I buy HDFC Bank?")
    cache.set(key, {"text": "cached", "provider": "gemini"})
    assert cache.get(key)["text"] == "cached"


def test_package_for_ask_agi_soft_wire():
    ac = {
        "enabled": True,
        "house_label": "Constructive",
        "bull": ["Strong deposit franchise"],
        "risks": ["NIM pressure"],
        "institutional_answer": {
            "enabled": True,
            "is_recommendation_query": True,
            "recommendation": "Buy",
            "conviction": "Medium Conviction",
            "reason": "Strong deposit franchise and reasonable valuation.",
            "risk": "NIM pressure",
            "horizon": "Medium Term",
        },
    }
    out = package_for_ask_agi(
        query="Should I buy HDFC Bank?",
        ticker="HDFCBANK",
        answer_construction=ac,
        company="HDFC Bank",
    )
    assert out["enabled"] is True
    assert out["agib_is_brain"] is True
    assert out["executive"]
    assert out["structured_intelligence"]["recommendation"] in {"Buy", "BUY"}
    assert "annual_report" not in out["structured_intelligence"]


def test_build_structured_package_from_agib_outputs():
    structured = build_structured_package(
        question="Should I buy HDFC Bank?",
        institutional_answer={
            "enabled": True,
            "recommendation": "Buy",
            "conviction": "Medium Conviction",
            "reason": "Strong deposit franchise",
            "risk": "NIM pressure",
            "horizon": "3-5 Years",
        },
        company="HDFC Bank",
        ticker="HDFCBANK",
    )
    assert structured["recommendation"] == "Buy"
    assert structured["top_reasons"] == ["Strong deposit franchise"]
    assert structured["top_risks"] == ["NIM pressure"]


def test_service_rejects_provider_override_of_recommendation(monkeypatch):
    class FakeProvider:
        name = "fake"

        def health(self):
            return {"provider": "fake", "available": True}

        async def rewrite(self, **kwargs):
            return {
                "text": "Recommendation: SELL\n\nThis invents a different call.",
                "provider": "fake",
                "model": "fake",
                "usage": {},
                "latency_ms": 1,
                "prompt": "x",
            }

    service = EditorialService(provider=FakeProvider())
    out = service.generateRecommendation(SAMPLE, question="Should I buy?")
    assert out["fallback"] is False or "BUY" in out["text"]
    assert "Recommendation: BUY" in out["text"]
    assert "SELL" not in out["text"].split("\n")[0]
