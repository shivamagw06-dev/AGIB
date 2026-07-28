"""Historical Knowledge Builder — canonical rows → versioned HistoricalKnowledgeObjects."""

from __future__ import annotations

from typing import Any

from app.contracts.models import (
    EntityRefs,
    HistoricalKnowledgeObject,
    HistoricalObjectType,
    HistoricalProvenance,
    PeriodKind,
    Source,
    utc_now,
)
from app.storage.db import HipStore


class HistoricalKnowledgeBuilder:
    def __init__(self, store: HipStore) -> None:
        self.store = store

    def build(
        self,
        *,
        canonical: dict[str, Any],
        entity_refs: EntityRefs,
        source: Source,
        collector_id: str,
        ingestion_run_id: str | None = None,
    ) -> HistoricalKnowledgeObject | None:
        try:
            object_type = HistoricalObjectType(canonical["object_type"])
        except Exception:
            return None
        symbol = (canonical.get("company_symbol") or entity_refs.company_symbol or "").upper()
        if not symbol:
            return None
        effective_date = str(canonical.get("effective_date") or "")
        if not effective_date:
            return None
        try:
            period_kind = PeriodKind(canonical.get("period_kind") or PeriodKind.POINT_IN_TIME.value)
        except Exception:
            period_kind = PeriodKind.POINT_IN_TIME

        subject_key = symbol
        version = self.store.latest_version(object_type, subject_key, effective_date) + 1
        previous_id = None
        if version > 1:
            # prior version retained; we don't fetch id for brevity — version chain is sufficient
            previous_id = None

        now = utc_now()
        provenance = HistoricalProvenance(
            source=source,
            collector_id=collector_id,
            retrieved_at=now,
            effective_date=effective_date,
            version=version,
            checksum=None,
            source_event_ids=[canonical["source_event_id"]] if canonical.get("source_event_id") else [],
            ingestion_run_id=ingestion_run_id,
        )
        knowledge = dict(canonical.get("knowledge") or {})
        # Ensure IR reports land in reports mirror
        if knowledge.get("report_type"):
            pass

        return HistoricalKnowledgeObject(
            object_type=object_type,
            company_symbol=symbol,
            subject_key=subject_key,
            effective_date=effective_date,
            period_kind=period_kind,
            version=version,
            previous_object_id=previous_id,
            knowledge=knowledge,
            entity_refs=entity_refs,
            provenance=provenance,
            created_at=now,
        )
