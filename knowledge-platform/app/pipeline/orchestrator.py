"""End-to-end KAIP acquisition pipeline (no reasoning)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from app.collectors.base import BaseCollector
from app.config.settings import Settings
from app.contracts.models import (
    KnowledgeObject,
    KnowledgeObjectType,
    LearningEvent,
    PublishedBundle,
    RawEvent,
    ValidationStatus,
)
from app.entity_resolution.resolver import EntityResolver
from app.knowledge_builder.builder import KnowledgeObjectBuilder
from app.normalizers.canonical import CanonicalNormalizer
from app.pipeline.change_detection import ChangeDetector
from app.publisher.publisher import KnowledgePublisher
from app.relationships.builder import RelationshipBuilder
from app.storage.db import KaipStore
from app.validators.gates import ValidationGate

logger = logging.getLogger("kaip.pipeline")


@dataclass
class PipelineResult:
    raw_events: list[RawEvent] = field(default_factory=list)
    accepted: list[RawEvent] = field(default_factory=list)
    rejected: list[RawEvent] = field(default_factory=list)
    duplicates: list[RawEvent] = field(default_factory=list)
    knowledge_objects: list[KnowledgeObject] = field(default_factory=list)
    learning_events: list[LearningEvent] = field(default_factory=list)
    published: PublishedBundle | None = None


class AcquisitionPipeline:
    def __init__(self, store: KaipStore, settings: Settings) -> None:
        self.store = store
        self.settings = settings
        self.validator = ValidationGate(store, duplicate_window_seconds=settings.duplicate_window_seconds)
        self.normalizer = CanonicalNormalizer()
        self.resolver = EntityResolver(store)
        self.builder = KnowledgeObjectBuilder(store)
        self.relationships = RelationshipBuilder(store)
        self.change_detector = ChangeDetector(store, settings)
        self.publisher = KnowledgePublisher(store)

    def ingest_events(self, events: list[RawEvent]) -> PipelineResult:
        result = PipelineResult(raw_events=list(events))
        built: list[KnowledgeObject] = []
        learning: list[LearningEvent] = []

        for event in events:
            # Always persist raw first (append-only), then validate
            self.store.insert_raw_event(event)
            validated = self.validator.validate(event)
            self.store.update_raw_validation(validated)

            if validated.validation_status == ValidationStatus.REJECTED:
                result.rejected.append(validated)
                continue
            if validated.validation_status == ValidationStatus.DUPLICATE:
                result.duplicates.append(validated)
                continue

            result.accepted.append(validated)
            canonical_items = self.normalizer.normalize(validated)
            for canonical in canonical_items:
                entity = self.resolver.resolve(
                    canonical.get("company_symbol") or validated.company_symbol or "",
                    hints={
                        "company_name": canonical.get("company_name"),
                        "sector": canonical.get("sector"),
                        "industry": canonical.get("industry"),
                    },
                )
                previous = None
                try:
                    ot = KnowledgeObjectType(canonical.get("object_type"))
                    previous = self.store.latest_ko(ot, entity.company_symbol)
                except Exception:
                    previous = None

                ko = self.builder.build(
                    canonical=canonical,
                    entity_refs=entity,
                    source_event_ids=[validated.event_id],
                )
                if ko is None:
                    continue
                self.relationships.apply(ko)
                learning.extend(self.change_detector.detect(ko, previous))
                built.append(ko)

        if built or learning:
            result.published = self.publisher.publish(built, learning)
            result.knowledge_objects = list(result.published.knowledge_objects)
            result.learning_events = list(result.published.learning_events)
        else:
            result.knowledge_objects = built
            result.learning_events = learning
        return result

    def run_collector(self, collector: BaseCollector) -> PipelineResult:
        logger.info("collecting collector_id=%s", collector.collector_id)
        events = collector.collect()
        return self.ingest_events(events)

    def status(self) -> dict[str, Any]:
        return {
            "raw_events": self.store.count_raw_events(),
            "published_knowledge_objects": self.store.count_published_kos(),
        }
