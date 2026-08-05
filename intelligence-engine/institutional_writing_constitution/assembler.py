"""Deterministic writing scaffold — six-section IRE hierarchy."""

from __future__ import annotations

from typing import Any

from institutional_writing_constitution.schema import (
    EVIDENCE_OBSERVATIONS_MAX,
    EVIDENCE_OBSERVATIONS_MIN,
    EXECUTIVE_SUMMARY_MAX_WORDS,
    QUESTIONS_MAX,
    QUESTIONS_MIN,
    RESPONSE_HIERARCHY,
    SECTION_LABELS,
)


def _word_count(text: str) -> int:
    return len((text or "").split())


def _truncate_words(text: str, max_words: int) -> str:
    words = (text or "").split()
    if len(words) <= max_words:
        return text.strip()
    return " ".join(words[:max_words]).strip() + "…"


def _supported_assertions(pack: dict[str, Any]) -> list[dict[str, Any]]:
    assertions = pack.get("institutional_assertions") or []
    if not assertions:
        sel = pack.get("ikr_selection") or {}
        assertions = sel.get("assertions") or []
    return [
        a for a in assertions
        if isinstance(a, dict) and str(a.get("status") or a.get("state")) in {"SUPPORTED", "PARTIAL", "ANSWERED"}
    ]


def _unknowns(pack: dict[str, Any]) -> list[str]:
    unknowns = pack.get("institutional_unknowns") or []
    out: list[str] = []
    for u in unknowns:
        if isinstance(u, dict):
            stmt = u.get("statement") or u.get("reason")
            if stmt:
                out.append(str(stmt))
        elif isinstance(u, str):
            out.append(u)
    return out[:5]


def _investment_meaning_bullets(pack: dict[str, Any], company: str) -> list[str]:
    """Explain why facts matter — not repeat them."""
    bullets: list[str] = []
    thesis = pack.get("investment_thesis") or {}
    if thesis.get("current_thesis"):
        bullets.append(
            f"The central investment debate on {company} centres on whether "
            f"{str(thesis.get('current_thesis')).lower().replace(company.lower(), 'the franchise')} "
            "continues to justify institutional attention."
        )
    quality = (pack.get("knowledge_quality") or {}).get("metrics") or {}
    if quality.get("evidence_coverage", 0) >= 50:
        bullets.append(
            "Current institutional evidence coverage supports a structured view, "
            "though gaps remain in areas that could shift the thesis."
        )
    else:
        bullets.append(
            "Material evidence gaps remain; investment meaning should be treated as "
            "directional until fuller institutional knowledge is compiled."
        )
    rc = pack.get("response_constitution") or {}
    if rc.get("direct_answer"):
        bullets.append(
            "The most immediate conclusion is that recent developments warrant "
            "interpretation through business quality and valuation, not headline reaction."
        )
    return bullets[:4]


def _evidence_observations(assertions: list[dict[str, Any]]) -> list[str]:
    observations: list[str] = []
    for a in assertions[:EVIDENCE_OBSERVATIONS_MAX]:
        stmt = str(a.get("statement") or "").strip()
        if not stmt:
            continue
        conf = a.get("confidence")
        prefix = "Evidence suggests"
        if conf is not None:
            observations.append(f"{prefix} {stmt.rstrip('.')}. (confidence: {conf}%)")
        else:
            observations.append(f"{prefix} {stmt.rstrip('.')}.")
    if not observations:
        placeholders = (
            "Evidence suggests institutional assertions are not yet compiled for this entity.",
            "Evidence suggests further validation is required before drawing firm conclusions.",
            "Evidence suggests monitoring should focus on thesis drivers once knowledge objects are populated.",
        )
        observations.extend(placeholders[:EVIDENCE_OBSERVATIONS_MIN])
    while len(observations) < EVIDENCE_OBSERVATIONS_MIN and assertions:
        observations.append("Evidence suggests further validation is required on remaining institutional claims.")
        break
    return observations[:EVIDENCE_OBSERVATIONS_MAX]


def _what_could_change_view(pack: dict[str, Any], company: str) -> list[str]:
    items: list[str] = []
    thesis = pack.get("investment_thesis") or {}
    for inv in (thesis.get("invalidation_conditions") or [])[:3]:
        items.append(str(inv))
    contradictions = (pack.get("institutional_knowledge_runtime") or {}).get("contradiction_count", 0)
    if contradictions:
        items.append(f"Resolution of {contradictions} contradicted assertion(s) would materially change the view.")
    items.extend([
        f"Operating margins deteriorate persistently at {company}.",
        "Competitive intensity increases without corresponding pricing power.",
        "Capital allocation weakens relative to historical standards.",
    ])
    return items[:5]


def _research_conclusion(pack: dict[str, Any], company: str) -> dict[str, Any]:
    supported = _supported_assertions(pack)
    unknowns = _unknowns(pack)
    return {
        "label": "Research Conclusion",
        "current_evidence_indicates": (
            f"Current evidence indicates {company} warrants continued institutional research "
            f"with {len(supported)} supported institutional assertion(s) and {len(unknowns)} open unknown(s)."
        ),
        "strongest_evidence_supports": (
            supported[0].get("statement") if supported else "Insufficient compiled assertions — compile Company DNA first."
        ),
        "largest_uncertainty_remains": unknowns[0] if unknowns else "Valuation versus growth expectations alignment.",
        "next_research_priority": (
            (pack.get("next_best_research_question") or {}).get("question")
            or (pack.get("institutional_review") or {}).get("what_research_should_be_updated", [None])[0]
            or f"Validate thesis drivers and monitoring triggers for {company}."
        ),
        "never_recommends": True,
        "user_decides": True,
    }


def _questions_before_you_decide(company: str, ticker: str | None) -> list[str]:
    label = ticker or company
    return [
        f"Is today's valuation on {label} already pricing in expected growth?",
        "What evidence would invalidate today's thesis?",
        f"How does {label} compare with the best alternative investment?",
        f"Would this still be an attractive business after one disappointing quarter?",
        "Does the risk/reward fit portfolio concentration limits?",
    ][:QUESTIONS_MAX]


def assemble_writing_sections(pack: dict[str, Any], *, company: str, ticker: str | None = None) -> dict[str, Any]:
    """Build six-section writing hierarchy from knowledge + constitution packs."""
    rc = pack.get("response_constitution") or {}
    assertions = _supported_assertions(pack)

    exec_src = (
        rc.get("direct_answer")
        or pack.get("executive")
        or pack.get("summary")
        or f"{company} — institutional research summary pending fuller evidence compilation."
    )
    executive = _truncate_words(str(exec_src), EXECUTIVE_SUMMARY_MAX_WORDS)

    sections: dict[str, Any] = {
        "executive_summary": {
            "label": SECTION_LABELS["executive_summary"],
            "text": executive,
            "word_count": _word_count(executive),
            "max_words": EXECUTIVE_SUMMARY_MAX_WORDS,
        },
        "investment_meaning": {
            "label": SECTION_LABELS["investment_meaning"],
            "bullets": _investment_meaning_bullets(pack, company),
            "guidance": "Explain why an investor should care — never repeat raw facts.",
        },
        "what_evidence_suggests": {
            "label": SECTION_LABELS["what_evidence_suggests"],
            "observations": _evidence_observations(assertions),
            "min_observations": EVIDENCE_OBSERVATIONS_MIN,
            "assertion_backed": bool(assertions),
        },
        "what_could_change_view": {
            "label": SECTION_LABELS["what_could_change_view"],
            "invalidation_scenarios": _what_could_change_view(pack, company),
        },
        "research_conclusion": _research_conclusion(pack, company),
        "questions_before_you_decide": {
            "label": SECTION_LABELS["questions_before_you_decide"],
            "questions": _questions_before_you_decide(company, ticker)[:QUESTIONS_MAX],
            "min_questions": QUESTIONS_MIN,
        },
    }
    return {k: sections[k] for k in RESPONSE_HIERARCHY}


def infer_answer_length(query: str) -> str:
    q = (query or "").lower()
    if any(w in q for w in ("deep dive", "comprehensive", "full research", "detailed")):
        return "deep_research"
    if any(w in q for w in ("compare", "explain", "analyze", "analyse", "should i", "thesis")):
        return "research_request"
    return "simple_question"
