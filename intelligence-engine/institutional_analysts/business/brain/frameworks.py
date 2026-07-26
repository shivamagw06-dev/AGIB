"""Apply business strategy frameworks to existing evidence — no new data fetches."""

from __future__ import annotations

from typing import Any


def _txt(v: Any) -> str:
    return str(v or "").strip()


def _list(v: Any, *, limit: int = 6) -> list[str]:
    if v is None:
        return []
    if isinstance(v, str):
        return [v] if v.strip() else []
    out: list[str] = []
    for item in v:
        s = _txt(item)
        if s and s not in out:
            out.append(s)
        if len(out) >= limit:
            break
    return out


def apply_frameworks(evidence: dict[str, Any]) -> dict[str, Any]:
    """Map available business evidence onto institutional frameworks.

    Reads only already-assembled context (company analysis, dossier, academy, live evidence).
    Does not call providers or engines.
    """
    name = evidence.get("company") or "the company"
    model = _txt(evidence.get("business_model"))
    advantages = _list(evidence.get("advantages"), limit=5)
    drivers = _list(evidence.get("revenue_drivers"), limit=5)
    position = _txt(evidence.get("competitive_position"))
    pricing = _txt(evidence.get("pricing_power"))
    brand = _txt(evidence.get("brand"))
    capital = _txt(evidence.get("capital_allocation"))
    growth = _list(evidence.get("growth_opportunities"), limit=4)
    risks = _list(evidence.get("business_risks"), limit=5)
    score = evidence.get("business_quality_score")

    # Porter Five Forces — qualitative assessment from available signals
    rivalry = "Elevated" if any("compet" in r.lower() for r in risks + advantages) else "Moderate"
    threat_new = "Contained where scale and distribution matter" if any(
        w in " ".join(advantages).lower() for w in ("scale", "distribution", "network")
    ) else "Open"
    substitutes = "Present but franchise trust and switching costs may mute displacement"
    buyer_power = "Mixed — depends on product differentiation and switching costs"
    supplier_power = "Sector-dependent; watch concentrated input or funding dependencies"

    porter = {
        "framework": "Porter Five Forces",
        "rivalry": rivalry,
        "threat_of_new_entrants": threat_new,
        "threat_of_substitutes": substitutes,
        "buyer_power": buyer_power,
        "supplier_power": supplier_power,
        "implication": (
            f"Industry structure around {name} is investable when rivalry and substitution "
            "do not permanently erase returns on incremental capital."
        ),
    }

    # Moat dimensions
    moat_signals = []
    blob = " ".join([model, position, brand, pricing, " ".join(advantages)]).lower()
    if any(k in blob for k in ("scale", "distribution", "network")):
        moat_signals.append("Economies of scale / distribution reach")
    if any(k in blob for k in ("brand", "trust", "franchise")):
        moat_signals.append("Brand / trust franchise")
    if any(k in blob for k in ("switch", "retention", "sticky")):
        moat_signals.append("Switching costs / retention")
    if any(k in blob for k in ("pricing", "price power")):
        moat_signals.append("Pricing power")
    if not moat_signals:
        moat_signals = ["Franchise durability under review — evidence still assembling"]

    durability = "High" if len(moat_signals) >= 3 and (score is None or float(score or 0) >= 65) else (
        "Moderate" if len(moat_signals) >= 2 or (score is not None and float(score) >= 50) else "Low"
    )

    moat = {
        "framework": "Competitive Advantage / Moat",
        "sources": moat_signals[:5],
        "durability": durability,
        "replicability": (
            "Difficult to replicate quickly where scale, brand and distribution reinforce each other."
            if durability in {"High", "Moderate"}
            else "Advantage may be more easily contested without clearer evidence of structural barriers."
        ),
        "assessment": (
            f"Moat durability assessed as {durability.lower()} based on available franchise signals."
        ),
    }

    # Value creation / capital allocation lens
    value_chain = {
        "framework": "Value Chain / How it makes money",
        "business_model": model or f"{name} earns through its core franchise activities.",
        "revenue_drivers": drivers or ["Core demand", "Mix", "Scale efficiencies"],
        "customer_retention_hypothesis": (
            brand
            or "Customers stay when product trust, distribution convenience and switching frictions remain intact."
        ),
        "capital_allocation": capital
        or "Reinvestment versus owner returns must stay disciplined through the cycle.",
        "long_term_value_creation": growth[:3]
        or ["Share gains", "Adjacent products", "Operating leverage"],
    }

    # Capital cycle / competitive outlook
    outlook = {
        "framework": "Competitive Outlook",
        "industry_phase_hypothesis": "Mid-cycle competitive conditions unless evidence shows capacity glut or disruption.",
        "disruption_watch": risks[:2] or ["Technology / regulation", "Aggressive new capacity"],
        "improving": bool(score is not None and float(score) >= 65) or durability == "High",
        "why_improving_or_not": (
            "Franchise signals and advantage sources support durable value creation."
            if durability == "High"
            else "Franchise quality is adequate but advantage durability still needs clearer confirmation."
            if durability == "Moderate"
            else "Evidence of durable advantage remains thin — ownership case is not yet institutional-grade on quality alone."
        ),
    }

    applied = [
        porter["framework"],
        moat["framework"],
        value_chain["framework"],
        outlook["framework"],
    ]
    return {
        "applied": applied,
        "porter_five_forces": porter,
        "moat": moat,
        "value_creation": value_chain,
        "competitive_outlook": outlook,
        "knowledge_hits": [
            d
            for d in (
                "Economies of Scale",
                "Brand Strength",
                "Pricing Power",
                "Switching Costs",
                "Distribution",
                "Capital Allocation",
                "Competitive Positioning",
            )
            if d.split()[0].lower() in blob or d.lower() in blob or any(x.lower() in blob for x in d.lower().split())
        ][:8],
    }
