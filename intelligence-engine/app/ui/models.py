"""Client-facing UI contracts — no internal engine identifiers."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

UI_VERSION = "ui-aggregation-1.0.0"


class UiMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    surface: str
    sources: list[str] = Field(default_factory=list)
    ui_version: str = UI_VERSION
    architecture_status: str = "v1.0.1 LOCKED"


class HomeView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    meta: UiMeta
    market_brief: dict[str, Any] = Field(default_factory=dict)
    composite_view: dict[str, Any] = Field(default_factory=dict)
    market_regime: dict[str, Any] = Field(default_factory=dict)
    market_risk: dict[str, Any] = Field(default_factory=dict)
    todays_research: list[dict[str, Any]] = Field(default_factory=list)
    latest_published: list[dict[str, Any]] = Field(default_factory=list)
    latest_news: list[dict[str, Any]] = Field(default_factory=list)
    market_themes: list[dict[str, Any]] = Field(default_factory=list)
    economic_calendar: list[dict[str, Any]] = Field(default_factory=list)
    system_health: dict[str, Any] = Field(default_factory=dict)
    research_queue: list[dict[str, Any]] = Field(default_factory=list)
    # PPE V1 — Ask AGI homepage
    hero: dict[str, Any] = Field(default_factory=dict)
    popular_questions: list[dict[str, Any]] = Field(default_factory=list)
    feeds: dict[str, Any] = Field(default_factory=dict)
    top_companies: list[dict[str, Any]] = Field(default_factory=list)
    ask_placeholder: str = (
        "Ask AGI anything about markets, companies, investments, themes, "
        "macroeconomics, valuation or research..."
    )
    example_questions: list[str] = Field(default_factory=list)
    # Investment Office Homepage V1
    morning_intelligence: dict[str, Any] = Field(default_factory=dict)
    knowledge_feed: list[dict[str, Any]] = Field(default_factory=list)
    featured_research: list[dict[str, Any]] = Field(default_factory=list)
    market_dashboard: dict[str, Any] = Field(default_factory=dict)
    footer_metrics: dict[str, Any] = Field(default_factory=dict)
    newsletter: dict[str, Any] = Field(default_factory=dict)
    market_snapshot: list[dict[str, Any]] = Field(default_factory=list)
    market_session: dict[str, Any] = Field(default_factory=dict)


class CompanyView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    meta: UiMeta
    ticker: str
    overview: dict[str, Any] = Field(default_factory=dict)
    market_intelligence: dict[str, Any] = Field(default_factory=dict)
    research: dict[str, Any] = Field(default_factory=dict)
    evidence: dict[str, Any] = Field(default_factory=dict)
    portfolio: dict[str, Any] = Field(default_factory=dict)
    # AGI Product V1
    valuation_snapshot: dict[str, Any] = Field(default_factory=dict)
    product_meta: dict[str, Any] = Field(default_factory=dict)
    discovery: dict[str, Any] = Field(default_factory=dict)
    follow_up_questions: list[str] = Field(default_factory=list)
    knowledge_graph: dict[str, Any] = Field(default_factory=dict)
    prediction_timeline: list[dict[str, Any]] = Field(default_factory=list)


class SearchView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    meta: UiMeta
    question: str
    intent: str | None = None
    entities: dict[str, Any] = Field(default_factory=dict)
    answer: dict[str, Any] = Field(default_factory=dict)
    # Institutional answer blocks (PPE V1)
    executive_summary: str | None = None
    house_view: dict[str, Any] | None = None
    confidence: float | None = None
    investment_thesis: str | None = None
    bull_case: list[str] = Field(default_factory=list)
    bear_case: list[str] = Field(default_factory=list)
    key_risks: list[str] = Field(default_factory=list)
    key_catalysts: list[str] = Field(default_factory=list)
    why: list[str] = Field(default_factory=list)
    supporting_research: list[dict[str, Any]] = Field(default_factory=list)
    latest_articles: list[dict[str, Any]] = Field(default_factory=list)
    latest_news: list[dict[str, Any]] = Field(default_factory=list)
    conflicting_opinions: list[dict[str, Any]] = Field(default_factory=list)
    evidence_used: list[dict[str, Any]] = Field(default_factory=list)
    knowledge_timeline: list[dict[str, Any]] = Field(default_factory=list)
    knowledge_freshness: dict[str, Any] = Field(default_factory=dict)
    last_updated: str | None = None
    related_companies: list[str] = Field(default_factory=list)
    related_themes: list[str] = Field(default_factory=list)
    related_sectors: list[str] = Field(default_factory=list)
    recommendations: dict[str, Any] = Field(default_factory=dict)
    follow_up_questions: list[str] = Field(default_factory=list)
    hits: list[dict[str, Any]] = Field(default_factory=list)
    answer_policy: str = "institutional_evidence_pack"
    # IAX — Institutional Answer Experience
    market_regime: str | None = None
    freshness_indicator: str | None = None
    house_view_card: dict[str, Any] = Field(default_factory=dict)
    whats_changed: dict[str, Any] = Field(default_factory=dict)
    current_thesis: dict[str, Any] = Field(default_factory=dict)
    supporting_evidence: list[dict[str, Any]] = Field(default_factory=list)
    conflicting_evidence: list[dict[str, Any]] = Field(default_factory=list)
    research_panel: dict[str, Any] = Field(default_factory=dict)
    knowledge_graph: dict[str, Any] = Field(default_factory=dict)
    market_intelligence: list[dict[str, Any]] = Field(default_factory=list)
    charts: list[dict[str, Any]] = Field(default_factory=list)
    predictions: list[dict[str, Any]] = Field(default_factory=list)
    related_ideas: dict[str, Any] = Field(default_factory=dict)
    portfolio_context: dict[str, Any] = Field(default_factory=dict)
    workspace: dict[str, Any] = Field(default_factory=dict)
    # IRP V1 — Institutional Reasoning Pipeline (Ask AGI briefing layer)
    irp: dict[str, Any] = Field(default_factory=dict)
    # KF1 — Knowledge Foundation objects resolved before documents
    knowledge_foundation: dict[str, Any] = Field(default_factory=dict)
    # KCV1 — Knowledge Corpus consult (primary source of truth before documents)
    knowledge_corpus: dict[str, Any] = Field(default_factory=dict)
    # AOI v1 — public acquisition structured knowledge soft retrieval
    open_intelligence: dict[str, Any] = Field(default_factory=dict)
    # EVE v1 — verified evidence / conflicts / confidence for Ask AGI
    evidence_verification: dict[str, Any] = Field(default_factory=dict)
    # IIE v1 — structured investment intelligence before reasoning
    investment_intelligence: dict[str, Any] = Field(default_factory=dict)
    # FLE v1 — forecast history, calibration and learning before reasoning
    forecast_learning: dict[str, Any] = Field(default_factory=dict)
    # MEE v1 — canonical market events / what changed before reasoning
    market_events: dict[str, Any] = Field(default_factory=dict)
    # CAE v1 — unified context assembly package (orchestration gateway)
    context_assembly: dict[str, Any] = Field(default_factory=dict)
    # IB v1 — intelligence bus soft emit metadata (Ask AGI activity)
    intelligence_bus: dict[str, Any] = Field(default_factory=dict)
    institutional_briefing: dict[str, Any] = Field(default_factory=dict)
    sector_intelligence: dict[str, Any] = Field(default_factory=dict)
    company_intelligence: dict[str, Any] = Field(default_factory=dict)
    current_outlook: str | None = None
    key_drivers: list[str] = Field(default_factory=list)
    valuation_perspective: str | None = None
    macro_drivers: list[str] = Field(default_factory=list)
    sector_drivers: list[str] = Field(default_factory=list)
    company_leaders: list[str] = Field(default_factory=list)
    historical_comparison: str | None = None


class TimelineView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    meta: UiMeta
    entity: str
    events: list[dict[str, Any]] = Field(default_factory=list)
    predictions: list[dict[str, Any]] = Field(default_factory=list)


class ArticleView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    meta: UiMeta
    article_id: str
    related_companies: list[str] = Field(default_factory=list)
    related_themes: list[str] = Field(default_factory=list)
    knowledge_graph: dict[str, Any] | None = None
    research_timeline: list[dict[str, Any]] = Field(default_factory=list)
    previous_agi_articles: list[dict[str, Any]] = Field(default_factory=list)
    house_view: dict[str, Any] | None = None
    confidence: float | None = None
    latest_updates: list[dict[str, Any]] = Field(default_factory=list)
    supporting_evidence: list[dict[str, Any]] = Field(default_factory=list)
    # AGI Product V1 — living research
    whats_changed_since_publication: list[str] = Field(default_factory=list)
    thesis_still_holds: bool | None = None
    thesis_status: dict[str, Any] = Field(default_factory=dict)
    prediction_status: list[dict[str, Any]] = Field(default_factory=list)
    latest_news: list[dict[str, Any]] = Field(default_factory=list)
    discovery: dict[str, Any] = Field(default_factory=dict)
    follow_up_questions: list[str] = Field(default_factory=list)


class AutocompleteView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    meta: UiMeta
    query: str
    companies: list[dict[str, Any]] = Field(default_factory=list)
    themes: list[dict[str, Any]] = Field(default_factory=list)
    sectors: list[dict[str, Any]] = Field(default_factory=list)
    articles: list[dict[str, Any]] = Field(default_factory=list)
    questions: list[dict[str, Any]] = Field(default_factory=list)
    popular_searches: list[dict[str, Any]] = Field(default_factory=list)


class ResearchView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    meta: UiMeta
    research_id: str | None = None
    article: dict[str, Any] = Field(default_factory=dict)
    related_research: list[dict[str, Any]] = Field(default_factory=list)
    related_companies: list[str] = Field(default_factory=list)
    related_themes: list[str] = Field(default_factory=list)
    related_sectors: list[str] = Field(default_factory=list)
    latest_news: list[dict[str, Any]] = Field(default_factory=list)
    knowledge_timeline: list[dict[str, Any]] = Field(default_factory=list)
    research_timeline: list[dict[str, Any]] = Field(default_factory=list)
    supporting_evidence: list[dict[str, Any]] = Field(default_factory=list)
    prediction_tracker: list[dict[str, Any]] = Field(default_factory=list)
    workflow: dict[str, Any] = Field(default_factory=dict)


class ThemeView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    meta: UiMeta
    theme_id: str
    current_thesis: str | None = None
    related_companies: list[str] = Field(default_factory=list)
    related_research: list[dict[str, Any]] = Field(default_factory=list)
    current_risks: list[str] = Field(default_factory=list)
    current_catalysts: list[str] = Field(default_factory=list)
    house_view: dict[str, Any] | None = None
    timeline: list[dict[str, Any]] = Field(default_factory=list)
    # AGI Product V1
    confidence: float | None = None
    stance: str | None = None
    related_macro: list[str] = Field(default_factory=list)
    knowledge_graph: dict[str, Any] = Field(default_factory=dict)
    research_timeline: list[dict[str, Any]] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)
    discovery: dict[str, Any] = Field(default_factory=dict)
    product_meta: dict[str, Any] = Field(default_factory=dict)


class SectorView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    meta: UiMeta
    sector_id: str
    sector_health: str | None = None
    leaders: list[str] = Field(default_factory=list)
    laggards: list[str] = Field(default_factory=list)
    current_theme: str | None = None
    current_risks: list[str] = Field(default_factory=list)
    current_research: list[dict[str, Any]] = Field(default_factory=list)
    valuation_snapshot: dict[str, Any] = Field(default_factory=dict)
    # AGI Product V1
    current_outlook: str | None = None
    current_opportunities: list[str] = Field(default_factory=list)
    macro_drivers: list[str] = Field(default_factory=list)
    sector_timeline: list[dict[str, Any]] = Field(default_factory=list)
    valuation_summary: dict[str, Any] = Field(default_factory=dict)
    follow_up_questions: list[str] = Field(default_factory=list)
    discovery: dict[str, Any] = Field(default_factory=dict)
    product_meta: dict[str, Any] = Field(default_factory=dict)


class DashboardView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    meta: UiMeta
    market_brief: dict[str, Any] = Field(default_factory=dict)
    market_regime: dict[str, Any] = Field(default_factory=dict)
    market_risk: dict[str, Any] = Field(default_factory=dict)
    todays_events: list[dict[str, Any]] = Field(default_factory=list)
    research_queue: list[dict[str, Any]] = Field(default_factory=list)
    latest_reports: list[dict[str, Any]] = Field(default_factory=list)
    system_health: dict[str, Any] = Field(default_factory=dict)
    sentiment: dict[str, Any] = Field(default_factory=dict)


class MacroView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    meta: UiMeta
    current_regime: dict[str, Any] = Field(default_factory=dict)
    macro_dashboard: dict[str, Any] = Field(default_factory=dict)
    regime_history: list[dict[str, Any]] = Field(default_factory=list)
    macro_timeline: list[dict[str, Any]] = Field(default_factory=list)
    macro_research: list[dict[str, Any]] = Field(default_factory=list)
    central_bank_events: list[dict[str, Any]] = Field(default_factory=list)
    market_risk: dict[str, Any] = Field(default_factory=dict)
    # AGI Product V1 — investment intelligence layer
    intelligence: dict[str, Any] = Field(default_factory=dict)
    follow_up_questions: list[str] = Field(default_factory=list)
    discovery: dict[str, Any] = Field(default_factory=dict)


class PredictionCentreView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    meta: UiMeta
    predictions: list[dict[str, Any]] = Field(default_factory=list)
    accuracy: dict[str, Any] = Field(default_factory=dict)
    prediction_timeline: list[dict[str, Any]] = Field(default_factory=list)
    discovery: dict[str, Any] = Field(default_factory=dict)
    follow_up_questions: list[str] = Field(default_factory=list)


class PortfolioView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    meta: UiMeta
    current_portfolio: dict[str, Any] | None = None
    historical_portfolio: list[dict[str, Any]] = Field(default_factory=list)
    sector_allocation: dict[str, Any] = Field(default_factory=dict)
    risk: dict[str, Any] | None = None
    performance: dict[str, Any] | None = None
    attribution: dict[str, Any] | None = None
    confidence: float | None = None
    composite_book: dict[str, Any] = Field(default_factory=dict)


class CopilotView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    meta: UiMeta
    page: str
    question: str
    context: dict[str, Any] = Field(default_factory=dict)
    answer_policy: str = "context_aware_never_empty"


class WorkflowView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    meta: UiMeta
    stages: list[dict[str, Any]] = Field(default_factory=list)
    pipeline: list[dict[str, Any]] = Field(default_factory=list)
    draft_queue: list[Any] = Field(default_factory=list)
    review_queue: list[Any] = Field(default_factory=list)
    published: list[dict[str, Any]] = Field(default_factory=list)
