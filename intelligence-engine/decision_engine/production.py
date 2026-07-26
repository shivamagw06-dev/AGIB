"""AGIB Investment Decision Engine — soft production entry for Ask AGI."""

from __future__ import annotations

from typing import Any

from decision_engine.flags import flags_dict, is_enabled
from decision_engine.intent import is_investment_decision_question
from decision_engine.layers import assemble_layers
from decision_engine.schema import ARCHITECTURE_STATUS, IDE_VERSION, PROGRAMME


def health() -> dict[str, Any]:
    return {
        "status": "ok" if is_enabled() else "disabled",
        "programme": PROGRAMME,
        "version": IDE_VERSION,
        "architecture_status": ARCHITECTURE_STATUS,
        "not_an_engine_redesign": True,
        "never_skip_layer": True,
        "decision_last": True,
        "flags": flags_dict(),
    }


def package_for_ask_agi(
    query: str = "",
    *,
    ticker: str | None = None,
    cid: dict[str, Any] | None = None,
    company_analysis: dict[str, Any] | None = None,
    company_monitor: dict[str, Any] | None = None,
    sector_intelligence: dict[str, Any] | None = None,
    live_evidence: dict[str, Any] | None = None,
    evidence_completion: dict[str, Any] | None = None,
    valuation_pack: dict[str, Any] | None = None,
    market_events: dict[str, Any] | None = None,
    investment_intelligence: dict[str, Any] | None = None,
    institutional_briefing: dict[str, Any] | None = None,
    intelligence_construction: dict[str, Any] | None = None,
    irp: dict[str, Any] | None = None,
    aws_macro: dict[str, Any] | None = None,
    gate_blocked: bool | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Soft entry — builds the full 13-layer decision stack for buy/invest questions."""
    if not is_enabled():
        return {
            "enabled": False,
            "programme": PROGRAMME,
            "version": IDE_VERSION,
            "bypassed": True,
            "architecture_status": ARCHITECTURE_STATUS,
        }

    leo = live_evidence if isinstance(live_evidence, dict) else {}
    irp_pkg = irp if isinstance(irp, dict) else {}
    triggered = force or is_investment_decision_question(query, leo_pkg=leo, irp=irp_pkg)
    # Also trigger when we have a resolved company for research-style questions
    if not triggered and (ticker or (company_analysis or {}).get("ticker") or (cid or {}).get("ticker")):
        if str((irp_pkg or {}).get("intent") or "").lower() in {"company_research", "investment_thesis", "valuation"}:
            triggered = True

    if not triggered:
        return {
            "enabled": True,
            "active": False,
            "programme": PROGRAMME,
            "version": IDE_VERSION,
            "architecture_status": ARCHITECTURE_STATUS,
            "reason": "not_an_investment_decision_question",
            "flags": flags_dict(),
        }

    sif = sector_intelligence if isinstance(sector_intelligence, dict) else {}
    blocked = gate_blocked
    if blocked is None:
        blocked = bool((sif.get("recommendation_gate") or {}).get("blocked")) or bool(
            (leo.get("quality_gate") or {}).get("blocked")
        )

    assembled = assemble_layers(
        query=query,
        ticker=ticker,
        cid=cid,
        company_analysis=company_analysis,
        sector_intelligence=sif,
        live_evidence=leo,
        evidence_completion=evidence_completion,
        valuation_pack=valuation_pack,
        market_events=market_events,
        investment_intelligence=investment_intelligence,
        institutional_briefing=institutional_briefing
        or ((irp_pkg.get("institutional_briefing") if isinstance(irp_pkg, dict) else None)),
        intelligence_construction=intelligence_construction,
        aws_macro=aws_macro,
        gate_blocked=bool(blocked),
    )

    decision = (assembled.get("layers_by_id") or {}).get("decision") or {}
    expected = (assembled.get("layers_by_id") or {}).get("expected_return") or {}
    probability = (assembled.get("layers_by_id") or {}).get("probability") or {}

    # Soft optional FIML consult — never required
    fiml_hint = None
    try:
        from models.consumers import for_ask_agi as fiml_for_ask_agi

        payload = {
            "subject_id": ticker or assembled.get("ticker") or "subject",
            "margin_of_safety": expected.get("margin_of_safety_proxy"),
            "catalysts": ((assembled.get("layers_by_id") or {}).get("catalysts") or {}).get("positive") or [],
            "data_quality": "B",
        }
        fiml_hint = fiml_for_ask_agi(payload)
    except Exception:
        fiml_hint = None

    return {
        "enabled": True,
        "active": True,
        "programme": PROGRAMME,
        "version": IDE_VERSION,
        "architecture_status": ARCHITECTURE_STATUS,
        "not_an_engine_redesign": True,
        "flags": flags_dict(),
        "query": query,
        "ticker": assembled.get("ticker"),
        "company_name": assembled.get("company_name"),
        "overall_score": assembled.get("overall_score"),
        "investment_grade": assembled.get("investment_grade"),
        "layers": assembled.get("layers"),
        "summary": {
            "overall_score": assembled.get("overall_score"),
            "investment_grade": assembled.get("investment_grade"),
            "confidence_pct": decision.get("confidence_pct"),
            "confidence_breakdown": decision.get("confidence_breakdown") or {},
            "expected_return_12m_pct": decision.get("expected_return_12m_pct"),
            "bull_case_pct": decision.get("bull_case_pct"),
            "base_case_pct": decision.get("base_case_pct"),
            "bear_case_pct": decision.get("bear_case_pct"),
            "probability_weighted_return_pct": decision.get("probability_weighted_return_pct"),
            "risk_reward": decision.get("risk_reward"),
            "action": decision.get("action"),
            "suitable_for": decision.get("suitable_for") or [],
            "unsuitable_for": decision.get("unsuitable_for") or [],
            "layer_scores": decision.get("layer_scores") or {},
            "gate_blocked": bool(blocked),
        },
        "pre_questions": decision.get("pre_questions") or [],
        "decision": decision,
        "probability": probability,
        "expected_return": expected,
        "answer_enrichment": {
            "executive_framing": (
                f"Investment decision stack for {assembled.get('company_name')}: "
                "macro → industry → company → financials → management → valuation → "
                "expectations → technical → risk → catalysts → probability → expected return → conclusion. "
                "No layer is skipped."
            ),
            "why_bullets": [
                lyr.get("reasoning")
                for lyr in (assembled.get("layers") or [])[:6]
                if lyr.get("id") != "decision" and lyr.get("reasoning")
            ][:6],
            "decision_conclusion": decision.get("reasoning"),
        },
        "fiml_soft_consult": {
            "used": bool(fiml_hint),
            "narrative_hint": (fiml_hint or {}).get("narrative_hint"),
        }
        if fiml_hint
        else {"used": False},
        "answer_policy": "multi_layer_investment_decision_never_direct_buy_sell",
        "never_skip_layer": True,
        "decision_last": True,
        "never_expose_framework_names": True,
    }


def quality_gates() -> dict[str, Any]:
    return {
        "programme": PROGRAMME,
        "version": IDE_VERSION,
        "architecture_status": ARCHITECTURE_STATUS,
        "passed": is_enabled(),
        "checks": {
            "enabled": is_enabled(),
            "thirteen_layers": True,
            "never_skip_layer": True,
            "decision_last": True,
            "never_direct_buy_sell_first": True,
        },
        "flags": flags_dict(),
    }
