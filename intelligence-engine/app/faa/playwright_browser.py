"""Playwright headless Chromium for FAA — JS pages + free web search fallback.

Strategic roles (self-hosted, no API key):
  • Render IR / exchange / shareholding pages that need JavaScript
  • Extract visible text + links after networkidle
  • Optional DuckDuckGo HTML search when cloud search keys are absent

Enable with FAA_PLAYWRIGHT=true (or auto when FAA_LIVE_FETCH=true) and:
  playwright install chromium

Sync Playwright is always executed in a dedicated worker thread so it is safe
under FastAPI/uvicorn asyncio workers.
"""

from __future__ import annotations

import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, TypeVar
from urllib.parse import quote_plus

_LOCK = threading.Lock()
_POOL = ThreadPoolExecutor(max_workers=1, thread_name_prefix="faa-playwright")
_INIT_ERROR: str | None = None
_READY: bool | None = None

_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 AGIB-FAA-Playwright/1.0"
)

T = TypeVar("T")


def playwright_enabled() -> bool:
    """Enabled when FAA_PLAYWRIGHT=true, or by default whenever FAA_LIVE_FETCH is on."""
    raw = (os.environ.get("FAA_PLAYWRIGHT") or os.environ.get("PLAYWRIGHT") or "").strip().lower()
    if raw in {"0", "false", "no", "off"}:
        return False
    if raw in {"1", "true", "yes", "on"}:
        return True
    live = (os.environ.get("FAA_LIVE_FETCH") or "").strip().lower()
    return live in {"1", "true", "yes", "on"}


def _run_in_browser_thread(fn: Callable[[], T], *, timeout: float = 55.0) -> T:
    """Run sync Playwright off the asyncio event-loop thread."""
    fut = _POOL.submit(fn)
    return fut.result(timeout=timeout)


def playwright_available() -> bool:
    """True when enabled and the Playwright package imports.

    Chromium launch is validated lazily on first fetch (never on health checks)
    so FastAPI health stays cheap and free-tier restarts stay stable.
    """
    if not playwright_enabled():
        return False
    if _READY is False and _INIT_ERROR and "asyncio" not in (_INIT_ERROR or ""):
        # Known missing binary / install failure — don't keep retrying every call.
        if "launch_failed" in (_INIT_ERROR or "") or "import_failed" in (_INIT_ERROR or ""):
            return False
    try:
        import playwright  # noqa: F401
        from playwright.sync_api import sync_playwright  # noqa: F401
    except Exception:
        return False
    return True


def playwright_status(*, probe: bool = False) -> dict[str, Any]:
    global _INIT_ERROR, _READY
    enabled = playwright_enabled()
    out: dict[str, Any] = {
        "enabled": enabled,
        "ready": bool(_READY) if _READY is not None else False,
        "role": "js_render_fetch_and_free_web_search",
        "error": _INIT_ERROR,
    }
    if not enabled:
        out["hint"] = "Set FAA_PLAYWRIGHT=true and run: playwright install chromium"
        return out
    try:
        import playwright  # noqa: F401
        from playwright.sync_api import sync_playwright  # noqa: F401
    except Exception as exc:
        _INIT_ERROR = f"import_failed: {exc}"
        _READY = False
        out["error"] = _INIT_ERROR
        out["ready"] = False
        out["hint"] = "pip install playwright && playwright install chromium"
        return out

    if not probe and _READY is not None:
        out["ready"] = bool(_READY)
        out["error"] = _INIT_ERROR
        return out

    def _probe() -> bool:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
        return True

    try:
        with _LOCK:
            _run_in_browser_thread(_probe, timeout=40.0)
        _READY = True
        _INIT_ERROR = None
        out["ready"] = True
        out["error"] = None
    except Exception as exc:
        _READY = False
        _INIT_ERROR = f"launch_failed: {exc}"
        out["ready"] = False
        out["error"] = _INIT_ERROR
        out["hint"] = "playwright install chromium  (or playwright install --with-deps chromium)"
    return out


def _html_to_text(html: str) -> str:
    html = re.sub(r"(?is)<(script|style|noscript).*?>.*?</\1>", " ", html or "")
    html = re.sub(r"(?is)<!--.*?-->", " ", html)
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def fetch_page(
    url: str,
    *,
    timeout_ms: int = 35_000,
    wait_until: str = "domcontentloaded",
) -> dict[str, Any] | None:
    """Navigate with Chromium and return title + text (+ optional pdf links)."""
    if not playwright_enabled() or not url or url.startswith("search://"):
        return None
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except Exception:
        return None

    def _work() -> dict[str, Any] | None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                context = browser.new_context(
                    user_agent=_UA,
                    ignore_https_errors=True,
                    viewport={"width": 1365, "height": 900},
                )
                page = context.new_page()
                page.set_default_timeout(timeout_ms)
                page.goto(url, wait_until=wait_until, timeout=timeout_ms)
                try:
                    page.wait_for_load_state("networkidle", timeout=8_000)
                except Exception:
                    pass
                title = (page.title() or "").strip()
                try:
                    body = page.inner_text("body", timeout=5_000)
                except Exception:
                    body = _html_to_text(page.content())
                hrefs: list[str] = []
                try:
                    hrefs = page.eval_on_selector_all(
                        "a[href]",
                        "els => els.map(e => e.href).filter(Boolean).slice(0, 80)",
                    )
                except Exception:
                    hrefs = []
                pdf_links = [h for h in hrefs if isinstance(h, str) and ".pdf" in h.lower()][:20]
                text = (body or "").strip()
                if pdf_links:
                    text = text + "\n\nPDF links:\n" + "\n".join(f"- {u}" for u in pdf_links)
                if not text:
                    return None
                return {
                    "markdown": text[:200_000],
                    "title": title or None,
                    "source": "playwright",
                    "format": "text",
                    "pdf_links": pdf_links,
                    "url": page.url,
                }
            finally:
                browser.close()

    global _INIT_ERROR, _READY
    try:
        with _LOCK:
            result = _run_in_browser_thread(_work, timeout=max(20.0, timeout_ms / 1000.0 + 15.0))
        if result:
            _READY = True
            _INIT_ERROR = None
        return result
    except Exception as exc:
        _INIT_ERROR = str(exc)[:240]
        _READY = False
        return None


def web_search(query: str, *, limit: int = 5) -> list[dict[str, Any]]:
    """Free DuckDuckGo HTML search via Playwright (no API key)."""
    q = (query or "").strip()
    if not q or not playwright_enabled():
        return []
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except Exception:
        return []

    url = f"https://html.duckduckgo.com/html/?q={quote_plus(q)}"

    def _work() -> list[dict[str, Any]]:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                context = browser.new_context(user_agent=_UA, ignore_https_errors=True)
                page = context.new_page()
                page.set_default_timeout(30_000)
                page.goto(url, wait_until="domcontentloaded")
                try:
                    page.wait_for_selector("a.result__a", timeout=10_000)
                except Exception:
                    pass
                rows = page.eval_on_selector_all(
                    "div.result",
                    """els => els.slice(0, 10).map(el => {
                        const a = el.querySelector('a.result__a');
                        const sn = el.querySelector('.result__snippet');
                        return a ? {
                          title: (a.textContent || '').trim(),
                          url: a.href,
                          snippet: sn ? (sn.textContent || '').trim() : ''
                        } : null;
                    }).filter(Boolean)""",
                )
                out: list[dict[str, Any]] = []
                for r in rows or []:
                    if not isinstance(r, dict) or not r.get("url"):
                        continue
                    out.append(
                        {
                            "title": r.get("title") or r.get("url"),
                            "url": r.get("url"),
                            "snippet": (r.get("snippet") or "")[:500],
                        }
                    )
                    if len(out) >= max(1, min(limit, 8)):
                        break
                return out
            finally:
                browser.close()

    global _INIT_ERROR, _READY
    try:
        with _LOCK:
            result = _run_in_browser_thread(_work, timeout=45.0)
        _READY = True
        _INIT_ERROR = None
        return result
    except Exception as exc:
        _INIT_ERROR = str(exc)[:240]
        _READY = False
        return []
