"""Playwright headless Chromium for FAA — JS pages + free web search fallback.

Strategic roles (self-hosted, no API key):
  • Render IR / exchange / shareholding pages that need JavaScript
  • Extract visible text + links after networkidle
  • Optional DuckDuckGo HTML search when cloud search keys are absent

Enable with FAA_PLAYWRIGHT=true and install browsers:
  playwright install chromium
"""

from __future__ import annotations

import os
import re
import threading
from typing import Any
from urllib.parse import quote_plus

_LOCK = threading.Lock()
_BROWSER = None
_PLAYWRIGHT = None
_INIT_ERROR: str | None = None

_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 AGIB-FAA-Playwright/1.0"
)


def playwright_enabled() -> bool:
    """Enabled when FAA_PLAYWRIGHT=true, or by default whenever FAA_LIVE_FETCH is on.

    Soft-fails at fetch time if Chromium binaries are missing — production
    Render services often omit new render.yaml env keys until set manually.
    """
    raw = (os.environ.get("FAA_PLAYWRIGHT") or os.environ.get("PLAYWRIGHT") or "").strip().lower()
    if raw in {"0", "false", "no", "off"}:
        return False
    if raw in {"1", "true", "yes", "on"}:
        return True
    live = (os.environ.get("FAA_LIVE_FETCH") or "").strip().lower()
    return live in {"1", "true", "yes", "on"}


def playwright_available() -> bool:
    """True when enabled and Chromium can be imported/launched."""
    if not playwright_enabled():
        return False
    status = playwright_status()
    return bool(status.get("ready"))


def playwright_status() -> dict[str, Any]:
    global _INIT_ERROR
    enabled = playwright_enabled()
    out: dict[str, Any] = {
        "enabled": enabled,
        "ready": False,
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
        out["error"] = _INIT_ERROR
        out["hint"] = "pip install playwright && playwright install chromium"
        return out
    # Probe binary without keeping a long-lived browser in status checks
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
        out["ready"] = True
        _INIT_ERROR = None
        out["error"] = None
    except Exception as exc:
        _INIT_ERROR = f"launch_failed: {exc}"
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
        from playwright.sync_api import sync_playwright
    except Exception:
        return None

    with _LOCK:
        try:
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
                    # Allow late JS tables (shareholding, calendars) without hanging forever
                    try:
                        page.wait_for_load_state("networkidle", timeout=8_000)
                    except Exception:
                        pass
                    title = (page.title() or "").strip()
                    # Prefer readable text over raw HTML chrome
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
        except Exception as exc:
            global _INIT_ERROR
            _INIT_ERROR = str(exc)[:240]
            return None


def web_search(query: str, *, limit: int = 5) -> list[dict[str, Any]]:
    """Free DuckDuckGo HTML search via Playwright (no API key)."""
    q = (query or "").strip()
    if not q or not playwright_enabled():
        return []
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return []

    url = f"https://html.duckduckgo.com/html/?q={quote_plus(q)}"
    with _LOCK:
        try:
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
        except Exception as exc:
            global _INIT_ERROR
            _INIT_ERROR = str(exc)[:240]
            return []
