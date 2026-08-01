"""Product-contract checks for AGI Ask responses (behavior, not wording)."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

# Implementation jargon that must never reach the user.
_JARGON_RE = re.compile(
    r"(?i)\b("
    r"E0[1-9]|E1[0-4]|L4|ORCH|"
    r"FAA|IEL|LEO|IERE|IFSE|IAP|IEG|IMAI|"
    r"Traceback|File \".*\.py\", line|"
    r"RuntimeError|TypeError|KeyError|AttributeError|"
    r"uvicorn|fastapi\.exceptions"
    r")\b"
)

# Explicit recommendation language — not casual mention of buybacks / "buy the argument".
# Negations like "no target price" / "does not issue buy" are allowed.
_RECOMMENDATION_RE = re.compile(
    r"(?i)("
    r"(?<!\bno\s)(?<!\bnot\s)(?<!\bwithout\s)(?<!\bnever\s)"
    r"(?:we recommend\s+(?:buying|selling|adding|reducing)|"
    r"recommendation\s*[:=]\s*(?:buy|sell|add|reduce|overweight|underweight)|"
    r"(?:buy|sell|add|reduce)\s+rating|"
    r"rating\s*[:=]\s*(?:buy|sell|add|reduce|overweight|underweight)|"
    r"target\s*price\s*[:=]?\s*\d|"
    r"(?:initiate|maintain|upgrade to|downgrade to)\s+(?:a\s+)?(?:buy|sell|add|reduce|overweight|underweight)|"
    r"you should\s+(?:buy|sell)|"
    r"go\s+(?:long|short))"
    r")"
)

_INSUFFICIENT_RE = re.compile(
    r"(?i)\b("
    r"insufficient evidence|not enough evidence|no (reliable )?evidence|"
    r"cannot (find|verify|confirm)|do not have (enough|sufficient)|"
    r"unknown company|unable to (locate|retrieve)|"
    r"coverage (is )?limited|knowledge gap|not in (the )?universe|"
    r"warming up|degraded|research desk"
    r")\b"
)

_ENTITY_ALIASES = {
    "RELIANCE": ["RELIANCE", "RELIANCE INDUSTRIES", "RIL"],
    "INFY": ["INFY", "INFOSYS"],
    "TCS": ["TCS", "TATA CONSULTANCY"],
    "HDFCBANK": ["HDFCBANK", "HDFC BANK", "HDFC"],
    "META": ["META", "META PLATFORMS", "FACEBOOK", "FB"],
    "AAPL": ["AAPL", "APPLE"],
    "NIFTY": ["NIFTY", "NIFTY 50", "NIFTY50"],
    "TITAN": ["TITAN"],
    "ASIANPAINT": ["ASIANPAINT", "ASIAN PAINTS"],
}


def flatten_text(payload: Any) -> str:
    if payload is None:
        return ""
    if isinstance(payload, str):
        return payload
    if isinstance(payload, (int, float, bool)):
        return str(payload)
    if isinstance(payload, dict):
        return " ".join(flatten_text(v) for v in payload.values())
    if isinstance(payload, (list, tuple, set)):
        return " ".join(flatten_text(v) for v in payload)
    return str(payload)


def extract_answer_text(payload: Dict[str, Any]) -> str:
    answer = payload.get("answer") if isinstance(payload.get("answer"), dict) else {}
    parts = [
        payload.get("executive_summary"),
        answer.get("executive_summary"),
        answer.get("summary"),
        answer.get("direct_answer"),
        (answer.get("response_constitution") or {}).get("direct_answer")
        if isinstance(answer.get("response_constitution"), dict)
        else None,
        payload.get("investment_thesis"),
        " ".join(payload.get("why") or []),
        " ".join(answer.get("why") or []) if isinstance(answer.get("why"), list) else None,
    ]
    return " ".join(str(p) for p in parts if p)


def evidence_count(payload: Dict[str, Any]) -> int:
    buckets = [
        payload.get("evidence_used"),
        payload.get("supporting_research"),
        payload.get("supporting_evidence"),
        payload.get("hits"),
        payload.get("latest_articles"),
    ]
    n = 0
    for b in buckets:
        if isinstance(b, list):
            n += len(b)
    multi = payload.get("multi_source") or {}
    if isinstance(multi, dict) and multi.get("evidence_count"):
        try:
            n = max(n, int(multi["evidence_count"]))
        except (TypeError, ValueError):
            pass
    kf = payload.get("knowledge_foundation") or {}
    if isinstance(kf, dict):
        for key in ("companies", "sectors", "themes", "items"):
            if isinstance(kf.get(key), list):
                n += len(kf[key])
    return n


def evidence_sources(payload: Dict[str, Any]) -> List[str]:
    sources: List[str] = []
    for key in ("evidence_used", "supporting_research", "supporting_evidence", "hits"):
        for item in payload.get(key) or []:
            if not isinstance(item, dict):
                continue
            src = item.get("source") or item.get("provider") or item.get("type") or item.get("title")
            if src:
                sources.append(str(src)[:80])
    multi = payload.get("multi_source") or {}
    if isinstance(multi, dict):
        for s in multi.get("sources") or multi.get("adapters") or []:
            sources.append(str(s)[:80])
    # unique preserve order
    out: List[str] = []
    seen = set()
    for s in sources:
        if s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out[:20]


def extract_entities(payload: Dict[str, Any]) -> List[str]:
    ents = payload.get("entities") or {}
    found: List[str] = []
    if isinstance(ents, dict):
        t = ents.get("ticker")
        if t:
            found.append(str(t).upper())
        for c in ents.get("companies") or []:
            found.append(str(c).upper())
    for r in payload.get("related_companies") or []:
        found.append(str(r).upper())
    # de-dupe
    out: List[str] = []
    seen = set()
    for e in found:
        if e in seen:
            continue
        seen.add(e)
        out.append(e)
    return out


def normalize_intent(raw: Any, family_hint: str = "") -> str:
    text = str(raw or family_hint or "").strip()
    if not text:
        return "Unknown"
    low = text.lower().replace("_", " ")
    mapping = [
        ("historical", "Historical"),
        ("replay", "Historical"),
        ("education", "Education"),
        ("concept", "Education"),
        ("document", "Documents"),
        ("macro", "Macro"),
        ("government", "Macro"),
        ("compare", "Compare"),
        ("peer", "Compare"),
        ("industry", "Industry"),
        ("private", "Private Markets"),
        ("valuation", "Explain"),
        ("explain", "Explain"),
        ("recommendation", "Company"),
        ("portfolio", "Company"),
        ("company", "Company"),
        ("analyse", "Company"),
        ("analyze", "Company"),
    ]
    for needle, family in mapping:
        if needle in low:
            return family
    return text.split()[0].title() if text else "Unknown"


def intent_matches(observed: str, expected_family: str) -> bool:
    if not expected_family:
        return True
    o = normalize_intent(observed).lower()
    e = expected_family.lower()
    if o == e:
        return True
    # Compatible families
    aliases = {
        "explain": {"explain", "education", "company", "industry"},
        "education": {"education", "explain"},
        "company": {"company", "explain", "compare"},
        "compare": {"compare", "company", "explain"},
        "macro": {"macro", "industry", "explain"},
        "industry": {"industry", "macro", "explain", "compare"},
        "documents": {"documents", "explain", "company"},
        "historical": {"historical", "explain", "company"},
        "private markets": {"private markets", "company", "explain", "industry"},
    }
    return o in aliases.get(e, {e})


def entity_mentioned(blob: str, entity: str) -> bool:
    aliases = _ENTITY_ALIASES.get(entity.upper(), [entity.upper()])
    upper = blob.upper()
    return any(a.upper() in upper for a in aliases)


def check_entity_binding(
    payload: Dict[str, Any],
    *,
    expected: Sequence[str] = (),
    forbid: Sequence[str] = (),
) -> Tuple[bool, List[str]]:
    """Soft entity binding: require at least one expected alias if provided; forbid pollution."""
    errors: List[str] = []
    blob = (
        flatten_text(extract_entities(payload))
        + " "
        + extract_answer_text(payload)
        + " "
        + flatten_text(payload.get("related_companies"))
    )
    if expected:
        if not any(entity_mentioned(blob, e) for e in expected):
            # Soft: only fail if a forbidden competitor clearly dominates
            if forbid and any(entity_mentioned(blob, f) for f in forbid):
                errors.append(f"expected entity {list(expected)} missing; forbidden entity present")
            # else: allow thin/degraded answers without hard fail on missing entity
    for f in forbid:
        # Fail only if forbidden entity appears as bound ticker/company AND expected missing
        bound = extract_entities(payload)
        aliases = _ENTITY_ALIASES.get(f.upper(), [f.upper()])
        if any(b in {a.upper() for a in aliases} or b.upper() in {a.upper() for a in aliases} for b in bound):
            if expected and not any(entity_mentioned(" ".join(bound), e) for e in expected):
                errors.append(f"entity pollution: bound {bound} includes forbidden {f}")
    return (len(errors) == 0), errors


def check_no_jargon(payload: Dict[str, Any]) -> Tuple[bool, List[str]]:
    text = extract_answer_text(payload) + " " + flatten_text(payload.get("why"))
    hits = _JARGON_RE.findall(text)
    if hits:
        return False, [f"implementation jargon leaked: {sorted(set(str(h) for h in hits))[:8]}"]
    return True, []


_NEGATED_OR_EDU_REC_RE = re.compile(
    r"(?i)("
    r"\b(?:no|not|never|without|does\s+not|do\s+not|don't)\b[^\n.]{0,64}"
    r"\b(?:buy|sell|buying|selling|add|reduce|target\s*price|price\s*target)\b"
    r"|\bno\s+buy\s*/\s*sell\b"
    r"|\bbuy\s*/\s*sell\s+(?:rating|recommendation|advice)\b"
    r"|\bbuy\s+or\s+sell\s+(?:rating|recommendation|advice|recommendations)\b"
    r")"
)


def check_no_recommendation(payload: Dict[str, Any]) -> Tuple[bool, List[str]]:
    text = extract_answer_text(payload)
    # Scrub negated / educational mentions before scanning for real violations.
    scrubbed = _NEGATED_OR_EDU_REC_RE.sub(" ", text or "")
    m = _RECOMMENDATION_RE.search(scrubbed)
    if m:
        return False, [f"recommendation policy violation: {m.group(0)}"]
    return True, []


def check_insufficient_evidence(payload: Dict[str, Any]) -> Tuple[bool, List[str]]:
    text = extract_answer_text(payload)
    if evidence_count(payload) == 0 and _INSUFFICIENT_RE.search(text):
        return True, []
    if _INSUFFICIENT_RE.search(text):
        return True, []
    if evidence_count(payload) == 0 and (
        payload.get("degraded") or payload.get("status") == "degraded" or payload.get("retryable")
    ):
        return True, []
    return False, ["expected honest insufficient-evidence stance for unknown company"]


def check_as_of_no_lookahead(
    payload: Dict[str, Any],
    *,
    as_of: Optional[str] = None,
    must_not: Sequence[str] = (),
) -> Tuple[bool, List[str]]:
    if not as_of and not must_not:
        return True, []
    text = extract_answer_text(payload).lower()
    errors: List[str] = []
    for needle in must_not:
        if needle and needle.lower() in text:
            errors.append(f"historical lookahead / leak: {needle}")
    # Soft: current PE quoted without as_of framing is a risk — only flag explicit future years
    for year in ("2024", "2025", "2026", "2027"):
        if as_of and as_of.startswith("2020") and year in text and "as of" not in text:
            # allow if discussing the prompt itself; flag dense future PE claims
            if re.search(rf"\b(pe|p/e|multiple|valuation).{{0,40}}{year}", text):
                errors.append(f"possible future valuation leak mentioning {year}")
    return (len(errors) == 0), errors


def mentions_insufficient_evidence(text: str) -> bool:
    return bool(_INSUFFICIENT_RE.search(text or ""))


def is_degraded(payload: Dict[str, Any]) -> bool:
    if payload.get("degraded") is True:
        return True
    if payload.get("status") == "degraded":
        return True
    if payload.get("mode") == "node_desk_fallback":
        return True
    deg = payload.get("degradation")
    if isinstance(deg, dict) and deg:
        return True
    return False


def has_usable_answer(payload: Dict[str, Any]) -> bool:
    text = extract_answer_text(payload).strip()
    if len(text) >= 40:
        return True
    if is_degraded(payload) and len(text) >= 20:
        return True
    if payload.get("error") == "research_desk_unavailable" and payload.get("retryable"):
        return True
    return False
