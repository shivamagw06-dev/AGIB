"""Index Service — push processed documents into FRE (and optional cache update)."""

from __future__ import annotations

from typing import Any

from app.faa.cache import DocumentCache
from app.faa.models import FetchedDocument
from app.fre.models import FreDocument


class IndexService:
    def __init__(self, cache: DocumentCache, *, fre: Any | None = None) -> None:
        self.cache = cache
        self.fre = fre

    def bind_fre(self, fre: Any) -> None:
        self.fre = fre

    def index(
        self,
        documents: list[FreDocument],
        fetched: list[FetchedDocument] | None = None,
    ) -> dict[str, Any]:
        if self.fre is None:
            return {"indexed": 0, "error": "fre_unbound"}

        # Prefer FRE pipeline ingest for chunk/embed/index
        result = self.fre.pipeline.ingest_documents(documents, publish_kip=False)
        fetched_by_checksum = {f.checksum: f for f in (fetched or []) if f.checksum}
        for doc in documents:
            src = fetched_by_checksum.get(doc.checksum)
            self.cache.put(
                url=doc.url,
                checksum=doc.checksum,
                title=doc.title,
                document_type=doc.document_type,
                connector_id=(src.connector_id if src else doc.source),
                live_fetch=bool(src.live_fetch) if src else False,
                fre_document_id=doc.document_id,
            )
        return {
            "indexed": len(result.get("ingested") or []),
            "chunks": result.get("chunks") or 0,
            "failed": result.get("failed") or 0,
            "fre_snapshot": result.get("snapshot") or {},
        }
