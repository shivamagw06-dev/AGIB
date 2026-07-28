"""Morning Government Board."""

from __future__ import annotations

from datetime import date
from typing import Any

from knowledge_factory.government_intelligence import store as igri_store
from knowledge_factory.government_intelligence.schema import IGRI_VERSION


def government_dashboard(*, ensure: bool = True) -> dict[str, Any]:
    if ensure and igri_store.policy_count() == 0:
        from knowledge_factory.government_intelligence.pipeline import run_government_intelligence_pipeline

        run_government_intelligence_pipeline()

    policies = igri_store.list_policies()
    today = date.today().isoformat()
    todays = [p for p in policies if str(p.get("announcement_date") or "")[:10] == today]
    rbi = [p for p in policies if p.get("domain") == "rbi"]
    budget = [p for p in policies if p.get("domain") == "budget"]
    sebi = [p for p in policies if p.get("domain") == "sebi"]
    gst = [p for p in policies if p.get("domain") == "gst"]
    pli = [p for p in policies if p.get("domain") == "pli"]
    high = [p for p in policies if p.get("impact_level") in {"Critical", "High"}]
    pending = sum(1 for p in policies if not (p.get("validation") or {}).get("gate_pass", True))
    ready = sum(1 for p in policies if (p.get("validation") or {}).get("institutional_ready"))
    timeline = igri_store.get_timeline() or {}
    last = igri_store.last_run() or {}

    return {
        "igri_version": IGRI_VERSION,
        "title": "Institutional Government & Regulatory Intelligence — Morning Board",
        "north_star": "institutional_government_intelligence_coverage",
        "kpi_rule": "Connect policy to markets with evidence — never political opinion or forecasts.",
        "architecture_frozen": "REASONING_V1",
        "todays_policies": len(todays),
        "new_rbi_releases": len(rbi),
        "budget_events": len(budget),
        "sebi_circulars": len(sebi),
        "gst_changes": len(gst),
        "pli_updates": len(pli),
        "high_impact_policies": len(high),
        "pending_validation": pending,
        "coverage": ready,
        "coverage_pct": round(100.0 * ready / (len(policies) or 1), 2),
        "validation_failures": pending,
        "policy_count": len(policies),
        "body_count": len(igri_store.list_bodies()),
        "replay_status": "operational" if timeline.get("point_in_time") else "unavailable",
        "timeline_policy_count": timeline.get("policy_count") or 0,
        "last_pipeline_status": last.get("status"),
        "last_runtime_seconds": last.get("runtime_seconds"),
        "fabricated": False,
        "political_opinion": False,
        "policy_forecast": False,
    }


__all__ = ["government_dashboard"]
