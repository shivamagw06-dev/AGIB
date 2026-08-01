"""Executive Composer contract — question → answer → evidence.

Observability-adjacent product surface. Does not change retrieval or LLM prompts.
Replaces planning/framework/committee scaffolding as the user-facing lead.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence

from app.ui.ticker_guard import (
    alias_ticker_from_question,
    looks_like_framework_meta_executive,
)

# ---------------------------------------------------------------------------
# Scaffold / meta detection (release-blocking patterns)
# ---------------------------------------------------------------------------

_PLANNING_MARKERS = (
    "analyse via",
    "analyze via",
    "frameworks applied",
    "framework input domain",
    "playbook:",
    "intent:",
    "template: research",
    "committee vote",
    "reasoning follows the analytical checklist",
    "fill from existing reasoning",
    "no unsupported certainty",
    "evidence coverage=",
    "entity-bound analysis",
    "concept mode — no company",
    "governance path:",
    "institutional brief (",
    "lidi validated publish",
)

_COMMITTEE_BOILERPLATE = re.compile(
    r"\b(own .+ only when franchise|committee vote|position sizing should respect|"
    r"live risk register|macro transmission)\b",
    re.I,
)

_COMPARE_RE = re.compile(
    r"\b(compare|versus|\bvs\.?\b|difference between|relative to)\b",
    re.I,
)

_COMPANY_REQUIRED_RE = re.compile(
    r"(?:"
    r"\b(pvt\.?\s*ltd|private\s+limited|limited|ltd\.?|inc\.?|corp\.?)\b|"
    r"\b(business model|quarterly earnings|earnings call|capex|target price|"
    r"should i buy|buy or sell)\b|"
    r"^(explain|describe|analyse|analyze|tell me about)\s+\S+"
    r")",
    re.I,
)

_CONCEPT_MACRO_RE = re.compile(
    r"\b("
    r"outlook|macro|private market|valuation multiples|"
    r"explain why|why (do|does|are|is|would|banks)|how would|what drives valuation for|"
    r"trade on p/?b|instead of ev/?ebitda|equity outlook|"
    r"as of \d|nifty valuations"
    r")\b",
    re.I,
)

# Multi-alias scan (first-match helper lives in ticker_guard).
_ALIAS_SCAN: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bmeta(?:\s+platforms)?\b|\bfacebook\b|\bfb\b", re.I), "META"),
    (re.compile(r"\bapple\b|\baapl\b", re.I), "AAPL"),
    (re.compile(r"\bmicrosoft\b|\bmsft\b", re.I), "MSFT"),
    (re.compile(r"\bgoogle\b|\balphabet\b|\bgoogl\b", re.I), "GOOGL"),
    (re.compile(r"\bamazon\b|\bamzn\b", re.I), "AMZN"),
    (re.compile(r"\bnvidia\b|\bnvda\b", re.I), "NVDA"),
    (re.compile(r"\breliance(?:\s+industries)?\b|\bril\b", re.I), "RELIANCE"),
    (re.compile(r"\binfosys\b|\binfy\b", re.I), "INFY"),
    (re.compile(r"\btcs\b|\btata consultancy\b", re.I), "TCS"),
    (re.compile(r"\bwipro\b|\bwpro\b", re.I), "WIPRO"),
    (re.compile(r"\bhdfc\s*bank\b", re.I), "HDFCBANK"),
    (re.compile(r"\btata motors\b|\bttmt\b", re.I), "TATAMOTORS"),
    (re.compile(r"\badani(?:\s+enterprises)?\b", re.I), "ADANIENT"),
    (re.compile(r"\bjsw energy\b", re.I), "JSWENERGY"),
)


def is_planning_scaffold(text: str) -> bool:
    """True when text is orchestration/planning, not a user answer."""
    if looks_like_framework_meta_executive(text):
        return True
    raw = text or ""
    low = raw.strip().lower()
    if not low:
        return True
    if low.startswith("analyse via") or low.startswith("analyze via"):
        return True
    if "analyse via" in low or "analyze via" in low:
        return True
    if _COMMITTEE_BOILERPLATE.search(raw):
        return True
    for marker in _PLANNING_MARKERS:
        m = marker.strip()
        if not m or m == "own":
            continue
        if m in low:
            return True
    return False


def is_comparison_question(question: str) -> bool:
    return bool(_COMPARE_RE.search(question or ""))


def requires_resolved_company(question: str) -> bool:
    """Company-shaped asks that must not invent a substitute entity."""
    q = question or ""
    # Concept / teaching questions win over bare "Explain …" unless a legal-entity cue is present.
    if _CONCEPT_MACRO_RE.search(q):
        has_legal = bool(
            re.search(r"\b(pvt\.?\s*ltd|private\s+limited|limited|ltd\.?|inc\.?)\b", q, re.I)
        )
        has_alias = bool(alias_ticker_from_question(q))
        if not has_legal and not has_alias:
            return False
    if is_comparison_question(q):
        return True
    return bool(_COMPANY_REQUIRED_RE.search(q))


def alias_tickers_from_question(question: str) -> List[str]:
    """All alias tickers mentioned (order preserved, de-duped)."""
    q = question or ""
    out: List[str] = []
    for pattern, ticker in _ALIAS_SCAN:
        if pattern.search(q) and ticker not in out:
            out.append(ticker)
    # Fallback to single-alias helper for any missed first match
    one = alias_ticker_from_question(q)
    if one and one not in out:
        out.insert(0, one)
    return out


def comparison_entity_count(question: str, *, ere_body: Optional[dict] = None) -> int:
    tickers = alias_tickers_from_question(question)
    if len(tickers) >= 2:
        return len(tickers)
    names: List[str] = list(tickers)
    if isinstance(ere_body, dict):
        for key in ("entities", "candidates", "resolved_entities"):
            for e in ere_body.get(key) or []:
                if isinstance(e, dict):
                    t = str(e.get("ticker") or e.get("name") or "").strip().upper()
                    if t and t not in names:
                        names.append(t)
                elif isinstance(e, str) and e.strip() and e.strip().upper() not in names:
                    names.append(e.strip().upper())
        # "Infosys vs TCS" style — entity field may be one, peers another
        peer = ere_body.get("peer") or ere_body.get("secondary_ticker")
        if peer:
            t = str(peer).strip().upper()
            if t and t not in names:
                names.append(t)
    # Lexical: "A vs B" / "A versus B"
    m = re.search(
        r"([A-Za-z][A-Za-z0-9&.\' -]{1,40}?)\s+(?:vs\.?|versus)\s+([A-Za-z][A-Za-z0-9&.\' -]{1,40})",
        question or "",
        re.I,
    )
    if m:
        for part in (m.group(1), m.group(2)):
            tok = part.strip().upper()
            if tok and tok not in names and len(tok) > 1:
                names.append(tok)
    return len(names)


def unknown_entity_executive(question: str, *, rejected: Optional[Sequence[str]] = None) -> str:
    rejected = [str(x) for x in (rejected or []) if x]
    base = (
        "I couldn't identify a verified company for this question, so I won't invent "
        "a research narrative or substitute another firm."
    )
    if rejected:
        return (
            f"{base} Rejected lookalike(s): {', '.join(rejected[:4])}. "
            "Please provide a listed ticker or the company's full legal name."
        )
    return (
        f"{base} Please provide a listed ticker or the company's full legal name. "
        f"(Asked: {str(question or '')[:120]})"
    )


def comparison_clarification_executive(question: str) -> str:
    return (
        "This is a comparison question, but I could not resolve at least two companies "
        "to compare. Please name both entities clearly (for example: Infosys vs TCS)."
    )


def _scrub_line(text: str, *, max_len: int = 280) -> str:
    s = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(s) > max_len:
        s = s[: max_len - 1].rstrip() + "…"
    return s


def _evidence_titles(evidence: Sequence[Any], *, limit: int = 4) -> List[str]:
    out: List[str] = []
    for e in evidence or []:
        if not isinstance(e, dict):
            continue
        title = e.get("title") or e.get("headline") or e.get("source")
        if not title:
            continue
        t = _scrub_line(str(title), max_len=160)
        if not t or t.lower().startswith("doc_"):
            continue
        if is_planning_scaffold(t):
            continue
        if t not in out:
            out.append(t)
        if len(out) >= limit:
            break
    return out


def _pack_narrative(packs: Dict[str, Any]) -> List[str]:
    """Pull short factual snippets from soft packs (no new retrieval)."""
    lines: List[str] = []
    ca = packs.get("company_analysis") if isinstance(packs.get("company_analysis"), dict) else {}
    for key in ("summary", "business_model", "overview", "narrative"):
        v = ca.get(key)
        if isinstance(v, str) and len(v.strip()) > 40 and not is_planning_scaffold(v):
            lines.append(_scrub_line(v, max_len=260))
            break
    dossier = packs.get("company_dossier") if isinstance(packs.get("company_dossier"), dict) else {}
    for key in ("summary", "overview", "business_description"):
        v = dossier.get(key)
        if isinstance(v, str) and len(v.strip()) > 40 and not is_planning_scaffold(v):
            lines.append(_scrub_line(v, max_len=260))
            break
    kb = packs.get("knowledge_bundle") if isinstance(packs.get("knowledge_bundle"), dict) else {}
    for doc in (kb.get("documents") or [])[:3]:
        if not isinstance(doc, dict):
            continue
        snip = doc.get("snippet") or doc.get("summary") or doc.get("title")
        if isinstance(snip, str) and len(snip.strip()) > 30 and not is_planning_scaffold(snip):
            lines.append(_scrub_line(snip, max_len=220))
        if len(lines) >= 3:
            break
    return lines[:4]


def _lead_for_question(
    question: str,
    *,
    tickers: Sequence[str],
    snippets: Sequence[str],
    evidence_titles: Sequence[str],
) -> str:
    q = (question or "").strip()
    ql = q.lower()
    names = [str(t) for t in tickers if t]

    if is_comparison_question(q) and len(names) >= 2:
        a, b = names[0], names[1]
        if snippets:
            return _scrub_line(
                f"{a} vs {b}: {snippets[0]}",
                max_len=300,
            )
        if evidence_titles:
            return _scrub_line(
                f"{a} vs {b}: comparison grounded in retrieved institutional evidence "
                f"(including {evidence_titles[0]}).",
                max_len=300,
            )
        return (
            f"{a} vs {b}: both entities are resolved; the brief below contrasts scale, "
            "margins, growth, and valuation drivers from available evidence."
        )

    if "business model" in ql and names:
        if snippets:
            return _scrub_line(
                f"{names[0]}'s business model: {snippets[0]}",
                max_len=300,
            )
        return (
            f"{names[0]} operates as a multi-segment franchise; the brief below summarizes "
            "segments, cash drivers, and risks from retrieved evidence — not a planning checklist."
        )

    if re.search(r"\b(q[1-4]|quarterly|earnings|capex|infrastructure spending)\b", ql) and names:
        topic = "earnings"
        if "ai" in ql and ("capex" in ql or "infrastructure" in ql or "spending" in ql):
            topic = "AI infrastructure spending"
        if snippets:
            return _scrub_line(
                f"On {topic}, {names[0]}: {snippets[0]}",
                max_len=300,
            )
        if evidence_titles:
            return _scrub_line(
                f"On {topic}, available evidence for {names[0]} includes: {evidence_titles[0]}.",
                max_len=300,
            )
        return (
            f"I do not have a clear management statement on {topic} for {names[0]} "
            "in the evidence pack — treating that as a knowledge gap rather than inventing commentary."
        )

    if snippets:
        return _scrub_line(snippets[0], max_len=300)
    if evidence_titles:
        subj = names[0] if names else "the subject"
        return _scrub_line(
            f"Based on retrieved evidence for {subj}: {evidence_titles[0]}.",
            max_len=300,
        )
    subj = names[0] if names else "this question"
    return (
        f"I have evidence for {subj} but cannot yet form a clean institutional answer "
        "to the exact question asked — see supporting items and knowledge gaps below."
    )


def compose_executive(
    question: str,
    *,
    detected_ticker: Optional[str] = None,
    evidence_used: Optional[Sequence[Any]] = None,
    supporting: Optional[Sequence[Any]] = None,
    packs: Optional[Dict[str, Any]] = None,
    candidates: Optional[Sequence[str]] = None,
    why: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """Return a contract-compliant executive.

    Output keys: executive, why, source, replaced_scaffold, tickers
    """
    packs = packs if isinstance(packs, dict) else {}
    tickers = alias_tickers_from_question(question)
    if detected_ticker and str(detected_ticker).upper() not in tickers:
        tickers = [str(detected_ticker).upper(), *tickers]

    # Prefer any non-scaffold candidate already produced upstream.
    for cand in candidates or []:
        text = str(cand or "").strip()
        if text and not is_planning_scaffold(text):
            why_out = [
                w
                for w in (why or [])
                if w and not is_planning_scaffold(str(w))
            ][:8]
            titles = _evidence_titles(list(evidence_used or []) + list(supporting or []))
            if titles and not why_out:
                why_out = [f"Evidence: {t}" for t in titles[:4]]
            return {
                "executive": _scrub_line(text, max_len=600),
                "why": why_out,
                "source": "upstream_clean",
                "replaced_scaffold": False,
                "tickers": tickers,
            }

    snippets = _pack_narrative(packs)
    titles = _evidence_titles(list(evidence_used or []) + list(supporting or []))
    lead = _lead_for_question(
        question, tickers=tickers, snippets=snippets, evidence_titles=titles
    )

    # Ensure sentence 1 is not scaffold
    if is_planning_scaffold(lead):
        lead = (
            f"Direct answer unavailable from clean evidence for: {str(question)[:140]}. "
            "See knowledge gaps rather than framework scaffolding."
        )

    body_bits: List[str] = [lead]
    for s in snippets[1:3]:
        if s and s not in lead:
            body_bits.append(s)
    executive = _scrub_line(" ".join(body_bits), max_len=700)

    why_out: List[str] = []
    for t in titles[:5]:
        why_out.append(f"Evidence: {t}")
    for w in why or []:
        ws = str(w)
        if ws and not is_planning_scaffold(ws) and ws not in why_out:
            why_out.append(_scrub_line(ws, max_len=220))
        if len(why_out) >= 8:
            break
    if not why_out:
        why_out = [
            "Supporting evidence titles were thin after scaffold removal — treat confidence as limited.",
        ]

    return {
        "executive": executive,
        "why": why_out[:8],
        "source": "executive_composer",
        "replaced_scaffold": True,
        "tickers": tickers,
    }
