"""Chief Investment Officer — reads ONLY the committee summary."""

from __future__ import annotations

from typing import Any

from institutional_analysts.base import as_list, pick_confidence, scrub_public


def write_report(committee: dict[str, Any], *, query: str = "", company: str = "") -> dict[str, Any]:
    """CIO never consumes raw provider data — committee only."""
    consensus = committee.get("consensus") if isinstance(committee.get("consensus"), dict) else {}
    name = company or "the company"
    conf = pick_confidence(committee.get("confidence"), default=0.55)

    business = consensus.get("business") or ""
    financial = consensus.get("financial") or ""
    valuation = consensus.get("valuation") or ""
    macro = consensus.get("macro") or ""
    risks = as_list(consensus.get("risks"), limit=5)

    exec_summary = scrub_public(
        f"{name}: institutional view balances business quality, financial trajectory, valuation, and risk. "
        f"{business} {financial} {valuation}".strip(),
        limit=420,
    )
    thesis = scrub_public(
        f"Own {name} as a franchise only if business durability and financial quality justify today's valuation after macro transmission. "
        f"{macro}".strip(),
        limit=360,
    )

    bull = [
        scrub_public("Franchise execution improves and returns expand while valuation stays reasonable.", limit=180),
        scrub_public(business, limit=180) if business else "Business quality supports upside optionality.",
    ]
    base = [
        scrub_public("Mid-cycle delivery with stable returns; valuation tracks fundamentals.", limit=180),
        scrub_public(financial, limit=180) if financial else "Financials evolve in line with sector norms.",
    ]
    bear = [
        scrub_public("Growth/margins disappoint or risk events force multiple compression.", limit=180),
        *risks[:2],
    ]

    catalysts = [
        "Next earnings print and management commentary",
        "Evidence of durable returns / asset quality",
        "Clearer valuation margin of safety",
    ]
    conclusion = scrub_public(
        f"Committee readiness: {committee.get('recommendation_readiness') or 'partial'}. "
        f"Conclusion remains an institutional assessment — not an automatic trade instruction. "
        f"Agreements: {'; '.join(as_list(committee.get('agreements'), limit=2))}",
        limit=360,
    )

    return {
        "owner": "cio",
        "analyst": "Chief Investment Officer",
        "query": query,
        "company": name,
        "executive_summary": exec_summary,
        "investment_thesis": thesis,
        "bull_case": [x for x in bull if x][:4],
        "base_case": [x for x in base if x][:4],
        "bear_case": [x for x in bear if x][:4],
        "key_risks": risks[:6] or ["Execution", "Earnings miss", "Multiple compression"],
        "key_catalysts": catalysts,
        "institutional_conclusion": conclusion,
        "confidence": conf,
        "recommendation_readiness": committee.get("recommendation_readiness"),
        "why": [
            scrub_public(business, limit=200),
            scrub_public(financial, limit=200),
            scrub_public(valuation, limit=200),
            scrub_public(macro, limit=200),
        ],
    }
