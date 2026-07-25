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


class CompanyView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    meta: UiMeta
    ticker: str
    overview: dict[str, Any] = Field(default_factory=dict)
    market_intelligence: dict[str, Any] = Field(default_factory=dict)
    research: dict[str, Any] = Field(default_factory=dict)
    evidence: dict[str, Any] = Field(default_factory=dict)
    portfolio: dict[str, Any] = Field(default_factory=dict)


class SearchView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    meta: UiMeta
    question: str
    intent: str | None = None
    answer: dict[str, Any] = Field(default_factory=dict)
    house_view: dict[str, Any] | None = None
    confidence: float | None = None
    supporting_research: list[dict[str, Any]] = Field(default_factory=list)
    latest_articles: list[dict[str, Any]] = Field(default_factory=list)
    latest_news: list[dict[str, Any]] = Field(default_factory=list)
    conflicting_opinions: list[dict[str, Any]] = Field(default_factory=list)
    evidence_used: list[dict[str, Any]] = Field(default_factory=list)
    related_companies: list[str] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)
    hits: list[dict[str, Any]] = Field(default_factory=list)
    answer_policy: str = "institutional_evidence_pack"


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
