"""Shared Evidence / Processing Event Bus catalogue (FSE-02 + FSE-04 + FSE-04.1)."""

from __future__ import annotations

# Collection (FSE-02)
COLLECTION_EVENTS = (
    "discovery.filing_found",
    "discovery.filing_updated",
    "evidence.stored",
    "evidence.duplicate_skipped",
    "evidence.restatement_candidate",
    "collection.job_failed",
    "collection.job_completed",
)

# Parsing (FSE-04) — legacy aliases retained during migration
PARSE_EVENTS_LEGACY = (
    "parse.started",
    "parse.completed",
    "parse.failed",
    "parse.quarantined",
)

# Parsing quality (FSE-04.1) — versioned (consumers must use these)
PARSE_EVENTS_V1 = (
    "parse.started.v1",
    "parse.completed.v1",
    "parse.failed.v1",
    "parse.quarantined.v1",
    "draft.created.v1",
    "draft.updated.v1",
    "schema.updated.v1",
    "unknown_metric.queued.v1",
    "parser.certified.v1",
    "parser.certification_failed.v1",
)

PARSE_EVENTS = PARSE_EVENTS_LEGACY + PARSE_EVENTS_V1

EVENT_TYPES = COLLECTION_EVENTS + PARSE_EVENTS
