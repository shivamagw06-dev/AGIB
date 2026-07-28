"""Stable KAIP contracts — Raw Events, Knowledge Objects, Learning Events."""

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


class KnowledgeObjectType(str, Enum):
    COMPANY_PROFILE = "CompanyProfile"
    MARKET_SNAPSHOT = "MarketSnapshot"
    CORPORATE_EVENT = "CorporateEvent"
    CORPORATE_ACTION = "CorporateAction"
    FINANCIAL_STATEMENT = "FinancialStatement"


class ValidationStatus(str, Enum):
    ACCEPTED = "accepted"
    DUPLICATE = "duplicate"
    REJECTED = "rejected"


class RawEvent(BaseModel):
    event_id: str = Field(default_factory=new_id)
    source: Source
    collector_id: str
    endpoint: str
    company_symbol: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=utc_now)
    checksum: str
    validation_status: ValidationStatus | None = None
    validation_errors: list[str] = Field(default_factory=list)


class EntityRefs(BaseModel):
    company_id: str
    company_name: str
    company_symbol: str
    sector: str | None = None
    industry: str | None = None
    indexes: list[str] = Field(default_factory=list)
    peers: list[str] = Field(default_factory=list)


class KnowledgeObject(BaseModel):
    object_type: KnowledgeObjectType
    object_id: str = Field(default_factory=new_id)
    company_symbol: str
    version: int = 1
    payload: dict[str, Any] = Field(default_factory=dict)
    entity_refs: EntityRefs
    published_at: datetime | None = None
    source_event_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class LearningEvent(BaseModel):
    learning_id: str = Field(default_factory=new_id)
    company_symbol: str
    field_name: str
    previous_value: Any = None
    new_value: Any = None
    delta: Any = None
    materiality: str = "material"
    reason: str
    object_type: KnowledgeObjectType | None = None
    object_id: str | None = None
    source_event_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    published_at: datetime | None = None


class PublishedBundle(BaseModel):
    knowledge_objects: list[KnowledgeObject] = Field(default_factory=list)
    learning_events: list[LearningEvent] = Field(default_factory=list)
