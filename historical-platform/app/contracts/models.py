"""Historical Acquisition Platform contracts — raw archive + historical knowledge objects."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return str(uuid4())


class Source(str, Enum):
    YAHOO = "yahoo"
    NSE = "nse"
    BSE = "bse"
    COMPANY_IR = "company_ir"
    DERIVED = "derived"


class HistoricalObjectType(str, Enum):
    PRICE_HISTORY = "HistoricalPriceHistory"
    FINANCIAL_STATEMENT = "HistoricalFinancialStatement"
    BALANCE_SHEET = "HistoricalBalanceSheet"
    CASH_FLOW = "HistoricalCashFlow"
    CORPORATE_EVENT = "HistoricalCorporateEvent"
    CORPORATE_ACTION = "HistoricalCorporateAction"
    DIVIDEND_HISTORY = "HistoricalDividendHistory"
    OWNERSHIP_HISTORY = "HistoricalOwnershipHistory"
    MARKET_SNAPSHOT = "HistoricalMarketSnapshot"
    COMPANY_PROFILE = "HistoricalCompanyProfile"
    NEWS_EVENT = "HistoricalNewsEvent"


class ValidationStatus(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"


class PeriodKind(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    EVENT = "event"
    POINT_IN_TIME = "point_in_time"


class RawHistoricalEvent(BaseModel):
    """Append-only raw archive unit — never mutated after insert."""

    event_id: str = Field(default_factory=new_id)
    source: Source
    collector_id: str
    endpoint: str
    company_symbol: str | None = None
    category: str
    payload: dict[str, Any] = Field(default_factory=dict)
    retrieved_at: datetime = Field(default_factory=utc_now)
    effective_start: str | None = None  # ISO date or period label
    effective_end: str | None = None
    checksum: str
    validation_status: ValidationStatus | None = None
    validation_errors: list[str] = Field(default_factory=list)
    ingestion_run_id: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class EntityRefs(BaseModel):
    company_symbol: str | None = None
    company_name: str | None = None
    sector: str | None = None
    sector_key: str | None = None
    industry: str | None = None
    index_membership: list[str] = Field(default_factory=list)
    time_period: str | None = None  # e.g. FY2019 Q3
    period_kind: PeriodKind | None = None


class HistoricalProvenance(BaseModel):
    source: Source
    collector_id: str | None = None
    retrieved_at: datetime = Field(default_factory=utc_now)
    effective_date: str | None = None
    version: int = 1
    checksum: str | None = None
    source_event_ids: list[str] = Field(default_factory=list)
    ingestion_run_id: str | None = None


class HistoricalKnowledgeObject(BaseModel):
    """Canonical historical object — append-only versions."""

    object_type: HistoricalObjectType
    object_id: str = Field(default_factory=new_id)
    company_symbol: str | None = None
    subject_key: str
    effective_date: str  # ISO date or fiscal period key
    period_kind: PeriodKind = PeriodKind.POINT_IN_TIME
    version: int = 1
    previous_object_id: str | None = None
    knowledge: dict[str, Any] = Field(default_factory=dict)
    entity_refs: EntityRefs
    provenance: HistoricalProvenance
    created_at: datetime = Field(default_factory=utc_now)


class IngestionRun(BaseModel):
    run_id: str = Field(default_factory=new_id)
    mode: str = "bootstrap"  # bootstrap | incremental | correction
    collector_id: str
    symbols: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=utc_now)
    ended_at: datetime | None = None
    status: str = "running"
    raw_accepted: int = 0
    raw_rejected: int = 0
    objects_written: int = 0
    detail: dict[str, Any] = Field(default_factory=dict)


class CoverageStatus(str, Enum):
    COMPLETE = "Complete"
    PARTIAL = "Partial"
    SPARSE = "Sparse"
    MISSING = "Missing"
