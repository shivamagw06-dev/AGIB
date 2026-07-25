"""In-memory institutional knowledge store (optional Supabase tables via migration)."""

from __future__ import annotations

from collections import defaultdict
from threading import RLock

from app.kip.models import (
    GraphEdge,
    GraphNode,
    KipChunk,
    KipDocument,
    TimelineEvent,
)


class KipStore:
    def __init__(self) -> None:
        self._lock = RLock()
        self.documents: dict[str, KipDocument] = {}
        self.chunks: list[KipChunk] = []
        self.lineages: dict[str, list[str]] = defaultdict(list)  # lineage_id -> doc ids newest last
        self.nodes: dict[str, GraphNode] = {}
        self.edges: list[GraphEdge] = []
        self.timeline: dict[str, list[TimelineEvent]] = defaultdict(list)  # ticker -> events
        self.themes: dict[str, set[str]] = defaultdict(set)  # theme -> doc ids
        self.company_docs: dict[str, set[str]] = defaultdict(set)

    def put_document(self, doc: KipDocument, chunks: list[KipChunk]) -> None:
        with self._lock:
            self.documents[doc.document_id] = doc
            # replace chunks for this document id (immutable docs ⇒ new id each version)
            self.chunks = [c for c in self.chunks if c.document_id != doc.document_id]
            self.chunks.extend(chunks)
            lineage = self.lineages[doc.lineage_id]
            if doc.document_id not in lineage:
                lineage.append(doc.document_id)
            for t in doc.investment.tickers:
                self.company_docs[t.upper()].add(doc.document_id)
            for theme in doc.investment.themes:
                self.themes[theme.lower()].add(doc.document_id)

    def get_document(self, document_id: str) -> KipDocument | None:
        with self._lock:
            return self.documents.get(document_id)

    def list_documents(self) -> list[KipDocument]:
        with self._lock:
            return list(self.documents.values())

    def lineage_docs(self, lineage_id: str) -> list[KipDocument]:
        with self._lock:
            ids = self.lineages.get(lineage_id, [])
            return [self.documents[i] for i in ids if i in self.documents]

    def mark_superseded(self, old_id: str, new_id: str) -> None:
        with self._lock:
            old = self.documents.get(old_id)
            new = self.documents.get(new_id)
            if old is not None:
                # Documents are immutable — store supersession pointers as new field updates
                # only allowed for lineage bookkeeping fields on the superseded record.
                updated = old.model_copy(update={"superseded_by": new_id})
                self.documents[old_id] = updated
            if new is not None and new.supersedes != old_id:
                self.documents[new_id] = new.model_copy(update={"supersedes": old_id})

    def add_timeline_events(self, events: list[TimelineEvent]) -> None:
        with self._lock:
            for ev in events:
                bucket = self.timeline[ev.ticker.upper()]
                # de-dupe by document+type+date
                key = (ev.document_id, ev.event_type, ev.event_date.isoformat())
                existing = {(e.document_id, e.event_type, e.event_date.isoformat()) for e in bucket}
                if key not in existing:
                    bucket.append(ev)
                bucket.sort(key=lambda e: e.event_date)

    def get_timeline(self, ticker: str) -> list[TimelineEvent]:
        with self._lock:
            return list(self.timeline.get(ticker.upper(), []))

    def company_document_ids(self, ticker: str) -> list[str]:
        with self._lock:
            return sorted(self.company_docs.get(ticker.upper(), set()))

    def theme_document_ids(self, theme: str) -> list[str]:
        with self._lock:
            return sorted(self.themes.get(theme.lower(), set()))

    def stats(self) -> dict[str, int]:
        with self._lock:
            return {
                "documents": len(self.documents),
                "chunks": len(self.chunks),
                "graph_nodes": len(self.nodes),
                "graph_edges": len(self.edges),
                "tickers": len(self.company_docs),
                "themes": len(self.themes),
            }
