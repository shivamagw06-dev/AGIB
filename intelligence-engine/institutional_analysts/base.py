"""Shared helpers for analyst opinions — no engine calls."""

from __future__ import annotations

import re
from typing import Any

_INTERNAL = re.compile(
    r"\b(CID|LEO|IRP|DVC|ECP|SIF|FLE|MEE|AOI|EVE|IIE|KF|KIP|FAA|FRE|AIL|CAE|"
    r"Company Analysis|Financial Intelligence|MarketDataClient|Yahoo|Groww|IndianAPI|"
    r"AlphaVantage|TwelveData|Capital IQ|provider|API|engine)\b",
    re.I,
)


def scrub_public(text: Any, *, limit: int = 420) -> str:
    s = str(text or "").strip()
    if not s:
        return ""
    s = _INTERNAL.sub("institutional research", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:limit]


def as_list(value: Any, *, limit: int = 8) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        item = scrub_public(value, limit=220)
        return [item] if item else []
    out: list[str] = []
    if isinstance(value, dict):
        for k, v in value.items():
            if isinstance(v, (str, int, float)) and str(v).strip():
                out.append(scrub_public(f"{k}: {v}", limit=180))
            elif isinstance(v, list):
                out.extend(as_list(v, limit=limit))
            if len(out) >= limit:
                break
        return out[:limit]
    for item in value:
        if isinstance(item, dict):
            title = item.get("title") or item.get("claim") or item.get("label") or item.get("name")
            summary = item.get("summary") or item.get("text") or item.get("snippet")
            piece = scrub_public(title or summary or "", limit=200)
        else:
            piece = scrub_public(item, limit=200)
        if piece and piece not in out:
            out.append(piece)
        if len(out) >= limit:
            break
    return out


def pick_confidence(*values: Any, default: float = 0.55) -> float:
    for v in values:
        if v is None:
            continue
        try:
            n = float(v)
        except Exception:
            continue
        if n > 1.0:
            n = n / 100.0
        return max(0.05, min(0.99, round(n, 4)))
    return default


def company_name(ctx: dict[str, Any]) -> str:
    for key in ("company_name", "name"):
        if ctx.get(key):
            return str(ctx[key])
    cid = ctx.get("company_dossier") or {}
    identity = cid.get("identity") if isinstance(cid, dict) else {}
    if isinstance(identity, dict) and identity.get("company_name"):
        return str(identity["company_name"])
    ca = ctx.get("company_analysis") or {}
    if isinstance(ca, dict):
        ca_identity = ca.get("identity") if isinstance(ca.get("identity"), dict) else {}
        if ca.get("company_name"):
            return str(ca["company_name"])
        if ca_identity.get("company_name"):
            return str(ca_identity["company_name"])
        if ca.get("ticker"):
            return str(ca["ticker"])
    return str(ctx.get("ticker") or "the company")


def ticker_of(ctx: dict[str, Any]) -> str | None:
    for src in (ctx, ctx.get("company_analysis") or {}, ctx.get("company_dossier") or {}, ctx.get("intelligence_layer") or {}):
        if isinstance(src, dict) and src.get("ticker"):
            return str(src["ticker"]).upper()
    return None


def opinion(
    *,
    role: str,
    question: str,
    headline: str,
    sections: dict[str, Any],
    evidence: list[str],
    confidence: float,
    score: float | None = None,
    word_limit: int = 500,
) -> dict[str, Any]:
    """Standard analyst opinion contract — public language only."""
    body_bits: list[str] = []
    clean_sections: dict[str, Any] = {}
    for k, v in sections.items():
        if isinstance(v, list):
            clean_sections[k] = as_list(v, limit=8)
            body_bits.extend(clean_sections[k])
        elif isinstance(v, dict):
            clean_sections[k] = {sk: scrub_public(sv, limit=180) for sk, sv in v.items() if sv not in (None, "", [])}
            body_bits.extend(str(x) for x in clean_sections[k].values())
        else:
            clean_sections[k] = scrub_public(v, limit=280)
            if clean_sections[k]:
                body_bits.append(clean_sections[k])

    narrative = scrub_public(headline, limit=280)
    words = " ".join([narrative, *body_bits]).split()
    if len(words) > word_limit:
        narrative = " ".join(words[: max(40, word_limit // 8)])

    return {
        "role": role,
        "analyst": _public_title(role),
        "question": question,
        "headline": narrative,
        "sections": clean_sections,
        "evidence": as_list(evidence, limit=10),
        "confidence": pick_confidence(confidence),
        "score": None if score is None else round(float(score), 2),
        "owner": role,
        "word_budget": word_limit,
    }


def _public_title(role: str) -> str:
    return {
        "business": "Business Analyst",
        "financial": "Financial Analyst",
        "valuation": "Valuation Analyst",
        "market": "Market Analyst",
        "sector": "Sector Analyst",
        "macro": "Macro Analyst",
        "risk": "Risk Analyst",
        "management": "Management Analyst",
        "ownership": "Ownership Analyst",
        "committee": "Investment Committee",
        "cio": "Chief Investment Officer",
    }.get(role, role.replace("_", " ").title())
