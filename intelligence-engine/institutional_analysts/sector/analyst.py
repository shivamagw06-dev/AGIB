"""Sector Analyst — Is the industry attractive?"""

from __future__ import annotations

from typing import Any

from institutional_analysts.base import as_list, company_name, opinion, pick_confidence, scrub_public


def analyse(ctx: dict[str, Any]) -> dict[str, Any]:
    sector = ctx.get("sector_intelligence") if isinstance(ctx.get("sector_intelligence"), dict) else {}
    academy = ctx.get("finance_academy") if isinstance(ctx.get("finance_academy"), dict) else {}
    kf = ctx.get("knowledge_foundation") if isinstance(ctx.get("knowledge_foundation"), dict) else {}
    sif = sector.get("sif") if isinstance(sector.get("sif"), dict) else sector
    name = company_name(ctx)
    sector_id = scrub_public(sector.get("sector_id") or sif.get("sector_id") or "sector", limit=40)

    evidence = []
    evidence.extend(as_list(sif.get("priority_metrics") or sector.get("priority_metrics"), limit=4))
    evidence.extend(as_list(academy.get("courses") or academy.get("concepts"), limit=3))
    evidence.extend(as_list(kf.get("hits") or kf.get("themes"), limit=2))

    return opinion(
        role="sector",
        question="Is the industry attractive?",
        headline=f"{name} sits in {sector_id}: industry structure and KPIs set the opportunity set.",
        sections={
            "industry_structure": sif.get("structure") or sector.get("structure") or f"{sector_id} competitive structure shapes returns",
            "competition": sif.get("competition") or sector.get("peers") or "Intensity of rivalry and substitutes matter for margins",
            "sector_growth": sif.get("growth") or sector.get("growth") or "Mid-cycle growth assumptions should be evidence-led",
            "sector_kpis": sif.get("priority_metrics") or sector.get("priority_metrics") or ["Growth", "Margins", "Returns", "Asset quality"],
            "demand": sif.get("demand") or "Demand linked to cycle, policy, and consumer/enterprise spend",
            "supply": sif.get("supply") or "Supply/capacity and competitive entry affect pricing",
            "technology": sif.get("technology") or "Technology shifts can reset cost curves and distribution",
            "regulation": sif.get("regulation") or "Regulatory stance is a first-order sector variable",
            "leading_companies": sif.get("leaders") or sector.get("leaders") or ["Peer leaders define the quality bar"],
        },
        evidence=evidence or [f"Sector framing for {sector_id}"],
        confidence=pick_confidence((sector.get("detection") or {}).get("confidence"), sif.get("confidence"), default=0.6),
        word_limit=450,
    )
