"""Knowledge Object Builder — Sprint 6.1 supports exactly five types."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.contracts.models import (
    EntityRefs,
    KnowledgeObject,
    KnowledgeObjectType,
    utc_now,
)
from app.storage.db import KaipStore

ALLOWED_TYPES = {
    KnowledgeObjectType.COMPANY_PROFILE,
    KnowledgeObjectType.MARKET_SNAPSHOT,
    KnowledgeObjectType.CORPORATE_EVENT,
    KnowledgeObjectType.CORPORATE_ACTION,
    KnowledgeObjectType.FINANCIAL_STATEMENT,
}


class KnowledgeObjectBuilder:
    def __init__(self, store: KaipStore) -> None:
        self.store = store

    def build(
        self,
        *,
        canonical: dict[str, Any],
        entity_refs: EntityRefs,
        source_event_ids: list[str],
    ) -> KnowledgeObject | None:
        type_name = canonical.get("object_type")
        try:
            object_type = KnowledgeObjectType(type_name)
        except Exception:
            return None
        if object_type not in ALLOWED_TYPES:
            return None

        symbol = (canonical.get("company_symbol") or entity_refs.company_symbol or "").upper()
        if not symbol:
            return None

        payload = {k: v for k, v in canonical.items() if k not in {"object_type"}}
        payload["company_symbol"] = symbol

        previous = self.store.latest_ko(object_type, symbol)
        version = (previous.version + 1) if previous else 1
        # For event/action/statement streams, always create a new object id/version
        now = utc_now()
        return KnowledgeObject(
            object_type=object_type,
            company_symbol=symbol,
            version=version,
            payload=payload,
            entity_refs=entity_refs,
            source_event_ids=source_event_ids,
            created_at=now,
            updated_at=now,
        )
