"""Shared Evidence / Processing Event Bus catalogue (FSE-02 + FSE-04+)."""

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

# Parsing (FSE-04)
PARSE_EVENTS = (
    "parse.started",
    "parse.completed",
    "parse.failed",
    "parse.quarantined",
)

EVENT_TYPES = COLLECTION_EVENTS + PARSE_EVENTS
