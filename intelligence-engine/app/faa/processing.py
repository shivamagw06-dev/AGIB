"""Processing Service — clean + prepare documents for FRE ingest."""

from __future__ import annotations

from typing import Any

from app.faa.models import FetchedDocument
from app.fre.acquisition import acquire_from_text
from app.fre.models import FreDocument
from app.fre.parser import clean_text


class ProcessingService:
    def process(self, fetched: list[FetchedDocument]) -> list[FreDocument]:
        out: list[FreDocument] = []
        for item in fetched:
            if item.skipped or item.error or not (item.content_text or "").strip():
                continue
            cleaned = clean_text(item.content_text)
            if not cleaned:
                continue
            doc = acquire_from_text(
                title=item.title,
                text=cleaned,
                url=item.url,
                source=item.connector_id,
                document_type=item.document_type,
                company=item.company,
                symbol=item.symbol,
                published_at=item.published_at,
                organisation=item.organisation,
            )
            doc.checksum = item.checksum or doc.checksum
            doc.content_type = item.content_type
            doc.metadata = {
                **(doc.metadata or {}),
                "faa_fetch_id": item.fetch_id,
                "faa_live_fetch": item.live_fetch,
                "faa_connector": item.connector_id,
                **(item.metadata or {}),
            }
            out.append(doc)
        return out
