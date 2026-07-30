"""AGIB Agent Map — Mission Control inventory of agents + working status.

Read-only diagnostics. Never modifies research / house views / recommendations.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Callable

AGENT_MAP_VERSION = "agent-map-v1.0.0"


def _env_truthy(name: str, default: str = "false") -> bool:
    return str(os.getenv(name, default)).strip().lower() in {"1", "true", "yes", "on"}


def _env_falsey(name: str, default: str = "false") -> bool:
    return not _env_truthy(name, default)


def _soft(fn: Callable[[], Any], default: Any = None) -> Any:
    try:
        return fn()
    except Exception:
        return default


def _probe_import(module: str, attr: str | None = None) -> tuple[bool, str | None]:
    try:
        mod = __import__(module, fromlist=[attr] if attr else ["__name__"])
        if attr:
            getattr(mod, attr)
        return True, None
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)[:160]


def _probe_health(module: str, fn_name: str = "health") -> tuple[str, dict[str, Any]]:
    ok, err = _probe_import(module, fn_name)
    if not ok:
        return "off", {"error": err or "import_failed"}
    try:
        mod = __import__(module, fromlist=[fn_name])
        body = getattr(mod, fn_name)()
        if not isinstance(body, dict):
            return "soft", {"probe": "non_dict"}
        status = str(body.get("status") or "").lower()
        if body.get("enabled") is False or status in {"disabled", "offline"}:
            return "off", body
        if status in {"ok", "healthy", "ready", "live"}:
            return "working", body
        if status in {"soft", "partial", "degraded", "warning"}:
            return "soft", body
        return "soft", body
    except Exception as exc:  # noqa: BLE001
        return "degraded", {"error": str(exc)[:160]}


def _registry_agents() -> list[str]:
    return _soft(
        lambda: list(
            __import__("app.agents.registry", fromlist=["list_agents"]).list_agents()  # type: ignore[attr-defined]
        ),
        [],
    ) or _soft(
        lambda: list(
            getattr(
                __import__("app.agents.registry", fromlist=["_REGISTRY"]),
                "_REGISTRY",
                {},
            ).keys()
        ),
        [],
    )


def _cio_status(agent_id: str) -> str:
    registered = set(_registry_agents() or [])
    # Ensure bootstrap ran
    if not registered:
        _soft(
            lambda: __import__(
                "app.agents.registry", fromlist=["bootstrap_registry"]
            ).bootstrap_registry()
        )
        registered = set(_registry_agents() or [])
    if agent_id in registered:
        return "working"
    # Source files present?
    path_map = {
        "macro_economist": "app.agents.cio_desk.macro_economist",
        "news_analyst": "app.agents.cio_desk.news_analyst",
        "market_analyst": "app.agents.cio_desk.market_analyst",
        "risk_manager": "app.agents.cio_desk.risk_manager",
        "cio": "app.agents.cio_synthesizer",
        "smoke_analyst": "app.agents.stubs",
    }
    mod = path_map.get(agent_id)
    if mod and _probe_import(mod)[0]:
        return "soft"
    return "orphan"


def _flag_status(enabled: bool, *, soft_when_on: bool = False) -> str:
    if not enabled:
        return "off"
    return "soft" if soft_when_on else "working"


# Catalog: static responsibilities + sources; status resolved at runtime.
_CATALOG: list[dict[str, Any]] = [
    # —— CIO desk ——
    {
        "id": "macro_economist",
        "name": "Macro Economist",
        "group": "cio_desk",
        "responsibility": "India macro transmission from the morning briefing cache.",
        "sources": ["AGIB macro briefing cache"],
        "kind": "cio_agent",
    },
    {
        "id": "news_analyst",
        "name": "News Analyst",
        "group": "cio_desk",
        "responsibility": "Explain why overnight news matters for the desk.",
        "sources": ["Market briefing", "Pre-market briefing"],
        "kind": "cio_agent",
    },
    {
        "id": "market_analyst",
        "name": "Market Analyst",
        "group": "cio_desk",
        "responsibility": "Overnight / global market tone for the CIO desk.",
        "sources": ["Pre-market briefing"],
        "kind": "cio_agent",
    },
    {
        "id": "risk_manager",
        "name": "Risk Manager",
        "group": "cio_desk",
        "responsibility": "Invalidators and scenario risks for the morning desk.",
        "sources": ["Macro risks", "Pre-market scenarios"],
        "kind": "cio_agent",
    },
    {
        "id": "cio",
        "name": "Chief Investment Officer",
        "group": "cio_desk",
        "responsibility": "Synthesize desk agent outputs into an institutional thesis.",
        "sources": ["Peer CIO-desk agent outputs", "LLM synthesizer"],
        "kind": "cio_agent",
    },
    {
        "id": "smoke_analyst",
        "name": "Smoke Analyst",
        "group": "cio_desk",
        "responsibility": "Pipeline smoke probe with cited evidence.",
        "sources": ["AGIB macro briefing cache"],
        "kind": "cio_agent",
    },
    # —— IAF specialists ——
    {
        "id": "iaf_business",
        "name": "Business Analyst",
        "group": "institutional_analysts",
        "responsibility": "Franchise quality and durable competitive advantages.",
        "sources": ["Company Analysis", "Academy", "Annual reports"],
        "kind": "iaf",
        "module": "institutional_analysts.production",
    },
    {
        "id": "iaf_financial",
        "name": "Financial Analyst",
        "group": "institutional_analysts",
        "responsibility": "Earnings quality, cash generation, balance-sheet resilience.",
        "sources": ["Financial Intelligence", "Data Validation & Consensus"],
        "kind": "iaf",
        "module": "institutional_analysts.production",
    },
    {
        "id": "iaf_valuation",
        "name": "Valuation Analyst",
        "group": "institutional_analysts",
        "responsibility": "Whether expectations already priced in look expensive or cheap.",
        "sources": ["Valuation engine", "Financial Intelligence", "Market pack"],
        "kind": "iaf",
        "module": "institutional_analysts.production",
    },
    {
        "id": "iaf_market",
        "name": "Market Specialist",
        "group": "institutional_analysts",
        "responsibility": "Price, volume and liquidity signals for the name.",
        "sources": ["Market tape", "Company dossier", "Live market pack"],
        "kind": "iaf",
        "module": "institutional_analysts.production",
    },
    {
        "id": "iaf_sector",
        "name": "Sector Specialist",
        "group": "institutional_analysts",
        "responsibility": "Industry attractiveness and competitive structure.",
        "sources": ["Sector Intelligence", "Knowledge Factory", "Academy"],
        "kind": "iaf",
        "module": "institutional_analysts.production",
    },
    {
        "id": "iaf_macro",
        "name": "Macro Specialist",
        "group": "institutional_analysts",
        "responsibility": "Rates, inflation and growth transmission to the company.",
        "sources": ["Macro briefing", "Policy series"],
        "kind": "iaf",
        "module": "institutional_analysts.production",
    },
    {
        "id": "iaf_risk",
        "name": "Risk Specialist",
        "group": "institutional_analysts",
        "responsibility": "What can impair the thesis before the base case arrives.",
        "sources": ["Company Monitor", "Risk models"],
        "kind": "iaf",
        "module": "institutional_analysts.production",
    },
    {
        "id": "iaf_management",
        "name": "Management Specialist",
        "group": "institutional_analysts",
        "responsibility": "Governance quality and capital-allocation trust.",
        "sources": ["Annual reports", "Earnings calls", "IR decks"],
        "kind": "iaf",
        "module": "institutional_analysts.production",
    },
    {
        "id": "iaf_ownership",
        "name": "Ownership Specialist",
        "group": "institutional_analysts",
        "responsibility": "Promoter, FI and insider alignment.",
        "sources": ["Shareholding data", "Company dossier"],
        "kind": "iaf",
        "module": "institutional_analysts.production",
    },
    {
        "id": "iaf_committee",
        "name": "Investment Committee",
        "group": "institutional_analysts",
        "responsibility": "Consensus, conflicts, votes and committee minutes.",
        "sources": ["Specialist opinions"],
        "kind": "iaf",
        "module": "institutional_analysts.production",
    },
    {
        "id": "iaf_cio_editor",
        "name": "IAF CIO Editor",
        "group": "institutional_analysts",
        "responsibility": "Institutional prose from the committee package.",
        "sources": ["Committee package"],
        "kind": "iaf",
        "module": "institutional_analysts.production",
    },
    # —— Acquisition / gather ——
    {
        "id": "faa",
        "name": "Finance Acquisition Agent",
        "group": "acquisition",
        "responsibility": "Discover → fetch → process → index public finance evidence into FRE.",
        "sources": [
            "Exa",
            "Firecrawl",
            "Browserbase",
            "Tavily",
            "Playwright",
            "NSE",
            "BSE",
            "SEBI",
            "RBI",
            "MCA",
            "PIB",
            "Company IR",
            "RSS/news",
        ],
        "kind": "faa",
    },
    {
        "id": "faa_background_collector",
        "name": "FAA Background Collector",
        "group": "acquisition",
        "responsibility": "Periodic FAA snapshot refresh off the Ask path.",
        "sources": ["FAA connectors"],
        "kind": "faa_bg",
    },
    {
        "id": "acquisition_planner",
        "name": "Acquisition & API Planner",
        "group": "acquisition",
        "responsibility": "Plans what evidence to fetch; does not collect itself.",
        "sources": ["Provider catalog", "Cache policy"],
        "kind": "planner",
        "module": "acquisition_planner.production",
    },
    # —— LIDI collectors ——
    {
        "id": "lidi_nse_bhavcopy",
        "name": "LIDI · NSE Bhavcopy",
        "group": "live_collectors",
        "responsibility": "Daily NSE prices and volumes.",
        "sources": ["NSE bhavcopy"],
        "kind": "lidi",
        "module": "live_data.collectors.nse_bhavcopy",
    },
    {
        "id": "lidi_nse_announcements",
        "name": "LIDI · NSE Announcements",
        "group": "live_collectors",
        "responsibility": "Corporate announcements from NSE.",
        "sources": ["NSE announcements"],
        "kind": "lidi",
        "module": "live_data.collectors.nse_announcements",
    },
    {
        "id": "lidi_bse_corporate_actions",
        "name": "LIDI · BSE Corporate Actions",
        "group": "live_collectors",
        "responsibility": "Splits, bonus and dividend actions from BSE.",
        "sources": ["BSE corporate actions"],
        "kind": "lidi",
        "module": "live_data.collectors.bse_corporate_actions",
    },
    {
        "id": "lidi_rbi_dbie",
        "name": "LIDI · RBI DBIE",
        "group": "live_collectors",
        "responsibility": "Repo, liquidity and macro series from RBI DBIE.",
        "sources": ["RBI DBIE"],
        "kind": "lidi",
        "module": "live_data.collectors.rbi_dbie",
    },
    {
        "id": "lidi_company_ir",
        "name": "LIDI · Company IR",
        "group": "live_collectors",
        "responsibility": "Company IR filings and guidance pages.",
        "sources": ["Company IR websites"],
        "kind": "lidi",
        "module": "live_data.collectors.company_ir",
    },
    # —— KF source clients ——
    {
        "id": "kf_yahoo",
        "name": "KF Yahoo Client",
        "group": "knowledge_factory",
        "responsibility": "Company/market history for Knowledge Factory (fixture-first).",
        "sources": ["Yahoo Finance", "KF fixtures"],
        "kind": "kf_client",
        "module": "knowledge_factory.collectors.yahoo.client",
    },
    {
        "id": "kf_groww",
        "name": "KF Groww Client",
        "group": "knowledge_factory",
        "responsibility": "India market series for Knowledge Factory.",
        "sources": ["Groww", "KF fixtures"],
        "kind": "kf_client",
        "module": "knowledge_factory.collectors.groww.client",
    },
    {
        "id": "kf_nse",
        "name": "KF NSE Client",
        "group": "knowledge_factory",
        "responsibility": "NSE series into Knowledge Factory.",
        "sources": ["NSE", "KF fixtures"],
        "kind": "kf_client",
        "module": "knowledge_factory.collectors.nse.client",
    },
    {
        "id": "kf_bse",
        "name": "KF BSE Client",
        "group": "knowledge_factory",
        "responsibility": "BSE series into Knowledge Factory.",
        "sources": ["BSE", "KF fixtures"],
        "kind": "kf_client",
        "module": "knowledge_factory.collectors.bse.client",
    },
    {
        "id": "kf_rbi",
        "name": "KF RBI Client",
        "group": "knowledge_factory",
        "responsibility": "RBI macro into Knowledge Factory.",
        "sources": ["RBI", "KF fixtures"],
        "kind": "kf_client",
        "module": "knowledge_factory.collectors.rbi.client",
    },
    {
        "id": "kf_fred",
        "name": "KF FRED Client",
        "group": "knowledge_factory",
        "responsibility": "Global macro series from FRED.",
        "sources": ["FRED", "KF fixtures"],
        "kind": "kf_client",
        "module": "knowledge_factory.collectors.fred.client",
    },
    {
        "id": "kf_world_bank",
        "name": "KF World Bank Client",
        "group": "knowledge_factory",
        "responsibility": "World Bank macro indicators.",
        "sources": ["World Bank", "KF fixtures"],
        "kind": "kf_client",
        "module": "knowledge_factory.collectors.world_bank.client",
    },
    # —— Offices ——
    {
        "id": "research_office",
        "name": "Research Office",
        "group": "offices",
        "responsibility": "Knowledge-only morning research desk / publications.",
        "sources": ["Knowledge Factory", "Institutional Scheduler"],
        "kind": "office",
        "module": "research_office.production",
    },
    {
        "id": "investment_office",
        "name": "Investment Office",
        "group": "offices",
        "responsibility": "Executive operating cockpit — briefs, queues, coverage.",
        "sources": ["CMS", "CIO desks", "AGIB caches"],
        "kind": "office",
        "module": "investment_office.production",
    },
    {
        "id": "ite_thesis",
        "name": "Investment Thesis Office",
        "group": "offices",
        "responsibility": "Why is this interesting? (ITE).",
        "sources": ["Research packages"],
        "kind": "v4_office",
        "module": "institutional_investment_thesis.production",
        "ask_flag": "AGI_V4_OFFICES_IN_ASK",
    },
    {
        "id": "ido_decision",
        "name": "Decision Office",
        "group": "offices",
        "responsibility": "Governance framing for institutional action (IDO).",
        "sources": ["Thesis", "Committee"],
        "kind": "v4_office",
        "module": "institutional_decision_office.production",
        "ask_flag": "AGI_V4_OFFICES_IN_ASK",
    },
    {
        "id": "ipo_portfolio",
        "name": "Portfolio Office",
        "group": "offices",
        "responsibility": "Idea comparison context — ideas ≠ positions (IPO).",
        "sources": ["Thesis", "Decision packages"],
        "kind": "v4_office",
        "module": "institutional_portfolio_office.production",
        "ask_flag": "AGI_V4_OFFICES_IN_ASK",
    },
    {
        "id": "imo_monitoring",
        "name": "Monitoring Office",
        "group": "offices",
        "responsibility": "What changed? Review queue for monitored names (IMO).",
        "sources": ["Events", "Company Monitor"],
        "kind": "v4_office",
        "module": "institutional_monitoring_office.production",
        "ask_flag": "AGI_V4_OFFICES_IN_ASK",
    },
    {
        "id": "ilo_learning",
        "name": "Learning Office",
        "group": "offices",
        "responsibility": "Process memory from decisions/outcomes — not KF facts (ILO).",
        "sources": ["Decisions", "Forecast validation outcomes"],
        "kind": "v4_office",
        "module": "institutional_learning_office.production",
        "ask_flag": "AGI_V4_OFFICES_IN_ASK",
    },
    {
        "id": "continuous_gather_learn",
        "name": "Continuous Gather → Learn",
        "group": "ops",
        "responsibility": (
            "Autonomous Collect→Validate→Store→Extract→Evaluate→Learn loop "
            "using LIDI, KF HD, FAA, Scheduler, FVL, FLE, ILO, CAL."
        ),
        "sources": [
            "LIDI",
            "Knowledge Factory Historical Depth",
            "FAA",
            "Institutional Scheduler",
            "FVL",
            "FLE",
            "ILO",
            "CAL",
        ],
        "kind": "cgl",
        "module": "continuous_gather_learn.production",
    },
    {
        "id": "financial_statements_engine",
        "name": "Financial Statements Engine",
        "group": "ops",
        "responsibility": (
            "Canonical financial statements pipeline — ingest → raw evidence → "
            "orchestrator → parse → validate → warehouse → DME."
        ),
        "sources": ["NSE", "BSE", "MCA", "Company IR", "FSE Raw Evidence"],
        "kind": "office",
        "module": "financial_statements_engine.production",
    },
    {
        "id": "financial_data_operations",
        "name": "Financial Data Operations (FDO)",
        "group": "ops",
        "responsibility": (
            "Coverage, completeness, gap scheduling, ingestion/source metrics, "
            "and FDO Mission Control over the existing FSE pipeline."
        ),
        "sources": ["FSE Raw Evidence", "Orchestrator", "Collection metrics"],
        "kind": "office",
        "module": "financial_statements_engine.fdo.production",
    },
    {
        "id": "financial_intelligence",
        "name": "Financial Intelligence (FIRE-01)",
        "group": "ops",
        "responsibility": (
            "Evidence-backed narrative & trend intelligence over warehouse facts — "
            "what happened financially (no BUY/SELL)."
        ),
        "sources": ["Financial Warehouse", "Derived Metrics", "Validation", "Coverage"],
        "kind": "office",
        "module": "financial_intelligence.production",
    },
    {
        "id": "financial_drivers",
        "name": "Financial Drivers (FIRE-02)",
        "group": "ops",
        "responsibility": (
            "Deterministic cross-statement relationship & driver analysis — "
            "which relationships explain financial changes (no BUY/SELL)."
        ),
        "sources": ["Financial Warehouse", "Derived Metrics", "Validation", "Coverage"],
        "kind": "office",
        "module": "financial_intelligence.drivers.production",
    },
    {
        "id": "financial_knowledge",
        "name": "Financial Knowledge Base (FKB-01)",
        "group": "ops",
        "responsibility": (
            "Canonical definitions for metrics, ratios, relationships, thresholds, "
            "glossary and sector guidance — knowledge only, no analysis."
        ),
        "sources": ["Institutional financial knowledge catalogs"],
        "kind": "office",
        "module": "financial_knowledge.production",
    },
    {
        "id": "business_intelligence",
        "name": "Business Intelligence (FIRE-03)",
        "group": "ops",
        "responsibility": (
            "Evidence extraction from official disclosures — what management says about "
            "the business, strategy, risks, opportunities, and guidance (no BUY/SELL)."
        ),
        "sources": ["Institutional Documents (IDI)", "FKB glossary (soft refs)"],
        "kind": "office",
        "module": "business_intelligence.production",
    },
    # —— Learning / eval ——
    {
        "id": "forecast_validation_learning",
        "name": "Forecast Validation & Learning",
        "group": "learning",
        "responsibility": "Score forecasts against outcomes and emit learning records.",
        "sources": ["Forecasts", "Outcomes"],
        "kind": "learning",
        "module": "forecast_validation_learning.production",
    },
    {
        "id": "fle",
        "name": "Forecast Learning Engine",
        "group": "learning",
        "responsibility": "Calibration / learning consult for Ask (retrieval).",
        "sources": ["FLE store", "Forecast history"],
        "kind": "learning",
        "module": "app.fle.service",
    },
    {
        "id": "evaluation_agent",
        "name": "Evaluation Agent",
        "group": "learning",
        "responsibility": "Record predictions for later outcome scoring.",
        "sources": ["Local eval store"],
        "kind": "eval",
        "module": "app.eval.evaluation_agent",
    },
    {
        "id": "red_team",
        "name": "Red Team Lab",
        "group": "learning",
        "responsibility": "Blind adversarial evaluation — never trains reasoning.",
        "sources": ["Exam / probe suites"],
        "kind": "eval",
        "module": "red_team.production",
    },
    # —— Historical / continuous (seeded) ——
    {
        "id": "historical_market_intelligence",
        "name": "Historical Market Intelligence",
        "group": "historical",
        "responsibility": "Decades-scale market memory (seeded; Ask never collects).",
        "sources": ["Seeded market history"],
        "kind": "historical",
        "module": "historical_market_intelligence.production",
    },
    {
        "id": "historical_sector_intelligence",
        "name": "Historical Sector Intelligence",
        "group": "historical",
        "responsibility": "Immutable sector event memory (seeded).",
        "sources": ["Seeded sector history"],
        "kind": "historical",
        "module": "historical_sector_intelligence.production",
    },
    {
        "id": "historical_macro_intelligence",
        "name": "Historical Macro Intelligence",
        "group": "historical",
        "responsibility": "Long-run macro regime memory (seeded).",
        "sources": ["Seeded macro history"],
        "kind": "historical",
        "module": "historical_macro_intelligence.production",
    },
    {
        "id": "continuous_macro_knowledge",
        "name": "Continuous Macro Knowledge",
        "group": "historical",
        "responsibility": "Ongoing macro knowledge pipeline (seeded / ops).",
        "sources": ["RBI / global macro releases (seeded)"],
        "kind": "historical",
        "module": "continuous_macro_knowledge.production",
    },
    # —— Ops ——
    {
        "id": "cio_morning_scheduler",
        "name": "CIO Morning Scheduler",
        "group": "ops",
        "responsibility": "Node scheduler that triggers CIO desk research runs.",
        "sources": ["Node API → engine /v1/research/runs"],
        "kind": "ops_flag",
        "env": "CIO_MORNING_SCHEDULER",
    },
    {
        "id": "cms_ingest_worker",
        "name": "CMS Ingest Worker",
        "group": "ops",
        "responsibility": "Ingest CMS articles into institutional knowledge.",
        "sources": ["CMS / Supabase queue"],
        "kind": "ops_flag",
        "env": "CMS_INGEST_WORKER_MODE",
        "env_working_values": {"embedded", "external", "1", "true"},
    },
    {
        "id": "institutional_scheduler",
        "name": "Institutional Scheduler",
        "group": "ops",
        "responsibility": "Ops DAG soft-wire to LIDI / KF / Research Office.",
        "sources": ["Ops APIs"],
        "kind": "planner",
        "module": "institutional_scheduler.production",
    },
    {
        "id": "analyst_router",
        "name": "Institutional Analyst Router",
        "group": "ops",
        "responsibility": "Plans which analysts should participate for a question.",
        "sources": ["Research ontology"],
        "kind": "planner",
        "module": "analyst_router.production",
    },
]


GROUP_LABELS = {
    "cio_desk": "CIO Morning Desk",
    "institutional_analysts": "Institutional Analyst Framework",
    "acquisition": "Acquisition & Gathering",
    "live_collectors": "Live Collectors (LIDI)",
    "knowledge_factory": "Knowledge Factory Clients",
    "offices": "Investment / Research Offices",
    "learning": "Learning & Evaluation",
    "historical": "Historical & Continuous Knowledge",
    "ops": "Ops / Schedulers",
}


def _resolve_status(item: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    """Return (status, detail, probe)."""
    kind = item.get("kind")
    probe: dict[str, Any] = {}

    if kind == "cio_agent":
        st = _cio_status(str(item["id"]))
        detail = {
            "working": "Registered and available for CIO desk runs.",
            "soft": "Source present but not registered in the live agent registry.",
            "orphan": "Source missing — packaging agent removed or not bootstrapped.",
        }.get(st, "")
        return st, detail, probe

    if kind == "iaf":
        flag_on = _env_truthy("INSTITUTIONAL_ANALYSTS", "true") or _env_truthy(
            "ASK_AGI_IAF", "true"
        )
        if not flag_on:
            return "off", "IAF flags disabled.", probe
        st, body = _probe_health(str(item.get("module") or "institutional_analysts.production"))
        # IAF is soft-wire by design even when healthy.
        if st == "working":
            st = "soft"
        return st, "Soft-wired into Ask Answer Construction; uses existing engines, not raw APIs.", body

    if kind == "faa":
        faa_on = _env_truthy("FAA", "true")
        live = _env_truthy("FAA_LIVE_FETCH", "false")
        ask_blocked = _env_falsey("AIL_LIVE_FAA", "false")  # false means Ask must not call unbound acquire
        if not faa_on:
            return "off", "FAA flag disabled.", {"FAA": False}
        if live:
            return (
                "working",
                "FAA live fetch enabled. Ask path blocked from unbound acquire."
                if ask_blocked
                else "FAA live fetch enabled; Ask may call live FAA.",
                {"FAA": True, "FAA_LIVE_FETCH": True, "AIL_LIVE_FAA": _env_truthy("AIL_LIVE_FAA", "false")},
            )
        return "soft", "FAA module on but live fetch off.", {"FAA": True, "FAA_LIVE_FETCH": False}

    if kind == "faa_bg":
        if _env_truthy("FAA_BACKGROUND_COLLECTOR", "false"):
            return "working", "Background collector enabled.", {}
        if _env_truthy("CONTINUOUS_FAA_REFRESH", "true"):
            return "soft", "FAA refresh runs inside CGL post-market/overnight phases (Ask-isolated).", {
                "CONTINUOUS_FAA_REFRESH": True
            }
        return "off", "FAA_BACKGROUND_COLLECTOR=false (enable flag or CONTINUOUS_FAA_REFRESH).", {}

    if kind == "lidi":
        mod = str(item.get("module") or "")
        ok, err = _probe_import(mod)
        if not ok:
            return "orphan", err or "Collector module missing.", {}
        if _env_truthy("CONTINUOUS_GATHER_LEARN", "true") and _env_truthy("CONTINUOUS_LIDI", "true"):
            return "working", "LIDI activated via Continuous Gather→Learn (Ask-isolated).", {
                "CONTINUOUS_LIDI": True
            }
        ask_slim = _env_truthy("ASK_SLIM", "true")
        if ask_slim:
            return "soft", "Collector code live-capable; Ask slim skips live fan-out. Ops/scheduler can still run.", {
                "ASK_SLIM": True
            }
        return "soft", "Live-capable collector soft-wired; enable CONTINUOUS_GATHER_LEARN for autonomous loop.", {}

    if kind == "kf_client":
        mod = str(item.get("module") or "")
        ok, err = _probe_import(mod)
        if not ok:
            return "orphan", err or "KF client missing.", {}
        return "soft", "Fixture-first Knowledge Factory client (live optional via KF flags).", {}

    if kind == "v4_office":
        mod = str(item.get("module") or "")
        ask_on = _env_truthy(str(item.get("ask_flag") or "AGI_V4_OFFICES_IN_ASK"), "0")
        st, body = _probe_health(mod) if mod else ("off", {})
        if st == "orphan" or (isinstance(body, dict) and body.get("error") and "import" in str(body.get("error")).lower()):
            ok, err = _probe_import(mod)
            if not ok:
                return "orphan", err or "Office package missing.", body
        if not ask_on:
            # Module may still work via Mission Control / dedicated APIs.
            if st in {"working", "soft", "degraded"} or _probe_import(mod)[0]:
                return "soft", "Office package available; off inside Ask (AGI_V4_OFFICES_IN_ASK=0).", {
                    "AGI_V4_OFFICES_IN_ASK": False
                }
            return "off", "v4 office off in Ask and package unavailable.", {}
        return "working" if st == "working" else st, "v4 office enabled in Ask.", body

    if kind == "office":
        mod = str(item.get("module") or "")
        st, body = _probe_health(mod)
        if st == "working":
            return "soft", "Office soft-wire available for ops / cockpit.", body
        if st == "off" and _probe_import(mod)[0]:
            return "soft", "Office module importable.", body
        return st, "Office probe result.", body

    if kind == "learning":
        mod = str(item.get("module") or "")
        cgl_learn = _env_truthy("CONTINUOUS_GATHER_LEARN", "true") and _env_truthy(
            "CONTINUOUS_LEARNING_LOOP", "true"
        )
        if item["id"] == "fle":
            ok, err = _probe_import(mod, "FleService") if mod else (False, "missing")
            # FleService class name may differ — try module only
            if not ok:
                ok, err = _probe_import(mod)
            ask_slim = _env_truthy("ASK_SLIM", "true")
            if not ok:
                return "orphan", err or "FLE missing.", {}
            if cgl_learn:
                return "working", "FLE activated in Continuous Gather→Learn cycle.", {"ASK_SLIM": ask_slim}
            return (
                "soft",
                "FLE consult soft-wired; Ask slim may skip heavy fan-out.",
                {"ASK_SLIM": ask_slim},
            )
        st, body = _probe_health(mod) if mod else ("off", {})
        if cgl_learn and (st in {"working", "soft"} or (mod and _probe_import(mod)[0])):
            return "working", "Learning loop activated via Continuous Gather→Learn (durable archive).", body
        if st == "working":
            st = "soft"
        if st in {"off", "degraded"} and mod and _probe_import(mod)[0]:
            return "soft", "Learning module present (in-memory / soft retrieval).", body
        return st, "Learning / validation soft-wire.", body

    if kind == "eval":
        mod = str(item.get("module") or "")
        ok, err = _probe_import(mod)
        if not ok:
            return "orphan", err or "Eval module missing.", {}
        return "soft", "Evaluation / red-team available for ops; not continuous prod learning.", {}

    if kind == "historical":
        mod = str(item.get("module") or "")
        st, body = _probe_health(mod) if mod else ("off", {})
        if mod and _probe_import(mod)[0]:
            return "soft", "Seeded historical memory available; Ask never triggers collectors.", body
        return "orphan", "Historical module missing.", body

    if kind == "planner":
        mod = str(item.get("module") or "")
        st, body = _probe_health(mod) if mod else ("off", {})
        if st == "working":
            st = "soft"
        if mod and _probe_import(mod)[0] and st == "off":
            return "soft", "Planner soft-wire importable.", body
        return st if st != "working" else "soft", "Planner soft-wire.", body

    if kind == "cgl":
        if not _env_truthy("CONTINUOUS_GATHER_LEARN", "true"):
            return "off", "CONTINUOUS_GATHER_LEARN=false.", {}
        st, body = _probe_health("continuous_gather_learn.production")
        if st in {"working", "soft"}:
            return "working", "Continuous gather→learn loop enabled (Ask-isolated).", body
        if _probe_import("continuous_gather_learn.production")[0]:
            return "working", "CGL package available; background starts with engine lifespan.", body
        return "orphan", "CGL package missing.", body

    if kind == "ops_flag":
        env_name = str(item.get("env") or "")
        raw = os.getenv(env_name, "")
        allowed = item.get("env_working_values")
        if allowed:
            if str(raw).strip().lower() in {str(v).lower() for v in allowed} or _env_truthy(env_name, "false"):
                return "working", f"{env_name}={raw or 'set'}.", {env_name: raw}
            # CMS worker defaults to embedded on Node API even if unset in engine env
            if item["id"] == "cms_ingest_worker":
                return "soft", "CMS ingest typically runs on Node API (embedded); engine env may not mirror it.", {
                    env_name: raw or None
                }
            return "off", f"{env_name} not in working mode (value={raw or 'unset'}).", {env_name: raw}
        if _env_truthy(env_name, "false"):
            return "working", f"{env_name}=true.", {env_name: True}
        # CIO morning scheduler is on Node, not engine
        if item["id"] == "cio_morning_scheduler":
            return "soft", "Runs on Node API (CIO_MORNING_SCHEDULER); engine env may not mirror it.", {
                env_name: raw or None
            }
        return "off", f"{env_name} disabled or unset.", {env_name: raw}

    # Generic module probe
    mod = str(item.get("module") or "")
    if mod:
        st, body = _probe_health(mod)
        return st, "Module probe.", body
    return "unknown", "No probe configured.", {}


def build_agent_map() -> dict[str, Any]:
    agents: list[dict[str, Any]] = []
    counts = {"working": 0, "soft": 0, "off": 0, "orphan": 0, "degraded": 0, "unknown": 0}

    for item in _CATALOG:
        status, detail, probe = _resolve_status(item)
        if status not in counts:
            status = "unknown"
        counts[status] = counts.get(status, 0) + 1
        agents.append(
            {
                "id": item["id"],
                "name": item["name"],
                "group": item["group"],
                "group_label": GROUP_LABELS.get(item["group"], item["group"]),
                "responsibility": item["responsibility"],
                "sources": list(item.get("sources") or []),
                "status": status,
                "working": status == "working",
                "detail": detail,
                "probe": probe if isinstance(probe, dict) else {},
            }
        )

    groups: dict[str, dict[str, Any]] = {}
    for a in agents:
        g = a["group"]
        bucket = groups.setdefault(
            g,
            {
                "id": g,
                "label": a["group_label"],
                "agents": [],
                "counts": {"working": 0, "soft": 0, "off": 0, "orphan": 0, "degraded": 0, "unknown": 0},
            },
        )
        bucket["agents"].append(a)
        bucket["counts"][a["status"]] = bucket["counts"].get(a["status"], 0) + 1

    ask_slim = _env_truthy("ASK_SLIM", "true")
    faa_bg = _env_truthy("FAA_BACKGROUND_COLLECTOR", "false")
    offices_ask = _env_truthy("AGI_V4_OFFICES_IN_ASK", "0")

    return {
        "enabled": True,
        "read_only": True,
        "programme": "AGIB Agent Map",
        "version": AGENT_MAP_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total": len(agents),
            **counts,
            "working_or_soft": counts["working"] + counts["soft"],
            "headline": (
                f"{counts['working']} working · {counts['soft']} soft-wire · "
                f"{counts['off']} off · {counts['orphan']} orphan"
            ),
        },
        "production_flags": {
            "ASK_SLIM": ask_slim,
            "FAA": _env_truthy("FAA", "true"),
            "FAA_LIVE_FETCH": _env_truthy("FAA_LIVE_FETCH", "false"),
            "FAA_BACKGROUND_COLLECTOR": faa_bg,
            "AIL_LIVE_FAA": _env_truthy("AIL_LIVE_FAA", "false"),
            "AGI_V4_OFFICES_IN_ASK": offices_ask,
            "AGI_V4_OFFICE_PERSIST": _env_truthy("AGI_V4_OFFICE_PERSIST", "0"),
            "CIO_MORNING_SCHEDULER": os.getenv("CIO_MORNING_SCHEDULER"),
            "INSTITUTIONAL_ANALYSTS": _env_truthy("INSTITUTIONAL_ANALYSTS", "true"),
        },
        "status_legend": {
            "working": "Intended to run in production and currently available.",
            "soft": "Code/path available as soft-wire, seeded, or ops-only — not a continuous primary loop.",
            "off": "Disabled by production flag or configuration.",
            "orphan": "Source missing or not importable.",
            "degraded": "Module present but health probe failed.",
            "unknown": "Could not determine status.",
        },
        "groups": list(groups.values()),
        "agents": agents,
    }
