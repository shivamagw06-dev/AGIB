"""Mission Control production facade — read-only diagnostics aggregation."""

from __future__ import annotations

from typing import Any

from mission_control.aggregate import build_mission_control
from mission_control.flags import flags_dict, is_enabled
from mission_control.schema import MISSION_CONTROL_VERSION, PROGRAMME, PROGRAMME_SHORT
from mission_control import store as mc_store


def health() -> dict[str, Any]:
    return {
        "status": "ok" if is_enabled() else "disabled",
        "programme": PROGRAMME,
        "layer": PROGRAMME_SHORT,
        "version": MISSION_CONTROL_VERSION,
        "architecture_status": "v1.0.1 LOCKED",
        "read_only": True,
        "not_an_engine": True,
        "not_client_facing": True,
        "never_modifies_research": True,
        "flags": flags_dict(),
        "enabled": is_enabled(),
    }


def dashboard(*, ioc_service: Any | None = None, force: bool = False) -> dict[str, Any]:
    if not force:
        cached = mc_store.get_dashboard()
        if cached:
            return cached
    desk = build_mission_control(ioc_service=ioc_service)
    if desk.get("enabled"):
        mc_store.put_dashboard(desk)
    return desk


def acknowledge_alert(alert_id: str, *, actor: str | None = None) -> dict[str, Any]:
    """Acknowledge only — never mutates research / house views."""
    return mc_store.acknowledge(alert_id, actor=actor)


def system_report(*, ioc_service: Any | None = None) -> dict[str, Any]:
    desk = mc_store.get_dashboard() or dashboard(ioc_service=ioc_service)
    sections = {
        "platform_health": desk.get("executive_status"),
        "api_health": desk.get("api_status"),
        "knowledge_growth": desk.get("knowledge_growth"),
        "coverage": desk.get("coverage_dashboard"),
        "learning": desk.get("academy"),
        "research": desk.get("research_pipeline"),
        "predictions": desk.get("prediction_intelligence"),
        "errors": [
            a for a in (desk.get("alerts_centre") or []) if not a.get("acknowledged")
        ][:40],
        "warnings": [
            p for p in (desk.get("platform_status") or []) if p.get("current_status") == "Warning"
        ],
        "recommendations": [
            "Investigate Critical / Offline platforms first",
            "Acknowledge resolved alerts in Alerts Centre",
            "Review CMS companies needing House View review",
            "Check IOC provider circuits for Red APIs",
        ],
        "architecture_map": desk.get("architecture_map"),
        "deployment": desk.get("deployment_centre"),
    }
    return {
        "ok": True,
        "report_type": "mission_control_system_report",
        "title": "AGI Mission Control System Report",
        "generated_at": desk.get("generated_at"),
        "version": MISSION_CONTROL_VERSION,
        "read_only": True,
        "sections": sections,
        **sections,
    }


def quality_gates() -> dict[str, Any]:
    # Prefer cached desk — never rebuild a second full aggregate for gates.
    desk = mc_store.get_dashboard() or dashboard()
    criteria = {
        "enabled": desk.get("enabled") is True,
        "read_only": desk.get("read_only") is True,
        "executive_status_present": bool(desk.get("executive_status")),
        "platforms_present": len(desk.get("platform_status") or []) >= 10,
        "engines_present": len(desk.get("engine_status") or []) >= 5,
        "apis_present": len(desk.get("api_status") or []) >= 5,
        "knowledge_growth_present": bool(desk.get("knowledge_growth")),
        "coverage_present": bool(desk.get("coverage_dashboard")),
        "company_monitor_present": bool(desk.get("company_monitor")),
        "architecture_map_present": len((desk.get("architecture_map") or {}).get("nodes") or []) >= 10,
        "events_present": isinstance(desk.get("live_event_stream"), list),
        "copilot_present": bool((desk.get("executive_copilot") or {}).get("prompts")),
        "never_mutates": desk.get("never_modifies_research") is True,
    }
    passed = all(criteria.values())
    return {
        "programme": PROGRAMME,
        "version": MISSION_CONTROL_VERSION,
        "passed": passed,
        "criteria": criteria,
        "message": "Mission Control quality gates passed" if passed else "Mission Control incomplete",
    }


def reset_for_tests() -> None:
    mc_store.reset_for_tests()
