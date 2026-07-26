"""FAA pipeline — Discovery → Fetch → Process → Index → notify FRE."""

from __future__ import annotations

from typing import Any

from app.faa.cache import DocumentCache
from app.faa.discovery import DiscoveryService
from app.faa.fetch import FetchService
from app.faa.index_service import IndexService
from app.faa.models import AcquisitionResult, FaaMetrics, utc_now
from app.faa.processing import ProcessingService


class FaaPipeline:
    def __init__(
        self,
        *,
        cache: DocumentCache | None = None,
        fre: Any | None = None,
        aoi: Any | None = None,
        live_fetch: bool = False,
        pdf_enabled: bool = True,
        metrics: FaaMetrics | None = None,
    ) -> None:
        self.cache = cache or DocumentCache()
        self.fre = fre
        self.aoi = aoi
        self.live_fetch = live_fetch
        self.metrics = metrics or FaaMetrics()
        self.discovery = DiscoveryService(live_fetch=live_fetch)
        self.fetch = FetchService(self.cache, live_fetch=live_fetch, pdf_enabled=pdf_enabled)
        self.processing = ProcessingService()
        self.index = IndexService(self.cache, fre=fre)

    def bind_fre(self, fre: Any) -> None:
        self.fre = fre
        self.index.bind_fre(fre)

    def acquire_for_query(self, query: str, *, limit: int = 24) -> AcquisitionResult:
        result = AcquisitionResult(query=query, live_fetch=self.live_fetch)
        tasks, candidates = self.discovery.discover(query, aoi=self.aoi, limit=limit)
        result.discovered = len(candidates)
        result.candidates = [c.to_dict() for c in candidates]
        self.metrics.discovery_runs += 1
        self.metrics.candidates_found += len(candidates)

        fetched = self.fetch.fetch_many(candidates)
        self.metrics.downloads_attempted += len(fetched)

        errors = []
        succeeded = []
        for f in fetched:
            if f.skipped:
                result.skipped_cached += 1
                self.metrics.cache_hits += 1
            elif f.error:
                result.failed += 1
                self.metrics.downloads_failed += 1
                errors.append(f"{f.url}: {f.error}")
            else:
                succeeded.append(f)
                self.metrics.downloads_succeeded += 1

        processed = self.processing.process(succeeded)
        result.processed = len(processed)
        self.metrics.processed += len(processed)

        if processed and self.fre is not None:
            indexed = self.index.index(processed, fetched=succeeded)
            result.indexed_to_fre = int(indexed.get("indexed") or 0)
            self.metrics.indexed_to_fre += result.indexed_to_fre
        elif processed and self.fre is None:
            errors.append("fre_unbound_not_indexed")

        result.fetched = len(succeeded)
        result.documents = [d.to_dict() for d in processed]
        result.errors = errors
        result.finished_at = utc_now()
        self.metrics.last_run_at = result.finished_at.isoformat()
        # attach task count for observability
        result.candidates = [
            {**c, "tasks_planned": len(tasks)} if i == 0 else c
            for i, c in enumerate(result.candidates)
        ]
        return result
