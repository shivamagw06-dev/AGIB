from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id(prefix: str = "") -> str:
    value = uuid4().hex
    return f"{prefix}{value}" if prefix else value


class DeskType(str, Enum):
    SMOKE = "smoke"
    CIO_MORNING = "cio_morning"
    EQUITY = "equity"
    CUSTOM = "custom"


class RunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class SourceType(str, Enum):
    AGIB_CACHE = "agib_cache"
    MACRO = "macro"
    MARKET = "market"
    NEWS = "news"
    PRE_MARKET = "pre_market"
    FUNDAMENTAL = "fundamental"
    INTERNAL = "internal"
    MEMORY = "memory"


class EvidenceItem(BaseModel):
    evidence_id: str = Field(default_factory=lambda: new_id("ev_"))
    claim: str
    source_id: str
    source_type: SourceType
    fetched_at: datetime = Field(default_factory=utcnow)
    snippet: str | None = None
    url: str | None = None
    reliability: float = Field(default=0.7, ge=0.0, le=1.0)

    @field_validator("claim")
    @classmethod
    def claim_not_empty(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("Evidence claim cannot be empty")
        return text


class ConfidenceBreakdown(BaseModel):
    score: int = Field(ge=0, le=100)
    supports: list[str] = Field(default_factory=list)
    challenges: list[str] = Field(default_factory=list)
    rationale: str

    @field_validator("rationale")
    @classmethod
    def rationale_required(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("Confidence rationale is required")
        return text


class Finding(BaseModel):
    statement: str
    evidence_ids: list[str] = Field(min_length=1)
    is_scenario: bool = False
    confidence: int | None = Field(default=None, ge=0, le=100)


class AgentOutput(BaseModel):
    agent_id: str
    mission: str
    findings: list[Finding] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    confidence: ConfidenceBreakdown
    assumptions: list[str] = Field(default_factory=list)
    invalidators: list[str] = Field(default_factory=list)
    raw_trace_ref: str | None = None
    completed_at: datetime = Field(default_factory=utcnow)

    @model_validator(mode="after")
    def evidence_must_back_findings(self) -> "AgentOutput":
        if not self.evidence:
            raise ValueError("AgentOutput requires at least one evidence item")
        known = {item.evidence_id for item in self.evidence}
        for finding in self.findings:
            missing = [eid for eid in finding.evidence_ids if eid not in known]
            if missing:
                raise ValueError(f"Finding cites unknown evidence ids: {missing}")
        return self


class DebatePosition(BaseModel):
    side: Literal["bull", "base", "bear"]
    points: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)


class DebatePackage(BaseModel):
    summary: str
    positions: list[DebatePosition] = Field(default_factory=list)
    unresolved_conflicts: list[str] = Field(default_factory=list)


class ScenarioCase(BaseModel):
    label: str
    probability: int = Field(ge=0, le=100)
    detail: str
    is_prediction: bool = True


class InstitutionalReport(BaseModel):
    report_id: str = Field(default_factory=lambda: new_id("rpt_"))
    desk: DeskType
    title: str
    executive_summary: str
    key_findings: list[str] = Field(default_factory=list)
    macro_view: str | None = None
    market_view: str | None = None
    sector_view: str | None = None
    company_view: str | None = None
    technical_view: str | None = None
    valuation_view: str | None = None
    catalysts: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    bull_case: ScenarioCase | None = None
    base_case: ScenarioCase | None = None
    bear_case: ScenarioCase | None = None
    confidence: ConfidenceBreakdown
    supporting_evidence: list[EvidenceItem] = Field(default_factory=list)
    action_items: list[str] = Field(default_factory=list)
    citations: dict[str, list[str]] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=utcnow)


class DirectorPlan(BaseModel):
    desk: DeskType
    agent_ids: list[str]
    rationale: str
    require_all: bool = False


class ResearchRunCreate(BaseModel):
    desk: DeskType = DeskType.SMOKE
    query: str | None = None
    symbols: list[str] = Field(default_factory=list)
    force: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResearchRun(BaseModel):
    run_id: str = Field(default_factory=lambda: new_id("run_"))
    desk: DeskType
    status: RunStatus = RunStatus.QUEUED
    query: str | None = None
    symbols: list[str] = Field(default_factory=list)
    director_plan: DirectorPlan | None = None
    agent_outputs: list[AgentOutput] = Field(default_factory=list)
    debate: DebatePackage | None = None
    cio_thesis: str | None = None
    report: InstitutionalReport | None = None
    errors: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    completed_at: datetime | None = None


class PredictionRecord(BaseModel):
    prediction_id: str = Field(default_factory=lambda: new_id("pred_"))
    run_id: str
    statement: str
    horizon: str
    created_at: datetime = Field(default_factory=utcnow)
    actual_outcome: str | None = None
    accuracy: float | None = Field(default=None, ge=0.0, le=1.0)
    success_reason: str | None = None
    failure_reason: str | None = None
