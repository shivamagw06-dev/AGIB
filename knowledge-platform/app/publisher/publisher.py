"""Knowledge Publisher — publishes Knowledge Objects only. Never raw JSON."""

from __future__ import annotations

from app.contracts.models import KnowledgeObject, LearningEvent, PublishedBundle, utc_now
from app.storage.db import KaipStore


class KnowledgePublisher:
    """In-process publisher for Sprint 6.1.

    Intelligence Engine retrieves via KAIP internal APIs — it never sees Yahoo/NSE/BSE.
    """

    def __init__(self, store: KaipStore) -> None:
        self.store = store
        self._last_bundle: PublishedBundle | None = None

    def publish(
        self,
        knowledge_objects: list[KnowledgeObject],
        learning_events: list[LearningEvent],
    ) -> PublishedBundle:
        now = utc_now()
        published_kos: list[KnowledgeObject] = []
        published_learning: list[LearningEvent] = []

        for ko in knowledge_objects:
            # Strip any accidental provider leakage keys
            ko.payload = {
                k: v
                for k, v in ko.payload.items()
                if k
                not in {
                    "chart",
                    "quote_summary",
                    "yahoo_symbol",
                    "raw",
                    "provider",
                    "marketCap",
                    "trailingPE",
                    "longName",
                }
            }
            ko.published_at = now
            ko.updated_at = now
            self.store.insert_knowledge_object(ko)
            self.store.mark_published(ko.object_id, now)
            published_kos.append(ko)

        for le in learning_events:
            le.published_at = now
            self.store.insert_learning_event(le)
            self.store.mark_learning_published(le.learning_id, now)
            published_learning.append(le)

        bundle = PublishedBundle(
            knowledge_objects=published_kos,
            learning_events=published_learning,
        )
        self._last_bundle = bundle
        return bundle

    @property
    def last_bundle(self) -> PublishedBundle | None:
        return self._last_bundle
