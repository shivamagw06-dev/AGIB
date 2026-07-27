"""Strategic web enrichment — Firecrawl (markdown scrape) + Browserbase (hard-page fetch).

Roles (cost-aware):
  • Exa / Tavily — discovery search (handled in search_api + fetch._call_search_provider)
  • Firecrawl   — upgrade thin HTML / deepen top search hits into LLM-ready markdown
  • Browserbase — fallback fetch for JS-heavy or blocked pages when Firecrawl fails

Never answers or reasons — acquisition-only helpers for FAA FetchService.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any
from urllib.parse import urlparse

from app.faa.http_client import HttpClient

# Hosts that often need a real browser / proxy path (exchanges, IR portals).
_HARD_HOST_RE = re.compile(
    r"(nseindia\.com|bseindia\.com|sebi\.gov\.in|mca\.gov\.in|"
    r"moneycontrol\.com|screener\.in|trendlyne\.com|"
    r"investor\.|ir\.|filings)",
    re.I,
)

_MIN_USEFUL_CHARS = 400


def firecrawl_configured() -> bool:
    return bool((os.environ.get("FIRECRAWL_API_KEY") or "").strip())


def browserbase_configured() -> bool:
    return bool((os.environ.get("BROWSERBASE_API_KEY") or "").strip())


def enrichment_status() -> dict[str, Any]:
    return {
        "firecrawl": firecrawl_configured(),
        "browserbase": browserbase_configured(),
        "roles": {
            "exa": "semantic research / industry search",
            "firecrawl": "URL → clean markdown enrichment",
            "browserbase": "JS-heavy / blocked page fallback fetch",
        },
    }


def looks_like_hard_host(url: str) -> bool:
    try:
        host = urlparse(url).netloc or ""
    except Exception:
        host = url
    return bool(_HARD_HOST_RE.search(host) or _HARD_HOST_RE.search(url or ""))


def text_is_thin(text: str | None, *, min_chars: int = _MIN_USEFUL_CHARS) -> bool:
    t = (text or "").strip()
    if len(t) < min_chars:
        return True
    # Heuristic: mostly chrome / nav leftovers
    lower = t.lower()
    noise = sum(1 for tok in ("cookie", "subscribe", "sign in", "javascript", "enable js") if tok in lower)
    return noise >= 2 and len(t) < min_chars * 2


def firecrawl_scrape(client: HttpClient, url: str) -> dict[str, Any] | None:
    """Scrape one URL to markdown via Firecrawl. Returns {markdown, title, source} or None."""
    key = (os.environ.get("FIRECRAWL_API_KEY") or "").strip()
    if not key or not url or url.startswith("search://"):
        return None
    # Prefer v2; fall back to v1 response shape.
    for endpoint in ("https://api.firecrawl.dev/v2/scrape", "https://api.firecrawl.dev/v1/scrape"):
        resp = client.post_json(
            endpoint,
            {"url": url, "formats": ["markdown"]},
            connector_id="firecrawl",
            headers={"Authorization": f"Bearer {key}"},
            max_per_minute=12,
        )
        if resp.error or not resp.ok:
            continue
        try:
            data = json.loads(resp.text or "{}")
        except Exception:
            continue
        # v2: {success, data: {markdown, metadata}}
        # v1: {success, data: {markdown, content, metadata}}
        payload = data.get("data") if isinstance(data.get("data"), dict) else data
        if not isinstance(payload, dict):
            continue
        md = (payload.get("markdown") or payload.get("content") or "").strip()
        if not md:
            continue
        meta = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        return {
            "markdown": md[:200_000],
            "title": (meta.get("title") or meta.get("ogTitle") or "").strip() or None,
            "source": "firecrawl",
            "endpoint": endpoint,
        }
    return None


def firecrawl_search(client: HttpClient, query: str, *, limit: int = 5) -> list[dict[str, Any]]:
    """Optional Firecrawl web search — returns results that may already include markdown."""
    key = (os.environ.get("FIRECRAWL_API_KEY") or "").strip()
    if not key or not (query or "").strip():
        return []
    for endpoint in ("https://api.firecrawl.dev/v2/search", "https://api.firecrawl.dev/v1/search"):
        resp = client.post_json(
            endpoint,
            {"query": query, "limit": max(1, min(limit, 8))},
            connector_id="firecrawl",
            headers={"Authorization": f"Bearer {key}"},
            max_per_minute=10,
        )
        if resp.error or not resp.ok:
            continue
        try:
            data = json.loads(resp.text or "{}")
        except Exception:
            continue
        rows = data.get("data") if isinstance(data.get("data"), list) else data.get("results") or []
        if not isinstance(rows, list):
            # v2 sometimes nests under data.web
            nested = data.get("data")
            if isinstance(nested, dict):
                rows = nested.get("web") or nested.get("results") or []
        out: list[dict[str, Any]] = []
        for r in rows or []:
            if not isinstance(r, dict):
                continue
            url = r.get("url") or r.get("link")
            if not url:
                continue
            snippet = (r.get("description") or r.get("snippet") or r.get("markdown") or "")[:500]
            out.append(
                {
                    "title": r.get("title") or url,
                    "url": url,
                    "snippet": snippet,
                    "markdown": (r.get("markdown") or "").strip() or None,
                }
            )
        if out:
            return out
    return []


def browserbase_fetch(client: HttpClient, url: str) -> dict[str, Any] | None:
    """Fetch page content via Browserbase Fetch API (markdown preferred)."""
    key = (os.environ.get("BROWSERBASE_API_KEY") or "").strip()
    if not key or not url or url.startswith("search://"):
        return None
    # Try markdown first; fall back to raw body if plan doesn't allow markdown.
    for fmt in ("markdown", "raw"):
        resp = client.post_json(
            "https://api.browserbase.com/v1/fetch",
            {"url": url, "format": fmt, "allowRedirects": True},
            connector_id="browserbase",
            headers={"X-BB-API-Key": key, "Content-Type": "application/json"},
            max_per_minute=8,
        )
        if resp.error or not resp.ok:
            continue
        try:
            data = json.loads(resp.text or "{}")
        except Exception:
            continue
        content = data.get("content")
        if isinstance(content, dict):
            content = json.dumps(content)
        text = (content or "").strip() if isinstance(content, str) else ""
        if not text:
            continue
        return {
            "markdown": text[:200_000],
            "title": None,
            "source": "browserbase",
            "format": fmt,
            "status_code": data.get("statusCode"),
        }
    return None


def enrich_url(
    client: HttpClient,
    url: str,
    *,
    prefer_browserbase: bool = False,
) -> dict[str, Any] | None:
    """Strategic single-URL enrichment: Firecrawl first, Browserbase on hard hosts / failure."""
    if not url or url.startswith("search://"):
        return None
    hard = prefer_browserbase or looks_like_hard_host(url)

    if hard and browserbase_configured():
        bb = browserbase_fetch(client, url)
        if bb and not text_is_thin(bb.get("markdown")):
            return bb

    if firecrawl_configured():
        fc = firecrawl_scrape(client, url)
        if fc and not text_is_thin(fc.get("markdown")):
            return fc

    if browserbase_configured():
        return browserbase_fetch(client, url)
    return None


def deepen_search_results(
    client: HttpClient,
    results: list[dict[str, Any]],
    *,
    max_pages: int = 3,
) -> list[dict[str, Any]]:
    """For top search hits, attach Firecrawl/Browserbase markdown when available."""
    if not results:
        return results
    if not firecrawl_configured() and not browserbase_configured():
        return results

    deepened: list[dict[str, Any]] = []
    enriched = 0
    for r in results:
        item = dict(r)
        # Firecrawl search may already include markdown
        if item.get("markdown") and not text_is_thin(item.get("markdown")):
            item["enriched_by"] = item.get("enriched_by") or "firecrawl_search"
            deepened.append(item)
            continue
        if enriched < max_pages:
            url = str(item.get("url") or "")
            page = enrich_url(client, url)
            if page and page.get("markdown"):
                item["markdown"] = page["markdown"]
                item["enriched_by"] = page.get("source")
                if page.get("title") and not item.get("title"):
                    item["title"] = page["title"]
                enriched += 1
        deepened.append(item)
    return deepened
