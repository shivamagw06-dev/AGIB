"""Ask ticker binding guard — never invent prose tokens as companies."""

from __future__ import annotations

import re
from typing import Any, Optional

from app.kip.extractors import KNOWN_TICKERS, TICKER_STOPWORDS, looks_like_equity_ticker

# Explicit global names that must bind even when ERE returns a Theme first.
_ALIAS_BIND: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bmeta(?:\s+platforms)?\b|\bfacebook\b|\bfb\b", re.I), "META"),
    (re.compile(r"\bapple\b|\baapl\b", re.I), "AAPL"),
    (re.compile(r"\bmicrosoft\b|\bmsft\b", re.I), "MSFT"),
    (re.compile(r"\bgoogle\b|\balphabet\b|\bgoogl\b", re.I), "GOOGL"),
    (re.compile(r"\bamazon\b|\bamzn\b", re.I), "AMZN"),
    (re.compile(r"\bnvidia\b|\bnvda\b", re.I), "NVDA"),
    (re.compile(r"\breliance(?:\s+industries)?\b|\bril\b", re.I), "RELIANCE"),
    (re.compile(r"\binfosys\b|\binfy\b", re.I), "INFY"),
    (re.compile(r"\btcs\b|\btata consultancy\b", re.I), "TCS"),
    (re.compile(r"\bhdfc\s*bank\b", re.I), "HDFCBANK"),
    (re.compile(r"\bicici\s*bank\b|\bicicibank\b", re.I), "ICICIBANK"),
)


def accept_detected_ticker(
    raw: Any,
    *,
    ere_blocked: bool = False,
    allow_when_blocked: bool = False,
) -> Optional[str]:
    """Return a safe equity ticker or None.

    Soft packs must not bind research-prose tokens (SUMMARIZE, WHAT, CAPEX)
    or unrelated symbols when ERE has blocked research / needs clarification.
    """
    if raw is None:
        return None
    t = str(raw).upper().replace(".NS", "").replace(".BO", "").strip()
    if not t or "_" in t:
        return None
    if t in TICKER_STOPWORDS:
        return None
    if ere_blocked and not allow_when_blocked:
        return None
    if looks_like_equity_ticker(t) or t in KNOWN_TICKERS:
        return t
    return None


def alias_ticker_from_question(question: str) -> Optional[str]:
    q = str(question or "")
    for pattern, ticker in _ALIAS_BIND:
        if pattern.search(q):
            return ticker
    return None


def looks_like_framework_meta_executive(text: str) -> bool:
    """True when ICE/framework scaffolding is being passed off as the answer."""
    low = (text or "").lower().strip()
    if not low:
        return False
    meta_markers = (
        "frameworks applied:",
        "frameworks applied",
        "playbook:",
        "reasoning follows the analytical checklist",
        "template: research note",
        "analyse via",
        "analyze via",
        "framework input domain",
        "committee vote",
        "fill from existing reasoning",
        "evidence coverage=",
        "entity-bound analysis",
        "governance path:",
        "lidi validated publish",
    )
    if any(m in low for m in meta_markers):
        return True
    if low.startswith("intent:") and ("template:" in low or "frameworks" in low):
        return True
    if low.startswith("intent:"):
        return True
    # Committee boilerplate leaked as lead narrative
    if "only when franchise" in low and "position sizing" in low:
        return True
    return False
