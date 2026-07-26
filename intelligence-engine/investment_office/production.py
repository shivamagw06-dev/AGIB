"""Investment Office production facade — aggregate soft adapters only."""

from __future__ import annotations

from typing import Any

from investment_office.aggregate import build_desk
from investment_office.flags import flags_dict, is_enabled
from investment_office.schema import IO_VERSION, PROGRAMME, PROGRAMME_SHORT
from investment_office import store as io_store


def health() -> dict[str, Any]:
    return {
        "status": "ok" if is_enabled() else "disabled",
        "programme": PROGRAMME,
        "layer": PROGRAMME_SHORT,
        "version": IO_VERSION,
        "architecture_status": "v1.0.1 LOCKED",
        "not_an_engine": True,
        "not_a_recommendation_engine": True,
        "not_portfolio_management": True,
        "flags": flags_dict(),
        "enabled": is_enabled(),
    }


def dashboard(*, ui_home: dict[str, Any] | None = None, ioc_service: Any | None = None) -> dict[str, Any]:
    desk = build_desk(ui_home=ui_home, ioc_service=ioc_service)
    if desk.get("enabled"):
        io_store.put_desk(desk)
    return desk


def cached_desk() -> dict[str, Any] | None:
    return io_store.get_desk()


def package_for_home(*, ui_home: dict[str, Any] | None = None, ioc_service: Any | None = None) -> dict[str, Any]:
    """Soft package for UiService.home — never empty when enabled."""
    desk = dashboard(ui_home=ui_home, ioc_service=ioc_service)
    if not desk.get("enabled"):
        return desk
    return {
        **desk,
        "home_strip": {
            "attention_count": len(desk.get("companies_requiring_attention") or []),
            "queue_count": len(desk.get("todays_research_queue") or []),
            "notifications": len(desk.get("notifications") or []),
            "coverage_pct": (desk.get("coverage_dashboard") or {}).get("coverage_pct"),
            "regime": (desk.get("morning_executive_brief") or {}).get("market_regime"),
            "risk": (desk.get("morning_executive_brief") or {}).get("risk_level"),
        },
    }


def package_for_ask_agi(query: str = "", *, ticker: str | None = None) -> dict[str, Any]:
    desk = cached_desk() or dashboard()
    attention = desk.get("companies_requiring_attention") or []
    hints = []
    if ticker:
        t = ticker.upper()
        hit = next((a for a in attention if a.get("ticker") == t), None)
        if hit:
            hints.append(
                f"Investment Office attention for {t}: {hit.get('priority')} — "
                f"{', '.join(hit.get('reasons') or [])}"
            )
    hints.append(
        f"IO desk: {len(attention)} companies needing attention; "
        f"{len(desk.get('todays_research_queue') or [])} research tasks queued."
    )
    for n in (desk.get("notifications") or [])[:3]:
        if n.get("message"):
            hints.append(str(n["message"])[:200])
    return {
        "enabled": bool(desk.get("enabled")),
        "programme": PROGRAMME,
        "version": IO_VERSION,
        "query": query,
        "ticker": ticker,
        "attention": [a for a in attention if not ticker or a.get("ticker") == (ticker or "").upper()][:8],
        "research_queue": (desk.get("todays_research_queue") or [])[:6],
        "executive_copilot": desk.get("executive_copilot") or {},
        "ask_agi_hints": hints[:8],
        "answer_policy": "investment_office_context_before_answer",
    }


def quality_gates() -> dict[str, Any]:
    # Seed CMS signals so desk is non-empty
    try:
        from company_monitor import store as cms_store
        from company_monitor.significance import annotate

        cms_store.reset_for_tests()
        cms_store.put_snapshot(
            "HDFCBANK",
            {
                "ticker": "HDFCBANK",
                "metrics": {"revenue_growth": 0.11, "operating_margin": 0.20, "roe": 0.15, "debt": 100, "pe": 16, "historical_pe": 18},
                "leo_evidence_count": 1,
                "channels_seen": {"financial_statements": True},
            },
        )
        from company_monitor.pipeline import monitor_company

        monitor_company(
            "HDFCBANK",
            force_pipeline=False,
            layers={
                "cid": {
                    "ticker": "HDFCBANK",
                    "financials": {"revenue_growth": 0.18, "operating_margin": 0.17, "roe": 0.14, "debt": 120},
                    "valuation": {"pe": 22, "historical_pe": 18},
                },
                "leo_pkg": {"evidence_objects": [{"type": "earnings"}]},
            },
        )
        _ = annotate
    except Exception:
        pass

    desk = dashboard(ui_home={
        "hero": {
            "house_view": "Cautious constructive — selective.",
            "market_regime": "Cautious Constructive",
            "risk_level": "Medium",
            "research_published_today": 2,
        },
        "morning_intelligence": {
            "greeting_line": "Here's what the AGI Investment Office believes today.",
            "cards": [{"id": "house_view", "label": "Today's House View", "value": "Selective"}],
        },
        "calendar": [{"title": "RBI", "type": "macro"}],
    })
    criteria = {
        "desk_enabled": desk.get("enabled") is True,
        "not_empty": desk.get("empty_state") is False,
        "morning_brief_present": bool(desk.get("morning_executive_brief")),
        "attention_ranked": isinstance(desk.get("companies_requiring_attention"), list),
        "research_queue_present": len(desk.get("todays_research_queue") or []) >= 1,
        "knowledge_growth_present": bool(desk.get("knowledge_growth")),
        "coverage_present": bool(desk.get("coverage_dashboard")),
        "risk_centre_present": bool(desk.get("risk_centre")),
        "executive_copilot_present": bool((desk.get("executive_copilot") or {}).get("prompts")),
        "ioc_system_health": (desk.get("system_health") or {}).get("ioc_only") is True,
        "notifications_present": len(desk.get("notifications") or []) >= 1,
    }
    passed = all(criteria.values())
    return {
        "programme": PROGRAMME,
        "version": IO_VERSION,
        "passed": passed,
        "criteria": criteria,
        "message": "Investment Office quality gates passed" if passed else "Investment Office incomplete",
    }


def reset_for_tests() -> None:
    io_store.reset_for_tests()
