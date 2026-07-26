"""FAA domain models — discovery tasks, fetch results, acquisition jobs."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data or b"").hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes((text or "").encode("utf-8"))


ConnectorId = Literal[
    "company_ir",
    "nse",
    "bse",
    "sebi",
    "rbi",
    "government",
    "news",
    "rss",
    "search_api",
    "pdf_url",
    "html_page",
]


class DiscoveryTask(BaseModel):
    task_id: str = Field(default_factory=lambda: new_id("disc"))
    description: str
    connector_id: str
    query: str = ""
    company: str | None = None
    symbol: str | None = None
    document_type: str = "unknown"
    preferred_url: str | None = None
    priority: int = 5

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()


class CandidateDocument(BaseModel):
    candidate_id: str = Field(default_factory=lambda: new_id("cand"))
    title: str
    url: str
    connector_id: str
    document_type: str = "unknown"
    company: str | None = None
    symbol: str | None = None
    organisation: str = ""
    published_at: str | None = None
    discovery_task_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()


class FetchedDocument(BaseModel):
    fetch_id: str = Field(default_factory=lambda: new_id("fetch"))
    candidate_id: str
    title: str
    url: str
    connector_id: str
    document_type: str = "unknown"
    company: str | None = None
    symbol: str | None = None
    organisation: str = ""
    published_at: str | None = None
    content_type: str = "text/plain"
    content_text: str = ""
    content_bytes_len: int = 0
    checksum: str = ""
    live_fetch: bool = False
    skipped: bool = False
    skip_reason: str | None = None
    error: str | None = None
    fetched_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = self.model_dump()
        d["fetched_at"] = self.fetched_at.isoformat()
        # never dump raw bytes
        return d


class AcquisitionResult(BaseModel):
    job_id: str = Field(default_factory=lambda: new_id("faa"))
    query: str
    discovered: int = 0
    fetched: int = 0
    skipped_cached: int = 0
    failed: int = 0
    processed: int = 0
    indexed_to_fre: int = 0
    live_fetch: bool = False
    candidates: list[dict[str, Any]] = Field(default_factory=list)
    documents: list[dict[str, Any]] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=utc_now)
    finished_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        d = self.model_dump()
        d["started_at"] = self.started_at.isoformat()
        d["finished_at"] = self.finished_at.isoformat() if self.finished_at else None
        return d


class FaaMetrics(BaseModel):
    discovery_runs: int = 0
    candidates_found: int = 0
    downloads_attempted: int = 0
    downloads_succeeded: int = 0
    downloads_failed: int = 0
    cache_hits: int = 0
    processed: int = 0
    indexed_to_fre: int = 0
    last_run_at: str | None = None

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:  # type: ignore[override]
        return super().model_dump(**kwargs)
