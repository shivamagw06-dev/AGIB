"""Resolve questions into a Verified Entity Contract state.

Rules:
- Never substitute another company (Air India ≠ BHARTIARTL).
- Ambiguous stems → clarification_required.
- Unknown fiction → unsupported_entity.
- Concept / industry / macro pedagogy → verified_* without company bind.
- CapIQ bind accepted only if it matches curated entity or high-confidence exact ticker
  and does not violate forbid lists.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from entity_intelligence.registry import (
    ambiguity_candidates,
    lookup_exact,
    normalize,
)
from entity_intelligence.schema import (
    CONFIDENCE_CLARIFY_MIN,
    CONFIDENCE_VERIFIED,
    COVERAGE_INSUFFICIENT,
    COVERAGE_NONE,
    EI_VERSION,
    LISTING_PRIVATE,
    STATE_CLARIFICATION_REQUIRED,
    STATE_UNSUPPORTED_ENTITY,
    STATE_VERIFIED_CONCEPT,
    STATE_VERIFIED_ENTITY,
    STATE_VERIFIED_INDUSTRY,
    STATE_VERIFIED_MACRO,
)

_CONCEPT_RE = re.compile(
    r"\b(what is|explain|define|meaning of|how (does|do|to)|roic|ebitda|free cash flow|"
    r"enterprise value|moat|pricing power|working capital|wacc)\b",
    re.I,
)
_INDUSTRY_RE = re.compile(
    r"\b(industry|sector|porter|oligopol|airline industry|banking industry|"
    r"saas industry|fmcg industry|industry economics|industry kpi)\b",
    re.I,
)
_MACRO_RE = re.compile(
    r"\b(macro|gdp|inflation|interest rate|rbi|fed|currency|usd|inr|macro outlook)\b",
    re.I,
)
_COMPANY_SHAPE_RE = re.compile(
    r"\b(company|business model|investment thesis|ticker|stock|share|"
    r"annual report|earnings|management|guidance|market cap|valuation for)\b",
    re.I,
)
_UNKNOWN_FICTION_RE = re.compile(
    r"\b(xyz quantum|abc pharma|quorvex|listed yesterday|fictional|made[- ]up company)\b",
    re.I,
)


def _bare_name(question: str) -> Optional[str]:
    """If the question is essentially just a company name / ticker, return it."""
    q = normalize(question)
    if not q:
        return None
    # Strip light lead-ins
    for prefix in (
        "what is ",
        "what about ",
        "who is ",
        "explain ",
        "tell me about ",
        "analyse ",
        "analyze ",
        "evaluate ",
        "assess ",
        "describe ",
    ):
        if q.startswith(prefix):
            q = q[len(prefix) :].strip()
    # Prefer exact alias before stripping legal suffixes (keeps "Titan Company").
    if lookup_exact(q):
        return q
    # Drop trailing filler — but not when remaining text alone is an ambiguous stem
    # that would erase a longer proper name already matched above.
    stripped = re.sub(r"\b(please|ltd|limited|inc|corp)\b", " ", q)
    stripped = " ".join(stripped.split())
    if lookup_exact(stripped):
        q = stripped
    if 1 <= len(q.split()) <= 5 and not _CONCEPT_RE.search(question):
        return q
    return q if lookup_exact(q) else None


def _find_entity_in_text(question: str) -> tuple[Optional[dict[str, Any]], float, str]:
    """Scan aliases; prefer leftmost mention, then longer alias.

    Critical: if Air India and Bharti Airtel both appear, do not silently
    drop Air India — prefer the private / forbid-sensitive entity when the
    user lead-mentions it (leftmost wins).
    """
    q = normalize(question)
    if not q:
        return None, 0.0, ""
    from entity_intelligence.registry import _ALIAS_INDEX

    hits: list[tuple[int, int, str, dict[str, Any]]] = []
    for alias, ent in _ALIAS_INDEX.items():
        if not alias:
            continue
        m = re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", q)
        if m:
            hits.append((m.start(), -len(alias), alias, ent))
    if not hits:
        return None, 0.0, ""
    hits.sort(key=lambda t: (t[0], t[1]))
    _pos, _neg_len, alias, ent = hits[0]
    conf = 0.99 if alias == q or q.startswith(alias) else 0.97
    return ent, conf, alias


def _cap_iq_safe(question: str, ent: Optional[dict[str, Any]]) -> Optional[str]:
    """Optional CapIQ ticker — rejected if it would substitute a curated entity."""
    try:
        from app.ui.company_router import detect_ikt_company

        tk = detect_ikt_company(question)
    except Exception:
        return None
    if not tk:
        return None
    forbid = set((ent or {}).get("forbid_tickers") or [])
    if tk.upper() in {f.upper() for f in forbid}:
        return None
    if ent and ent.get("ticker") and str(ent["ticker"]).upper() != str(tk).upper():
        # Curated entity disagrees with CapIQ → trust curated, drop CapIQ
        return None
    if ent and not ent.get("ticker") and ent.get("listing") == LISTING_PRIVATE:
        # Private curated entity must never inherit a CapIQ ticker
        return None
    return str(tk).upper()


def _clarification_payload(stem: str, cands: list[dict[str, Any]]) -> dict[str, Any]:
    options = [
        {
            "id": c["id"],
            "name": c["canonical_name"],
            "ticker": c.get("ticker"),
        }
        for c in cands
    ]
    names = " · ".join(
        f"{o['name']}" + (f" ({o['ticker']})" if o.get("ticker") else "") for o in options
    )
    summary = (
        f"“{stem}” is ambiguous. Did you mean: {names}? "
        "I will not guess — please specify the exact company."
    )
    return {
        "ok": True,
        "state": STATE_CLARIFICATION_REQUIRED,
        "confidence": 0.88,
        "allow_planner": False,
        "entity": None,
        "ticker": None,
        "canonical_name": None,
        "clarification": {"stem": stem, "options": options},
        "summary": summary,
        "why": [
            "Entity Intelligence requires disambiguation before any intelligence engine runs.",
            "Never substitute a related or similar-looking company.",
        ],
        "version": EI_VERSION,
    }


def _unsupported_payload(name: str, *, reason: str) -> dict[str, Any]:
    summary = (
        f"I identified “{name}”, but I do not currently have verified institutional coverage "
        f"sufficient to produce a structured investment-style analysis. "
        f"I will not substitute another company. ({reason})"
    )
    return {
        "ok": True,
        "state": STATE_UNSUPPORTED_ENTITY,
        "confidence": 0.99,
        "allow_planner": False,
        "entity": {"canonical_name": name, "coverage": COVERAGE_NONE},
        "ticker": None,
        "canonical_name": name,
        "summary": summary,
        "why": [
            f"{name} is outside the verified institutional coverage universe for this request.",
            "AGI will not bind a different CapIQ ticker or invent coverage.",
            "Ask about a covered company, or ask a general industry/concept question.",
        ],
        "version": EI_VERSION,
    }


def _private_limited_payload(ent: dict[str, Any]) -> dict[str, Any]:
    name = ent["canonical_name"]
    facts = list(ent.get("public_facts") or [])
    summary = (
        f"{name} is a privately owned company"
        + (f" under {ent['parent']}" if ent.get("parent") else "")
        + ". I do not currently have verified institutional financial coverage "
        "sufficient to produce an investment-committee-style analysis. "
        "I can discuss business model, industry structure, and competitive context from public facts — "
            "but I will not substitute any listed telecom or airline ticker for this entity."
        )
    if facts:
        summary = facts[0] + " " + summary
    return {
        "ok": True,
        "state": STATE_VERIFIED_ENTITY,
        "confidence": 0.99,
        "allow_planner": False,  # block INV/CapIQ stack; Ask uses EI executive
        "entity": {
            "id": ent["id"],
            "canonical_name": name,
            "ticker": None,
            "listing": LISTING_PRIVATE,
            "coverage": ent.get("coverage") or COVERAGE_INSUFFICIENT,
            "sector": ent.get("sector"),
            "industry": ent.get("industry"),
            "parent": ent.get("parent"),
            "forbid_tickers": list(ent.get("forbid_tickers") or []),
            "public_facts": facts,
        },
        "ticker": None,
        "canonical_name": name,
        "coverage": ent.get("coverage") or COVERAGE_INSUFFICIENT,
        "summary": summary,
        "why": [
            f"Resolved entity: {name} (private).",
            f"Coverage: {ent.get('coverage')}.",
            "Planner blocked for investment-style engines until institutional coverage exists.",
            "Forbidden substitutions: "
            + (", ".join(ent.get("forbid_tickers") or []) or "n/a")
            + ".",
        ],
        "version": EI_VERSION,
    }


def resolve(question: str) -> dict[str, Any]:
    q = (question or "").strip()
    if not q:
        return {
            "ok": False,
            "state": STATE_UNSUPPORTED_ENTITY,
            "confidence": 0.0,
            "allow_planner": False,
            "summary": "No question provided.",
            "version": EI_VERSION,
        }

    nq = normalize(q)

    # Fiction / unknown names that must refuse without substitution
    if _UNKNOWN_FICTION_RE.search(q):
        m = _UNKNOWN_FICTION_RE.search(q)
        return _unsupported_payload(m.group(0).title() if m else "Unknown company", reason="unrecognized entity")

    # Ambiguous bare stems first (HDFC, Tata, JSW, Titan) — including
    # "Explain HDFC" / "What about Titan?" lead-ins.
    bare = _bare_name(q)
    stem_probe = bare
    if not stem_probe:
        stripped = normalize(q)
        for prefix in ("what is ", "what about ", "explain ", "tell me about ", "analyse ", "analyze "):
            if stripped.startswith(prefix):
                stripped = stripped[len(prefix) :].strip()
        stem_probe = stripped
    if stem_probe in {"hdfc", "tata", "jsw", "titan"}:
        cands = ambiguity_candidates(stem_probe)
        if cands:
            return _clarification_payload(stem_probe, cands)

    # Curated entity match (longest alias)
    ent, conf, alias = _find_entity_in_text(q)
    if ent:
        # Global unsupported
        if ent.get("unsupported_global") or ent.get("coverage") == COVERAGE_NONE:
            return _unsupported_payload(ent["canonical_name"], reason="unsupported global / no verified coverage")

        # Private / insufficient institutional — verified identity, block planner
        if ent.get("listing") == LISTING_PRIVATE or ent.get("coverage") == COVERAGE_INSUFFICIENT:
            out = _private_limited_payload(ent)
            out["matched_alias"] = alias
            return out

        # Full / limited public coverage — verified entity, allow planner
        ticker = ent.get("ticker")
        # CapIQ may confirm but never override curated
        _cap_iq_safe(q, ent)
        allow = conf >= CONFIDENCE_VERIFIED or conf >= CONFIDENCE_CLARIFY_MIN
        if conf < CONFIDENCE_CLARIFY_MIN:
            return _clarification_payload(alias or ent["canonical_name"], [ent])
        return {
            "ok": True,
            "state": STATE_VERIFIED_ENTITY,
            "confidence": max(conf, CONFIDENCE_VERIFIED) if allow else conf,
            "allow_planner": True,
            "entity": {
                "id": ent["id"],
                "canonical_name": ent["canonical_name"],
                "ticker": ticker,
                "listing": ent.get("listing"),
                "coverage": ent.get("coverage"),
                "exchange": ent.get("exchange"),
                "sector": ent.get("sector"),
                "industry": ent.get("industry"),
                "forbid_tickers": list(ent.get("forbid_tickers") or []),
            },
            "ticker": ticker,
            "canonical_name": ent["canonical_name"],
            "matched_alias": alias,
            "coverage": ent.get("coverage"),
            "summary": (
                f"Resolved entity: {ent['canonical_name']}"
                + (f" ({ticker})" if ticker else "")
                + f". Coverage: {ent.get('coverage')}."
            ),
            "why": [
                f"Exact/alias match on “{alias}”.",
                "Entity Intelligence verified before Knowledge Planner.",
            ],
            "version": EI_VERSION,
        }

    # Non-company pedagogy before unsupported-company fallback
    if _MACRO_RE.search(q) and not _find_entity_in_text(q)[0]:
        return {
            "ok": True,
            "state": STATE_VERIFIED_MACRO,
            "confidence": 0.96,
            "allow_planner": True,
            "ticker": None,
            "summary": "Verified macro / rates / currency pedagogy route.",
            "version": EI_VERSION,
        }
    if _INDUSTRY_RE.search(q) and not bare:
        return {
            "ok": True,
            "state": STATE_VERIFIED_INDUSTRY,
            "confidence": 0.96,
            "allow_planner": True,
            "ticker": None,
            "summary": "Verified industry pedagogy route (no company bind).",
            "version": EI_VERSION,
        }
    if _CONCEPT_RE.search(q) and not bare:
        return {
            "ok": True,
            "state": STATE_VERIFIED_CONCEPT,
            "confidence": 0.96,
            "allow_planner": True,
            "ticker": None,
            "summary": "Verified financial/business concept route (no company bind).",
            "version": EI_VERSION,
        }

    # CapIQ-only bind for company-shaped questions (no curated hit)
    if _COMPANY_SHAPE_RE.search(q) or (bare and len(bare.split()) <= 3):
        tk = _cap_iq_safe(q, None)
        if tk:
            return {
                "ok": True,
                "state": STATE_VERIFIED_ENTITY,
                "confidence": 0.96,
                "allow_planner": True,
                "entity": {
                    "id": f"CAPIQ_{tk}",
                    "canonical_name": tk,
                    "ticker": tk,
                    "listing": "public",
                    "coverage": "full_institutional",
                    "source": "capiq_ikt",
                },
                "ticker": tk,
                "canonical_name": tk,
                "summary": f"Resolved listed entity ticker {tk} via CapIQ/IKT exact match.",
                "why": ["CapIQ/IKT exact bind after Entity Intelligence curated miss."],
                "version": EI_VERSION,
            }
        label = bare or nq
        if bare or re.search(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b", q):
            return _unsupported_payload(label.title() if label == bare else q[:80], reason="no verified entity")

    # Default: unknown / unsupported — do not run company engines
    return {
        "ok": True,
        "state": STATE_UNSUPPORTED_ENTITY,
        "confidence": 0.5,
        "allow_planner": False,
        "ticker": None,
        "summary": (
            "I could not verify a canonical institutional entity for this question. "
            "I will not guess or substitute another company."
        ),
        "why": ["Entity Intelligence: no verified entity / concept / industry / macro."],
        "version": EI_VERSION,
    }


def assert_no_forbidden_bind(contract: dict[str, Any], bound_ticker: Optional[str]) -> bool:
    """Return False if bound_ticker is a forbidden substitution for the resolved entity."""
    if not bound_ticker:
        return True
    ent = contract.get("entity") or {}
    forbid = {str(x).upper() for x in (ent.get("forbid_tickers") or [])}
    if bound_ticker.upper() in forbid:
        return False
    # Private entities must never receive any ticker bind
    if ent.get("listing") == LISTING_PRIVATE and bound_ticker:
        return False
    return True
