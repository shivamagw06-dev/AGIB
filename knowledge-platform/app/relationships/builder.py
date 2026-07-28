"""Relationship Builder — Company → Sector → Industry → Index → Peers."""

from __future__ import annotations

from app.contracts.models import EntityRefs, KnowledgeObject, KnowledgeObjectType
from app.storage.db import KaipStore


class RelationshipBuilder:
    def __init__(self, store: KaipStore) -> None:
        self.store = store

    def apply(self, ko: KnowledgeObject) -> EntityRefs:
        """Update entity relationships from a knowledge object and return fresh refs."""
        payload = ko.payload
        sector = payload.get("sector")
        industry = payload.get("industry")
        indexes = payload.get("indexes")
        peers = payload.get("peers")

        if ko.object_type == KnowledgeObjectType.COMPANY_PROFILE:
            updated = self.store.update_entity_relationships(
                ko.company_symbol,
                sector=sector,
                industry=industry,
                indexes=indexes if isinstance(indexes, list) else None,
                peers=peers if isinstance(peers, list) else None,
            )
            if updated:
                # Keep KO entity_refs aligned with registry
                ko.entity_refs = updated
                return updated

        # Non-profile objects still refresh peer/index graph from registry
        current = self.store.get_entity(ko.company_symbol)
        if current:
            ko.entity_refs = current
            return current
        return ko.entity_refs
