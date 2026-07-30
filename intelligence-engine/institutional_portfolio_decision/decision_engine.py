"""CIO-01 decision engine — portfolio decisions reference company decisions."""

from __future__ import annotations

import hashlib
from typing import Any, Optional, Sequence

from institutional_portfolio.portfolio_entities import InstitutionalPortfolio
from institutional_portfolio_decision.allocation_actions import generate_allocation_actions
from institutional_portfolio_decision.calibration import calibrate_portfolio
from institutional_portfolio_decision.exposure_actions import generate_exposure_actions
from institutional_portfolio_decision.models import (
    CompanyDecisionRef,
    InstitutionalPortfolioDecision,
)
from institutional_portfolio_decision.monitoring import build_monitoring_plan, monitoring_items_flat
from institutional_portfolio_decision.schema import (
    DECISION_ENGINE_VERSION,
    LINEAGE_CHAIN,
    VALIDATOR_VERSION,
)

try:
    from financial_statements_engine.util import now_iso
except Exception:  # noqa: BLE001
    from datetime import datetime, timezone

    def now_iso() -> str:  # type: ignore[misc]
        return datetime.now(timezone.utc).isoformat()


def _decision_id(portfolio_id: str, version: int, recommendation: str) -> str:
    raw = f"{portfolio_id}|{version}|{recommendation}|{DECISION_ENGINE_VERSION}"
    return f"cio-{portfolio_id.lower()}-{hashlib.sha256(raw.encode()).hexdigest()[:12]}"


def build_company_decision_refs(
    portfolio: InstitutionalPortfolio,
) -> tuple[tuple[CompanyDecisionRef, ...], tuple[CompanyDecisionRef, ...]]:
    """
    Map holdings to referential company decision links.

    Company recommendations are inputs — never rewritten here.
    """
    supporting: list[CompanyDecisionRef] = []
    contradicting: list[CompanyDecisionRef] = []
    # Dominant recommendation by weight
    weights = {"BUY": 0.0, "HOLD": 0.0, "SELL": 0.0}
    for h in portfolio.holdings:
        rec = (h.recommendation or "HOLD").upper()
        if rec not in weights:
            rec = "HOLD"
        weights[rec] = weights.get(rec, 0.0) + float(h.weight)
    dominant = max(weights, key=weights.get) if portfolio.holdings else "HOLD"

    for h in portfolio.holdings:
        rec = (h.recommendation or "HOLD").upper()
        if rec not in {"BUY", "HOLD", "SELL"}:
            rec = "HOLD"
        role = "supporting" if rec == dominant else "contradicting"
        ref = CompanyDecisionRef(
            ticker=h.ticker,
            decision_id=h.decision_id,
            recommendation=rec,
            confidence=int(h.confidence or 0),
            conviction="",
            weight=float(h.weight),
            role=role,
        )
        if role == "contradicting":
            contradicting.append(ref)
        else:
            supporting.append(ref)
    return tuple(supporting), tuple(contradicting)


def _choose_recommendation(
    *,
    sector_concentration: float,
    hhi: float,
    cash_weight: float,
    top_sector: str,
    allocation_delta_cash: float,
    has_trim_actions: bool,
    agreement: float,
    sell_weight: float,
) -> tuple[str, str, str]:
    """Return (recommendation, posture, rule_path)."""
    # Priority rules — first match wins
    if sector_concentration >= 0.85 or hhi >= 0.28:
        return (
            "Reduce Concentration",
            "Defensive",
            "rule:concentration_critical",
        )
    if sector_concentration >= 0.70 and has_trim_actions:
        if top_sector.lower() in {"banking", "financials", "banks", "finance"}:
            return (
                "Increase Diversification",
                "Defensive",
                "rule:sector_concentration_financials",
            )
        if "tech" in top_sector.lower() or top_sector.lower() in {"information technology", "it"}:
            return (
                "Reduce Technology",
                "Defensive",
                "rule:sector_concentration_technology",
            )
        return (
            "Increase Diversification",
            "Defensive",
            "rule:sector_concentration",
        )
    if allocation_delta_cash > 0 or (cash_weight < 0.06 and sector_concentration >= 0.60):
        return (
            "Increase Cash",
            "Defensive",
            "rule:cash_buffer",
        )
    if sell_weight >= 0.20:
        return (
            "Review Portfolio",
            "Review",
            "rule:sell_weight_material",
        )
    if (
        top_sector.lower() in {"banking", "financials", "banks", "finance"}
        and agreement >= 0.75
        and sector_concentration < 0.70
        and hhi < 0.20
    ):
        return (
            "Increase Financials",
            "Constructive",
            "rule:financials_constructive",
        )
    if agreement >= 0.8 and hhi < 0.22 and sector_concentration < 0.75:
        return (
            "Maintain Allocation",
            "Neutral",
            "rule:maintain_stable",
        )
    if not has_trim_actions and agreement >= 0.6:
        return (
            "No Action Required",
            "Neutral",
            "rule:no_material_change",
        )
    return (
        "Maintain Allocation",
        "Neutral",
        "rule:default_maintain",
    )


def generate_portfolio_decision(
    portfolio: InstitutionalPortfolio,
    *,
    previous_version: int = 0,
    concentration: Optional[dict[str, Any]] = None,
    observation_health: float = 0.7,
    forecast_stability: float = 0.7,
) -> InstitutionalPortfolioDecision:
    """
    Build an InstitutionalPortfolioDecision from portfolio state + company decision refs.

    Does not call decide_company to rewrite recommendations — only reads refs.
    """
    conc = dict(concentration or {})
    hhi = float(conc.get("hhi") or 0.0)
    sectors = [e for e in portfolio.exposures if e.dimension == "sector"]
    sector_concentration = float(sectors[0].weight) if sectors else 0.0
    top_sector = sectors[0].name if sectors else ""

    supporting, contradicting = build_company_decision_refs(portfolio)
    all_refs = tuple(list(supporting) + list(contradicting))
    sell_weight = sum(r.weight for r in all_refs if r.recommendation == "SELL")
    agreement = 0.0
    if all_refs:
        buckets: dict[str, float] = {}
        for r in all_refs:
            buckets[r.recommendation] = buckets.get(r.recommendation, 0.0) + r.weight
        agreement = max(buckets.values()) if buckets else 0.0

    alloc_actions = generate_allocation_actions(
        portfolio,
        refs=all_refs,
        sector_concentration=sector_concentration,
        hhi=hhi,
    )
    cash_delta = 0.0
    for a in alloc_actions:
        if a.ticker == "CASH":
            cash_delta = a.to_weight - a.from_weight
    has_trim = any(a.to_weight < a.from_weight and a.ticker != "CASH" for a in alloc_actions)

    recommendation, posture, rule_path = _choose_recommendation(
        sector_concentration=sector_concentration,
        hhi=hhi,
        cash_weight=float(portfolio.cash_weight or 0.0),
        top_sector=top_sector,
        allocation_delta_cash=cash_delta,
        has_trim_actions=has_trim,
        agreement=agreement,
        sell_weight=sell_weight,
    )

    # Special-case label when banking book constructive increase
    if recommendation == "Increase Diversification" and top_sector.lower() in {
        "banking",
        "financials",
        "banks",
    }:
        # Keep Increase Diversification — more accurate than Increase Financials when already concentrated
        pass

    exposure_actions = generate_exposure_actions(portfolio)
    calibration, scorecard = calibrate_portfolio(
        portfolio,
        refs=all_refs,
        hhi=hhi,
        sector_concentration=sector_concentration,
        recommendation=recommendation,
        observation_health=observation_health,
        forecast_stability=forecast_stability,
    )
    plan = build_monitoring_plan(
        portfolio,
        refs=all_refs,
        allocation_actions=alloc_actions,
        recommendation=recommendation,
        sector_concentration=sector_concentration,
    )
    version = int(previous_version or 0) + 1
    risks = tuple(r.to_dict() if hasattr(r, "to_dict") else dict(r) for r in portfolio.risks)

    return InstitutionalPortfolioDecision(
        portfolio_id=portfolio.portfolio_id,
        decision_id=_decision_id(portfolio.portfolio_id, version, recommendation),
        decision_version=version,
        generated_at=now_iso(),
        recommendation=recommendation,
        confidence=calibration.confidence,
        conviction=calibration.conviction,
        investment_posture=posture,
        supporting_decisions=supporting,
        contradicting_decisions=contradicting,
        allocation_actions=alloc_actions,
        exposure_actions=exposure_actions,
        portfolio_risks=risks,
        monitoring_items=monitoring_items_flat(plan),
        monitoring_plan=plan,
        calibration=calibration,
        scorecard=scorecard,
        diagnostics=None,
        lineage=LINEAGE_CHAIN,
        portfolio_graph_id=portfolio.graph_id,
        decision_engine_version=DECISION_ENGINE_VERSION,
        validator_version=VALIDATOR_VERSION,
        rule_path=rule_path,
        llm=False,
        mutates_company_decisions=False,
    )
