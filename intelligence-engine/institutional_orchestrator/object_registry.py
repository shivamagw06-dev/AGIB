"""UAG-01 Object Registry — engines register capabilities; router discovers them."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass(frozen=True)
class ObjectRegistration:
    object_type: str
    routes: tuple[str, ...]
    provider: str
    planner: str  # company | portfolio | market | governance
    description: str = ""
    retrieve: Optional[Callable[..., dict[str, Any]]] = field(default=None, compare=False, hash=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "object_type": self.object_type,
            "routes": list(self.routes),
            "provider": self.provider,
            "planner": self.planner,
            "description": self.description,
            "has_provider": self.retrieve is not None,
        }


_REGISTRY: dict[str, ObjectRegistration] = {}


def reset_registry_for_tests() -> None:
    _REGISTRY.clear()
    bootstrap_default_registry()


def register(
    object_type: str,
    *,
    routes: list[str] | tuple[str, ...],
    provider: str,
    planner: str = "company",
    description: str = "",
    retrieve: Optional[Callable[..., dict[str, Any]]] = None,
) -> None:
    key = str(object_type).strip()
    _REGISTRY[key] = ObjectRegistration(
        object_type=key,
        routes=tuple(str(r).lower() for r in routes),
        provider=provider,
        planner=planner,
        description=description,
        retrieve=retrieve,
    )


def get(object_type: str) -> Optional[ObjectRegistration]:
    return _REGISTRY.get(str(object_type))


def all_registrations() -> list[ObjectRegistration]:
    return list(_REGISTRY.values())


def catalog() -> list[dict[str, Any]]:
    return [r.to_dict() for r in sorted(_REGISTRY.values(), key=lambda x: x.object_type)]


def match_routes(question: str) -> list[ObjectRegistration]:
    q = (question or "").lower()
    hits: list[tuple[int, ObjectRegistration]] = []
    for reg in _REGISTRY.values():
        score = 0
        for route in reg.routes:
            if route and route in q:
                score += max(1, len(route.split()))
        if score:
            hits.append((score, reg))
    hits.sort(key=lambda x: (-x[0], x[1].object_type))
    return [r for _, r in hits]


# --- Default provider retrieve functions (stateless calls into domain engines) ---


def _retrieve_company_decision(ctx: dict[str, Any]) -> dict[str, Any]:
    ticker = str((ctx.get("entities") or ["AXISBANK"])[0] or "AXISBANK").upper()
    # Soft: institutional decision / IDS if available
    try:
        from institutional_decision.production import get_decision  # type: ignore

        out = get_decision(ticker)
        if isinstance(out, dict) and out.get("ok") is not False:
            return {"ok": True, "object_type": "CompanyDecision", "ticker": ticker, "payload": out}
    except Exception:
        pass
    try:
        from decision_engine.production import get_latest  # type: ignore

        out = get_latest(ticker)
        if out:
            return {"ok": True, "object_type": "CompanyDecision", "ticker": ticker, "payload": out}
    except Exception:
        pass
    # Deterministic placeholder from ticker context — orchestration must not invent BUY/SELL
    return {
        "ok": True,
        "object_type": "CompanyDecision",
        "ticker": ticker,
        "payload": {
            "ticker": ticker,
            "available": False,
            "note": "Company decision provider soft-unavailable; no recommendation invented",
        },
        "soft_missing": True,
    }


def _retrieve_portfolio_graph(ctx: dict[str, Any]) -> dict[str, Any]:
    pid = str(ctx.get("portfolio_id") or "agi-core-equity")
    try:
        from institutional_portfolio.production import get_portfolio_graph

        out = get_portfolio_graph(pid, rebuild=True, include_company_graphs=False)
        return {"ok": bool(out.get("ok")), "object_type": "PortfolioGraph", "payload": out}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "object_type": "PortfolioGraph", "error": str(exc)}


def _retrieve_portfolio_risk(ctx: dict[str, Any]) -> dict[str, Any]:
    pid = str(ctx.get("portfolio_id") or "agi-core-equity")
    try:
        from institutional_portfolio_risk.production import evaluate_portfolio_risk

        out = evaluate_portfolio_risk({"portfolio_id": pid})
        return {"ok": bool(out.get("ok")), "object_type": "PortfolioRisk", "payload": out}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "object_type": "PortfolioRisk", "error": str(exc)}


def _retrieve_policy(ctx: dict[str, Any]) -> dict[str, Any]:
    pid = str(ctx.get("portfolio_id") or "agi-core-equity")
    profile = str(ctx.get("policy") or "family_office")
    try:
        from institutional_policy.production import check_policy

        out = check_policy({"portfolio_id": pid, "policy": profile})
        return {"ok": bool(out.get("ok")), "object_type": "PolicyAssessment", "payload": out}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "object_type": "PolicyAssessment", "error": str(exc)}


def _retrieve_portfolio_decision(ctx: dict[str, Any]) -> dict[str, Any]:
    pid = str(ctx.get("portfolio_id") or "agi-core-equity")
    try:
        from institutional_portfolio_decision.production import decide_portfolio

        out = decide_portfolio({"portfolio_id": pid, "policy": ctx.get("policy") or "family_office"})
        return {"ok": bool(out.get("ok")), "object_type": "PortfolioDecision", "payload": out}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "object_type": "PortfolioDecision", "error": str(exc)}


def _retrieve_committee(ctx: dict[str, Any]) -> dict[str, Any]:
    pid = str(ctx.get("portfolio_id") or "agi-core-equity")
    try:
        from institutional_committee.production import review_committee

        out = review_committee({"portfolio_id": pid, "policy": ctx.get("policy") or "family_office"})
        return {"ok": bool(out.get("ok")), "object_type": "CommitteeResolution", "payload": out}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "object_type": "CommitteeResolution", "error": str(exc)}


def _retrieve_observation(ctx: dict[str, Any]) -> dict[str, Any]:
    ticker = str((ctx.get("entities") or [""])[0] or "").upper()
    try:
        from institutional_observation.production import get_observations  # type: ignore

        out = get_observations(ticker) if ticker else {"ok": False}
        return {"ok": bool(out.get("ok", True)), "object_type": "Observation", "payload": out}
    except Exception:
        return {
            "ok": True,
            "object_type": "Observation",
            "payload": {"available": False, "ticker": ticker},
            "soft_missing": True,
        }


def _retrieve_forecast(ctx: dict[str, Any]) -> dict[str, Any]:
    ticker = str((ctx.get("entities") or [""])[0] or "").upper()
    try:
        from institutional_forecasting.production import get_company_scenarios  # type: ignore

        out = get_company_scenarios(ticker) if ticker else {"ok": False}
        return {"ok": bool(out.get("ok", True)), "object_type": "Forecast", "payload": out}
    except Exception:
        return {
            "ok": True,
            "object_type": "Forecast",
            "payload": {"available": False, "ticker": ticker},
            "soft_missing": True,
        }


def _retrieve_research(ctx: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": True,
        "object_type": "Research",
        "payload": {
            "note": "Research objects consulted via registry; detailed IRP soft-unavailable",
            "question": ctx.get("question"),
        },
        "soft_missing": True,
    }


def bootstrap_default_registry() -> None:
    if _REGISTRY:
        return
    register(
        "CompanyDecision",
        routes=["buy", "sell", "hold", "recommendation", "investment thesis", "valuation", "should i"],
        provider="institutional_decision",
        planner="company",
        description="Company InstitutionalDecision (referential)",
        retrieve=_retrieve_company_decision,
    )
    register(
        "PortfolioGraph",
        routes=["portfolio", "holdings", "allocation", "exposure", "what do we own"],
        provider="institutional_portfolio",
        planner="portfolio",
        description="PKG-01 InstitutionalPortfolio",
        retrieve=_retrieve_portfolio_graph,
    )
    register(
        "PortfolioRisk",
        routes=["portfolio risk", "risk", "drawdown", "concentration", "stress", "liquidity", "hhi"],
        provider="institutional_portfolio_risk",
        planner="portfolio",
        description="PRE-01 InstitutionalPortfolioRisk",
        retrieve=_retrieve_portfolio_risk,
    )
    register(
        "PolicyAssessment",
        routes=["policy", "mandate", "violation", "compliance", "constraint", "allowed"],
        provider="institutional_policy",
        planner="governance",
        description="PCE-01 InstitutionalPolicyAssessment",
        retrieve=_retrieve_policy,
    )
    register(
        "PortfolioDecision",
        routes=["reduce", "increase", "trim", "rebalance", "portfolio decision", "which holdings"],
        provider="institutional_portfolio_decision",
        planner="portfolio",
        description="CIO-01 InstitutionalPortfolioDecision",
        retrieve=_retrieve_portfolio_decision,
    )
    register(
        "CommitteeResolution",
        routes=["committee", "approved", "rejected", "deferred", "escalated", "why was"],
        provider="institutional_committee",
        planner="governance",
        description="ICE-01 InstitutionalCommitteeResolution",
        retrieve=_retrieve_committee,
    )
    register(
        "Observation",
        routes=["observation", "monitor", "alert", "what changed", "today"],
        provider="institutional_observation",
        planner="market",
        description="IO-01 observations",
        retrieve=_retrieve_observation,
    )
    register(
        "Forecast",
        routes=["forecast", "scenario", "outlook", "rbi"],
        provider="institutional_forecasting",
        planner="market",
        description="FG-01 forecasts/scenarios",
        retrieve=_retrieve_forecast,
    )
    register(
        "Research",
        routes=["research", "note", "briefing", "explain"],
        provider="research",
        planner="company",
        description="Research packages (soft)",
        retrieve=_retrieve_research,
    )


# Bootstrap on import
bootstrap_default_registry()
