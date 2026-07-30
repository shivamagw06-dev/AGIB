"""AGI V1.3 — Institutional Morning Office tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from investment_office.v13_schema import (
    IO_V13_PLATFORM,
    IO_V13_PRODUCT,
    IO_V13_VERSION,
    IO_V13_WORKSTREAM_ID,
    MISSION,
    POLICY,
    RESEARCH_QUEUE_STAGES,
)
from investment_office.production import (
    calendar_v13,
    daily_brief,
    generate_morning_brief,
    morning_office,
    morning_overview,
    opportunities_v13,
    refresh_morning_office,
    research_queue_v13,
    soft_slice_morning_office,
)


def test_io_v13_identity():
    overview = morning_overview()
    assert overview["ok"] is True
    assert overview["admin_only"] is True
    assert overview["workstream_id"] == IO_V13_WORKSTREAM_ID
    assert overview["product"] == IO_V13_PRODUCT
    assert overview["platform"] == IO_V13_PLATFORM
    assert overview["version"] == IO_V13_VERSION
    assert overview["policy"]["buy_sell"] is False
    assert overview["policy"]["issues_recommendations"] is False
    assert "Morning Office" in MISSION or "morning" in MISSION.lower()
    assert POLICY["monitoring_only"] is True


def test_overview_has_required_surfaces():
    overview = morning_overview()
    for key in (
        "header",
        "top_summary",
        "executive_brief",
        "priorities",
        "overnight_activity",
        "research_queue",
        "opportunities",
        "market_summary",
        "macro",
        "calendar",
        "portfolio_monitor",
        "sector_monitor",
        "metrics",
        "analyst_workspace",
        "investment_calendar",
        "ai_summary",
        "actions",
        "links",
    ):
        assert key in overview, key

    top = overview["top_summary"]
    for k in (
        "market_mood",
        "global_risk",
        "research_queue",
        "companies_updated_overnight",
        "critical_alerts",
        "macro_events_today",
        "earnings_today",
        "institutional_coverage_complete",
    ):
        assert k in top, k

    assert overview["header"]["greeting"] == "Good Morning"
    assert overview["header"]["title"] == "Investment Office"
    assert overview["links"]["knowledge_operations"] == "/admin/knowledge-operations"
    assert "open_knowledge_operations" in overview["actions"]


def test_research_queue_stages():
    q = research_queue_v13()
    assert q["ok"] is True
    stages = q.get("stages") or {}
    for stage in RESEARCH_QUEUE_STAGES:
        assert stage in stages
    assert isinstance(q.get("items"), list)


def test_opportunities_are_monitoring_only():
    opp = opportunities_v13()
    assert opp["ok"] is True
    assert opp["issues_recommendations"] is False
    assert "not recommendation" in (opp.get("note") or "").lower()


def test_morning_slices_and_mutations():
    mo = morning_office()
    assert mo["ok"] is True
    assert "executive_brief" in mo
    assert "priorities" in mo

    brief = daily_brief()
    assert brief["ok"] is True
    assert brief["policy"]["buy_sell"] is False

    cal = calendar_v13()
    assert cal["ok"] is True
    assert "earnings_today" in cal

    refreshed = refresh_morning_office()
    assert refreshed["ok"] is True
    assert "overview" in refreshed

    gen = generate_morning_brief()
    assert gen["ok"] is True
    assert gen["issues_recommendations"] is False
    assert "ai_summary" in gen
    assert "executive_brief" in gen

    soft = soft_slice_morning_office()
    assert soft["status"] in {"ok", "error"}
    assert soft["admin_only"] is True
    if soft["status"] == "ok":
        assert soft["buy_sell"] is False
        assert soft["route"] == "/admin/investment-office"
