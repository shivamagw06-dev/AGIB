"""Editorial Intelligence Layer — rewrite-only soft-wire tests."""

from __future__ import annotations

from editorial.cache import EditorialCache
from editorial.package import build_structured_package, contains_forbidden_payload, sanitize_structured
from editorial.production import health, package_for_ask_agi, quality_gates
from editorial.service import (
    EditorialService,
    generateQuickAnalysis,
    generateQuickSummary,
    generateRecommendation,
    strip_advice_language,
)
from editorial.template_fallback import render_template


SAMPLE = {
    "recommendation": "BUY",
    "conviction": "Medium",
    "business_quality": "Excellent",
    "financial_quality": "Stable",
    "valuation": "Attractive",
    "company": "HDFC Bank",
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
    assert h["never_generates_advice"] is True
    g = quality_gates()
    assert g["checks"]["never_reads_pdfs"] is True
    assert g["checks"]["never_recommends_actions"] is True
    assert g["checks"]["word_limits"]["quick_summary"] == 80
    assert g["checks"]["word_limits"]["quick_analysis"] == 150
    assert g["checks"]["word_limits"]["detailed_analysis"] == 400


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
    assert clean["recommendation"] == "BUY"


def test_template_fallback_is_plain_english_rewrite():
    text = render_template("quick_summary", SAMPLE)
    assert "Recommendation:" not in text
    lower = text.lower()
    assert "buy" not in lower.split()  # no action verb as a word lead
    assert "business strength" in lower or "deposit" in lower
    assert "interest margin" in lower or "loan quality" in lower or "watch" in lower
    assert "you should" not in lower
    assert "target price" not in lower
    assert "franchise" not in lower
    assert "nim" not in lower


def test_generate_quick_summary_never_emits_advice():
    out = generateQuickSummary(SAMPLE, question="Should I buy HDFC Bank?")
    assert out["enabled"] is True
    assert out["fallback"] is True
    assert out["mode"] == "quick_summary"
    assert out["max_words"] == 80
    assert out["word_count"] <= 80
    assert "Recommendation:" not in (out.get("rewritten_summary") or "")
    assert "Recommendation:" not in (out.get("text") or "")
    lower = (out.get("rewritten_summary") or "").lower()
    assert "you should" not in lower
    assert "target price" not in lower
    # First sentence answers directly
    assert (out.get("text") or "").startswith("HDFC Bank")


def test_generate_recommendation_is_plain_summary_not_action():
    # Legacy name still returns rewrite-only prose — never Recommendation: BUY
    out = generateRecommendation(SAMPLE, question="Should I buy HDFC Bank?")
    assert out["fallback"] is True
    assert not (out.get("text") or "").startswith("Recommendation:")
    assert "Recommendation:" not in (out.get("rewritten_summary") or "")
    assert out["recommendation_from_agib_only"] is True
    assert out["never_recommends_actions"] is True


def test_generate_quick_analysis_word_limit():
    out = generateQuickAnalysis(SAMPLE, question="Quick view on HDFC Bank")
    assert out["mode"] == "quick_analysis"
    assert out["max_words"] == 150
    assert out["word_count"] <= 150
    assert "Recommendation:" not in out["text"]


def test_strip_advice_language():
    dirty = "Recommendation: SELL\nYou should exit the stock.\nDeposit franchise remains resilient."
    clean = strip_advice_language(dirty)
    assert "Recommendation:" not in clean
    assert "you should" not in clean.lower()
    assert "Deposit franchise remains resilient." in clean


def test_service_strips_provider_advice(monkeypatch):
    class FakeProvider:
        name = "fake"

        def health(self):
            return {"provider": "fake", "available": True}

        async def rewrite(self, **kwargs):
            return {
                "text": "Recommendation: SELL\nBuy this name aggressively.\nStrong deposit franchise supports resilience.",
                "provider": "fake",
                "model": "fake",
                "usage": {},
                "latency_ms": 1,
                "prompt": "x",
            }

    service = EditorialService(provider=FakeProvider())
    out = service.generateQuickSummary(SAMPLE, question="Should I buy?")
    assert "Recommendation:" not in (out.get("rewritten_summary") or "")
    assert "SELL" not in (out.get("rewritten_summary") or "")


def test_cache_identical_summary_requests():
    cache = EditorialCache(ttl_seconds=60)
    key = cache.make_key("quick_summary", SAMPLE, "Should I buy HDFC Bank?")
    cache.set(key, {"text": "cached", "provider": "gemini"})
    assert cache.get(key)["text"] == "cached"


def test_package_for_ask_agi_soft_wire_rewrite_only():
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
    assert out["never_generates_advice"] is True
    assert out["never_recommends_actions"] is True
    assert out["executive"]
    assert out["structured_intelligence"]["recommendation"] in {"Buy", "BUY"}
    assert out["rewritten_summary"]
    assert "Recommendation:" not in out["rewritten_summary"]
    assert "Recommendation:" not in (out["executive"] or "")
    assert not (out["executive"] or "").lower().startswith("recommendation")


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
