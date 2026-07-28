"""Deterministic intent classifier — Track A taxonomy."""

from __future__ import annotations

from typing import Any

from ask_pipeline.intent_resolution.schema import INTENTS_V2


def classify_intent(
    *,
    language: dict[str, Any],
    temporal: dict[str, Any],
    entities: dict[str, Any],
) -> dict[str, Any]:
    cues = language.get("cues") or {}
    scores: dict[str, float] = {i: 0.0 for i in INTENTS_V2}
    reasons: list[str] = []

    def bump(intent: str, amount: float, reason: str) -> None:
        scores[intent] = scores.get(intent, 0.0) + amount
        reasons.append(f"{intent}:{reason}")

    # Historical replay highest priority when temporal/replay cues present
    if temporal.get("is_historical") and (
        cues.get("historical_replay") or temporal.get("mode") == "point_in_time" or "replay" in reasons
    ):
        bump("HistoricalReplay", 3.5, "temporal_replay")
    if cues.get("historical_replay"):
        bump("HistoricalReplay", 2.5, "replay_lexicon")

    if cues.get("cross_domain"):
        bump("CrossDomain", 3.0, "cross_domain_cue")
    # Multiple domain cues → cross-domain
    domain_hits = sum(
        1
        for k in ("macro", "government", "industry", "accounting", "documents", "valuation_lexicon")
        if cues.get(k)
    )
    if domain_hits >= 3 and (cues.get("analyse") or cues.get("cross_domain") or cues.get("list_request")):
        bump("CrossDomain", 2.2, "multi_domain")

    if cues.get("documents"):
        bump("Documents", 2.8, "documents_lexicon")
    if cues.get("compare"):
        bump("Compare", 3.0, "compare_lexicon")
    if cues.get("education") and not entities.get("primary"):
        bump("Education", 3.2, "definition_shape")
    if cues.get("portfolio"):
        bump("Portfolio", 3.0, "portfolio_lexicon")
    if cues.get("government") and not cues.get("valuation_lexicon"):
        bump("Government", 2.4, "government_lexicon")
    if cues.get("macro") and not cues.get("valuation_lexicon"):
        bump("Macro", 2.4, "macro_lexicon")
    # FX / transmission into named companies → Macro / CrossDomain over generic Explain
    if cues.get("macro") and entities.get("primary") and (cues.get("how_would_you") or cues.get("explain")):
        bump("Macro", 2.2, "macro_transmission_to_companies")
        bump("CrossDomain", 1.8, "macro_cross_companies")
        scores["Explain"] -= 1.2
        reasons.append("Explain:penalty_macro_transmission")
    if cues.get("industry") and not entities.get("primary"):
        bump("Industry", 2.3, "industry_lexicon")
    if cues.get("industry") and entities.get("primary"):
        bump("Industry", 1.2, "industry_with_entity")
    if cues.get("corporate_events"):
        bump("CorporateEvents", 2.0, "events_lexicon")
    if cues.get("accounting"):
        bump("Accounting", 2.0, "accounting_lexicon")
    if cues.get("risk") and not cues.get("explain"):
        bump("Risk", 2.0, "risk_lexicon")

    # Explain / why / how-would-you — do NOT force Valuation even if lexicon present
    if cues.get("why_question") or cues.get("explain") or cues.get("how_would_you"):
        bump("Explain", 3.4, "explain_shape")
        if cues.get("valuation_lexicon"):
            bump("Explain", 1.0, "valuation_lexicon_as_explain")
            scores["Valuation"] -= 1.5
            reasons.append("Valuation:penalty_explain_shape")
        # Domain-coloured explain (no company) → prefer domain intent
        if not entities.get("primary"):
            if cues.get("industry"):
                bump("Industry", 2.0, "why_industry_concept")
            if cues.get("macro") and not cues.get("government"):
                bump("Macro", 2.0, "why_macro_concept")
            if cues.get("government"):
                bump("Government", 2.0, "why_government_concept")
            if cues.get("documents"):
                bump("Documents", 2.0, "why_documents_concept")

    if cues.get("analyse") or cues.get("list_request"):
        bump("Analyse", 2.6, "analyse_shape")
        if cues.get("valuation_lexicon") and not cues.get("why_question"):
            # "assess whether undervalued" stays Analyse/Compare, not Valuation conclusion path
            bump("Analyse", 0.8, "analyse_with_valuation_words")
            scores["Valuation"] -= 1.0
            reasons.append("Valuation:penalty_analyse_shape")

    # Pure valuation asks (is it cheap / fair value of X)
    if cues.get("valuation_lexicon") and not (
        cues.get("why_question") or cues.get("explain") or cues.get("how_would_you") or cues.get("list_request")
    ):
        bump("Valuation", 2.8, "valuation_ask")

    if cues.get("education") and cues.get("valuation_lexicon") and not entities.get("primary"):
        bump("Education", 1.5, "concept_metric")
        scores["Valuation"] -= 2.0
        reasons.append("Valuation:penalty_education_concept")

    # Evidence-package / IC prep without valuing
    if cues.get("list_request") and cues.get("cross_domain"):
        bump("CrossDomain", 1.5, "ic_evidence_package")
        scores["Valuation"] -= 2.0
        reasons.append("Valuation:penalty_evidence_package")

    # Pick winner
    ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    intent, score = ranked[0]
    if score <= 0.5:
        intent, score = "Unknown", 0.4
        reasons.append("fallback_unknown")

    # Confidence calibrated
    second = ranked[1][1] if len(ranked) > 1 else 0.0
    margin = score - second
    confidence = min(0.99, 0.55 + 0.1 * score + 0.05 * max(margin, 0))

    return {
        "intent": intent if intent in INTENTS_V2 else "Unknown",
        "confidence": round(confidence, 4),
        "scores": {k: round(v, 3) for k, v in ranked if v > 0},
        "reasons": reasons[:24],
        "fabricated": False,
    }
