"""Fetch Service — download documents with cache + optional live HTTP."""

from __future__ import annotations

import io
import os
import re
from typing import Any

from app.faa.cache import DocumentCache
from app.faa.models import CandidateDocument, FetchedDocument, sha256_bytes, sha256_text, utc_now

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


class FetchService:
    def __init__(self, cache: DocumentCache, *, live_fetch: bool = False, pdf_enabled: bool = True) -> None:
        self.cache = cache
        self.live_fetch = live_fetch
        self.pdf_enabled = pdf_enabled

    def fetch_many(self, candidates: list[CandidateDocument]) -> list[FetchedDocument]:
        return [self.fetch_one(c) for c in candidates]

    def fetch_one(self, candidate: CandidateDocument) -> FetchedDocument:
        url = (candidate.url or "").strip()
        if not url:
            return self._fail(candidate, "missing_url")

        # Cache short-circuit by URL
        skip, reason = self.cache.should_skip(url)
        if skip and not url.startswith("search://"):
            row = self.cache.lookup(url) or {}
            return FetchedDocument(
                candidate_id=candidate.candidate_id,
                title=candidate.title,
                url=url,
                connector_id=candidate.connector_id,
                document_type=candidate.document_type,
                company=candidate.company,
                symbol=candidate.symbol,
                organisation=candidate.organisation,
                published_at=candidate.published_at,
                checksum=str(row.get("checksum") or ""),
                skipped=True,
                skip_reason=reason,
                live_fetch=bool(row.get("live_fetch")),
                metadata={"cache": row},
            )

        if url.startswith("search://"):
            return self._fetch_search(candidate)

        if self.live_fetch:
            return self._live_http_fetch(candidate)

        # Offline-safe acquisition stub — still produces processable text with clear provenance.
        text = self._offline_stub_text(candidate)
        checksum = sha256_text(text)
        return FetchedDocument(
            candidate_id=candidate.candidate_id,
            title=candidate.title,
            url=url,
            connector_id=candidate.connector_id,
            document_type=candidate.document_type,
            company=candidate.company,
            symbol=candidate.symbol,
            organisation=candidate.organisation,
            published_at=candidate.published_at or utc_now().date().isoformat(),
            content_type="text/plain",
            content_text=text,
            content_bytes_len=len(text.encode("utf-8")),
            checksum=checksum,
            live_fetch=False,
            metadata={
                "mode": "offline_stub",
                "note": "FAA_LIVE_FETCH=false — enable for real HTTP downloads",
            },
        )

    def _live_http_fetch(self, candidate: CandidateDocument) -> FetchedDocument:
        url = candidate.url
        try:
            import httpx

            headers = {
                "User-Agent": "AGIB-FAA/1.0 (+https://agarwalglobalinvestments.com; institutional research bot)",
                "Accept": "text/html,application/pdf,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
            with httpx.Client(timeout=25.0, follow_redirects=True, headers=headers) as client:
                resp = client.get(url)
            raw = resp.content or b""
            checksum = sha256_bytes(raw)
            # If content unchanged, skip processing
            if self.cache.has_checksum(checksum):
                return FetchedDocument(
                    candidate_id=candidate.candidate_id,
                    title=candidate.title,
                    url=url,
                    connector_id=candidate.connector_id,
                    document_type=candidate.document_type,
                    company=candidate.company,
                    symbol=candidate.symbol,
                    organisation=candidate.organisation,
                    checksum=checksum,
                    skipped=True,
                    skip_reason="checksum_exists",
                    live_fetch=True,
                    content_bytes_len=len(raw),
                    metadata={"http_status": resp.status_code},
                )

            ctype = (resp.headers.get("content-type") or "").lower()
            text = ""
            if "pdf" in ctype or url.lower().endswith(".pdf"):
                text = self._extract_pdf(raw) if self.pdf_enabled else ""
                content_type = "application/pdf"
            else:
                text = self._html_to_text(raw.decode("utf-8", errors="ignore"))
                content_type = "text/html"

            if resp.status_code >= 400 or not text.strip():
                # Keep a minimal live provenance record even on thin pages
                text = text.strip() or (
                    f"Live fetch HTTP {resp.status_code} from {url}. "
                    f"Title: {candidate.title}. "
                    "Page returned insufficient extractable text; retained for provenance."
                )

            return FetchedDocument(
                candidate_id=candidate.candidate_id,
                title=candidate.title,
                url=url,
                connector_id=candidate.connector_id,
                document_type=candidate.document_type,
                company=candidate.company,
                symbol=candidate.symbol,
                organisation=candidate.organisation,
                published_at=candidate.published_at or utc_now().date().isoformat(),
                content_type=content_type,
                content_text=text[:200_000],
                content_bytes_len=len(raw),
                checksum=checksum,
                live_fetch=True,
                metadata={"http_status": resp.status_code, "content_type": ctype},
            )
        except Exception as exc:
            return self._fail(candidate, f"live_fetch_error: {exc}")

    def _fetch_search(self, candidate: CandidateDocument) -> FetchedDocument:
        meta = candidate.metadata or {}
        if meta.get("deferred") or not meta.get("providers_available"):
            return FetchedDocument(
                candidate_id=candidate.candidate_id,
                title=candidate.title,
                url=candidate.url,
                connector_id=candidate.connector_id,
                document_type=candidate.document_type,
                company=candidate.company,
                symbol=candidate.symbol,
                skipped=True,
                skip_reason="search_api_unconfigured",
                live_fetch=False,
                metadata=meta,
            )
        if not self.live_fetch:
            return FetchedDocument(
                candidate_id=candidate.candidate_id,
                title=candidate.title,
                url=candidate.url,
                connector_id=candidate.connector_id,
                document_type=candidate.document_type,
                company=candidate.company,
                symbol=candidate.symbol,
                skipped=True,
                skip_reason="live_fetch_disabled",
                live_fetch=False,
                metadata=meta,
            )

        provider = (meta.get("providers_available") or ["tavily"])[0]
        query = meta.get("query") or candidate.title
        results = self._call_search_provider(provider, str(query))
        # Flatten top results into one evidence document
        lines = [f"Search provider: {provider}", f"Query: {query}", ""]
        for i, r in enumerate(results[:5], 1):
            lines.append(f"{i}. {r.get('title')}")
            lines.append(f"   URL: {r.get('url')}")
            if r.get("snippet"):
                lines.append(f"   {r.get('snippet')}")
            lines.append("")
        text = "\n".join(lines).strip()
        checksum = sha256_text(text)
        return FetchedDocument(
            candidate_id=candidate.candidate_id,
            title=f"{provider} results — {query}",
            url=candidate.url,
            connector_id=candidate.connector_id,
            document_type=candidate.document_type,
            company=candidate.company,
            symbol=candidate.symbol,
            organisation=provider,
            content_type="application/json",
            content_text=text,
            content_bytes_len=len(text.encode("utf-8")),
            checksum=checksum,
            live_fetch=True,
            metadata={"provider": provider, "result_count": len(results), "results": results[:5]},
        )

    def _call_search_provider(self, provider: str, query: str) -> list[dict[str, Any]]:
        try:
            import httpx
        except Exception:
            return []

        if provider == "tavily":
            key = (os.environ.get("TAVILY_API_KEY") or "").strip()
            if not key:
                return []
            resp = httpx.post(
                "https://api.tavily.com/search",
                json={"api_key": key, "query": query, "max_results": 5, "include_answer": False},
                timeout=25.0,
            )
            data = resp.json() if resp.status_code < 500 else {}
            return [
                {"title": r.get("title"), "url": r.get("url"), "snippet": r.get("content")}
                for r in (data.get("results") or [])
                if isinstance(r, dict)
            ]

        if provider == "serpapi":
            key = (os.environ.get("SERPAPI_API_KEY") or os.environ.get("SERPAPI_KEY") or "").strip()
            if not key:
                return []
            resp = httpx.get(
                "https://serpapi.com/search.json",
                params={"q": query, "api_key": key, "engine": "google", "num": 5},
                timeout=25.0,
            )
            data = resp.json() if resp.status_code < 500 else {}
            return [
                {
                    "title": r.get("title"),
                    "url": r.get("link"),
                    "snippet": r.get("snippet"),
                }
                for r in (data.get("organic_results") or [])
                if isinstance(r, dict)
            ]

        if provider == "exa":
            key = (os.environ.get("EXA_API_KEY") or "").strip()
            if not key:
                return []
            resp = httpx.post(
                "https://api.exa.ai/search",
                headers={"x-api-key": key, "Content-Type": "application/json"},
                json={"query": query, "numResults": 5, "contents": {"text": True}},
                timeout=25.0,
            )
            data = resp.json() if resp.status_code < 500 else {}
            return [
                {
                    "title": r.get("title"),
                    "url": r.get("url"),
                    "snippet": (r.get("text") or "")[:400],
                }
                for r in (data.get("results") or [])
                if isinstance(r, dict)
            ]

        if provider == "bing":
            key = (os.environ.get("BING_SEARCH_API_KEY") or "").strip()
            if not key:
                return []
            resp = httpx.get(
                "https://api.bing.microsoft.com/v7.0/search",
                params={"q": query, "count": 5},
                headers={"Ocp-Apim-Subscription-Key": key},
                timeout=25.0,
            )
            data = resp.json() if resp.status_code < 500 else {}
            return [
                {
                    "title": r.get("name"),
                    "url": r.get("url"),
                    "snippet": r.get("snippet"),
                }
                for r in ((data.get("webPages") or {}).get("value") or [])
                if isinstance(r, dict)
            ]

        if provider == "google_cse":
            key = (os.environ.get("GOOGLE_CSE_API_KEY") or "").strip()
            cx = (os.environ.get("GOOGLE_CSE_ID") or "").strip()
            if not key or not cx:
                return []
            resp = httpx.get(
                "https://www.googleapis.com/customsearch/v1",
                params={"key": key, "cx": cx, "q": query, "num": 5},
                timeout=25.0,
            )
            data = resp.json() if resp.status_code < 500 else {}
            return [
                {"title": r.get("title"), "url": r.get("link"), "snippet": r.get("snippet")}
                for r in (data.get("items") or [])
                if isinstance(r, dict)
            ]
        return []

    def _extract_pdf(self, raw: bytes) -> str:
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(raw))
            pages = []
            for i, page in enumerate(reader.pages[:40]):
                try:
                    t = page.extract_text() or ""
                except Exception:
                    t = ""
                if t.strip():
                    pages.append(f"[page {i+1}]\n{t.strip()}")
            return "\n\n".join(pages)
        except Exception as exc:
            return f"[pdf_extract_failed] {exc}"

    def _html_to_text(self, html: str) -> str:
        # Remove scripts/styles
        html = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
        text = _TAG_RE.sub(" ", html)
        text = _WS_RE.sub(" ", text)
        return text.strip()

    def _offline_stub_text(self, candidate: CandidateDocument) -> str:
        return (
            f"{candidate.title}\n"
            f"Source URL: {candidate.url}\n"
            f"Connector: {candidate.connector_id}\n"
            f"Document type: {candidate.document_type}\n"
            f"Company: {candidate.company or 'n/a'} ({candidate.symbol or 'n/a'})\n"
            f"Organisation: {candidate.organisation or 'n/a'}\n\n"
            "FAA offline acquisition stub. Enable FAA_LIVE_FETCH=true to download the live page/PDF. "
            "This record preserves the discovery target so FRE can track intended public sources."
        )

    def _fail(self, candidate: CandidateDocument, error: str) -> FetchedDocument:
        return FetchedDocument(
            candidate_id=candidate.candidate_id,
            title=candidate.title,
            url=candidate.url,
            connector_id=candidate.connector_id,
            document_type=candidate.document_type,
            company=candidate.company,
            symbol=candidate.symbol,
            organisation=candidate.organisation,
            error=error,
            live_fetch=self.live_fetch,
        )
