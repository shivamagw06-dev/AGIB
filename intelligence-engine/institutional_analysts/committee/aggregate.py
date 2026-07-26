"""Investment Committee — reads ONLY analyst opinions."""

from __future__ import annotations

from typing import Any

from institutional_analysts.base import as_list, pick_confidence, scrub_public


def aggregate(opinions: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Never consumes raw APIs / CID / statements — opinions only."""
    roles = ["business", "financial", "valuation", "market", "sector", "macro", "risk", "management", "ownership"]
    present = {r: opinions[r] for r in roles if isinstance(opinions.get(r), dict) and opinions[r].get("headline")}

    agreements: list[str] = []
    disagreements: list[str] = []
    missing: list[str] = []
    for r in roles:
        if r not in present:
            missing.append(f"{r.replace('_', ' ').title()} opinion incomplete")

    biz = present.get("business") or {}
    fin = present.get("financial") or {}
    val = present.get("valuation") or {}
    mkt = present.get("market") or {}
    risk = present.get("risk") or {}

    if biz.get("score") is not None and float(biz.get("score") or 0) >= 55:
        agreements.append("Business quality is adequate for continued institutional coverage.")
    if fin.get("headline"):
        agreements.append("Financial trajectory is part of the underwriting file.")
    if val.get("headline") and risk.get("headline"):
        disagreements.append("Valuation attractiveness and downside risks must be weighed together — not collapsed into one number.")
    if mkt.get("confidence", 0) < 0.55:
        disagreements.append("Market/tape confidence is lower than fundamental coverage confidence.")

    confs = [float(o.get("confidence") or 0.5) for o in present.values()]
    consensus_conf = pick_confidence(sum(confs) / len(confs) if confs else 0.55)

    readiness = "ready" if len(present) >= 7 and not missing[:1] else "partial"
    if len(missing) >= 3:
        readiness = "not_ready"

    summary = {
        "owner": "committee",
        "analyst": "Investment Committee",
        "question": "What is the coordinated institutional view?",
        "committee_summary": scrub_public(
            "Committee reviewed specialist opinions across business, financials, valuation, market, sector, macro, risk, management, and ownership.",
            limit=280,
        ),
        "consensus": {
            "business": scrub_public((biz.get("headline") or "Business opinion pending"), limit=220),
            "financial": scrub_public((fin.get("headline") or "Financial opinion pending"), limit=220),
            "valuation": scrub_public((val.get("headline") or "Valuation opinion pending"), limit=220),
            "market": scrub_public((mkt.get("headline") or "Market opinion pending"), limit=220),
            "macro": scrub_public(((present.get("macro") or {}).get("headline") or "Macro opinion pending"), limit=220),
            "sector": scrub_public(((present.get("sector") or {}).get("headline") or "Sector opinion pending"), limit=220),
            "risks": as_list((risk.get("sections") or {}).get("business_risks"), limit=5)
            or as_list(["Execution", "Earnings", "Multiple compression"], limit=5),
            "management": scrub_public(((present.get("management") or {}).get("headline") or "Management opinion pending"), limit=220),
            "ownership": scrub_public(((present.get("ownership") or {}).get("headline") or "Ownership opinion pending"), limit=220),
        },
        "agreements": agreements or ["Specialists cover distinct questions without repeating each other's mandate."],
        "disagreements": disagreements or ["No hard conflict — residual tension is valuation versus risk."],
        "conflicts": disagreements[:3],
        "missing_evidence": missing,
        "confidence": consensus_conf,
        "recommendation_readiness": readiness,
        "opinions_count": len(present),
        "analyst_roles_present": list(present.keys()),
    }
    return summary
