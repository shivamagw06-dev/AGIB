"""KIP domain models — documents, chunks, graph, search, RAG evidence."""

from __future__ import annotations

import datetime as _dt
from enum import Enum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


def _utcnow() -> _dt.datetime:
    return _dt.datetime.now(_dt.timezone.utc)


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


class DocumentType(str, Enum):
    AGI_RESEARCH = "agi_research"
    AGI_NOTE = "agi_note"
    AGI_CIO_REPORT = "agi_cio_report"
    AGI_DAILY_BRIEF = "agi_daily_brief"
    BROKER_RESEARCH = "broker_research"
    BROKER_EMAIL = "broker_email"
    NEWSLETTER = "newsletter"
    SEC_FILING = "sec_filing"
    NSE_BSE_FILING = "nse_bse_filing"
    EARNINGS_TRANSCRIPT = "earnings_transcript"
    INVESTOR_PRESENTATION = "investor_presentation"
    ANNUAL_REPORT = "annual_report"
    QUARTERLY_REPORT = "quarterly_report"
    GOVERNMENT_REPORT = "government_report"
    CENTRAL_BANK_REPORT = "central_bank_report"
    INDUSTRY_REPORT = "industry_report"
    COMMODITY_REPORT = "commodity_report"
    MACRO_REPORT = "macro_report"
    OTHER = "other"


class DocumentMetadata(BaseModel):
    title: str = ""
    author: str = ""
    source: str = ""
    date: _dt.date | None = None
    document_type: DocumentType = DocumentType.OTHER
    broker: str = ""
    language: str = "en"
    version: int = 1


class InvestmentMetadata(BaseModel):
    companies: list[str] = Field(default_factory=list)
    tickers: list[str] = Field(default_factory=list)
    industries: list[str] = Field(default_factory=list)
    sectors: list[str] = Field(default_factory=list)
    countries: list[str] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    macro_topics: list[str] = Field(default_factory=list)


class ResearchMetadata(BaseModel):
    investment_thesis: str = ""
    bull_case: list[str] = Field(default_factory=list)
    bear_case: list[str] = Field(default_factory=list)
    counter_arguments: list[str] = Field(default_factory=list)
    catalysts: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    valuation: str = ""
    forecasts: list[str] = Field(default_factory=list)
    target_prices: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    key_metrics: dict[str, str] = Field(default_factory=dict)
    tables: list[dict[str, Any]] = Field(default_factory=list)
    timeline_events: list[dict[str, Any]] = Field(default_factory=list)


class KnowledgeMetadata(BaseModel):
    freshness: float = 1.0
    confidence: float = 0.5
    source_reliability: float = 0.7
    related_documents: list[str] = Field(default_factory=list)
    related_companies: list[str] = Field(default_factory=list)
    related_themes: list[str] = Field(default_factory=list)
    related_research: list[str] = Field(default_factory=list)
    summary: str = ""


class KipChunk(BaseModel):
    chunk_id: str = Field(default_factory=lambda: _new_id("chk"))
    document_id: str
    lineage_id: str
    version: int = 1
    ordinal: int = 0
    text: str
    tokens: list[str] = Field(default_factory=list)
    embedding: list[float] = Field(default_factory=list)
    tickers: list[str] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    sectors: list[str] = Field(default_factory=list)


class KipDocument(BaseModel):
    document_id: str = Field(default_factory=lambda: _new_id("doc"))
    lineage_id: str = Field(default_factory=lambda: _new_id("lin"))
    content: str = ""
    cleaned_content: str = ""
    ocr_applied: bool = False
    document: DocumentMetadata = Field(default_factory=DocumentMetadata)
    investment: InvestmentMetadata = Field(default_factory=InvestmentMetadata)
    research: ResearchMetadata = Field(default_factory=ResearchMetadata)
    knowledge: KnowledgeMetadata = Field(default_factory=KnowledgeMetadata)
    supersedes: str | None = None
    superseded_by: str | None = None
    knowledge_version: str = "kip-v1.0.1"
    pipeline_stages: list[str] = Field(default_factory=list)
    created_at: _dt.datetime = Field(default_factory=_utcnow)
    immutable: Literal[True] = True


class GraphNode(BaseModel):
    node_id: str
    kind: str
    label: str
    attributes: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    edge_id: str = Field(default_factory=lambda: _new_id("edge"))
    source: str
    target: str
    relation: str
    document_id: str | None = None
    weight: float = 1.0


class KnowledgeGraphView(BaseModel):
    entity: str
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)


class TimelineEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: _new_id("evt"))
    ticker: str
    event_date: _dt.date
    event_type: str
    title: str
    document_id: str | None = None
    source: str = ""
    summary: str = ""


class ResearchTimeline(BaseModel):
    ticker: str
    events: list[TimelineEvent] = Field(default_factory=list)


class SearchHit(BaseModel):
    document_id: str
    lineage_id: str
    version: int
    title: str
    document_type: str
    score: float
    keyword_score: float = 0.0
    semantic_score: float = 0.0
    snippet: str = ""
    tickers: list[str] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    freshness: float = 1.0
    confidence: float = 0.5


class SearchResponse(BaseModel):
    query: str
    mode: str
    hits: list[SearchHit] = Field(default_factory=list)
    knowledge_version: str = "kip-v1.0.1"


class RagEvidenceItem(BaseModel):
    document_id: str
    title: str
    snippet: str
    tickers: list[str] = Field(default_factory=list)
    stance: str = "neutral"  # bull / bear / neutral
    freshness: float = 1.0
    confidence: float = 0.5
    date: _dt.date | None = None


class RagEvidencePack(BaseModel):
    query: str
    documents_retrieved: list[str] = Field(default_factory=list)
    supporting_evidence: list[RagEvidenceItem] = Field(default_factory=list)
    conflicting_opinions: list[RagEvidenceItem] = Field(default_factory=list)
    source_list: list[str] = Field(default_factory=list)
    freshness_score: float = 0.0
    confidence_score: float = 0.0
    knowledge_version: str = "kip-v1.0.1"
    answer_policy: str = "retrieval_augmented_only"


class IngestRequest(BaseModel):
    title: str = ""
    content: str = ""
    author: str = ""
    source: str = "agi"
    document_type: DocumentType = DocumentType.OTHER
    broker: str = ""
    language: str = "en"
    date: _dt.date | None = None
    tickers: list[str] = Field(default_factory=list)
    companies: list[str] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    sectors: list[str] = Field(default_factory=list)
    needs_ocr: bool = False
    ocr_text: str = ""
    lineage_id: str | None = None
    supersedes: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CompanyKnowledge(BaseModel):
    ticker: str
    documents: list[str] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    sectors: list[str] = Field(default_factory=list)
    related_companies: list[str] = Field(default_factory=list)
    latest_thesis: str = ""
    bull_case: list[str] = Field(default_factory=list)
    bear_case: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    catalysts: list[str] = Field(default_factory=list)
    timeline: ResearchTimeline | None = None
    graph: KnowledgeGraphView | None = None


class ThemeKnowledge(BaseModel):
    theme_id: str
    theme: str
    documents: list[str] = Field(default_factory=list)
    tickers: list[str] = Field(default_factory=list)
    related_themes: list[str] = Field(default_factory=list)
