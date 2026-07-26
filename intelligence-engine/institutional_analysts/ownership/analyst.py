"""Ownership Analyst — Who owns this business?"""

from __future__ import annotations

from typing import Any

from institutional_analysts.base import as_list, company_name, opinion, pick_confidence, scrub_public


def analyse(ctx: dict[str, Any]) -> dict[str, Any]:
    cid = ctx.get("company_dossier") if isinstance(ctx.get("company_dossier"), dict) else {}
    leo = ctx.get("live_evidence") if isinstance(ctx.get("live_evidence"), dict) else {}
    yfp = ctx.get("yahoo_enrichment") if isinstance(ctx.get("yahoo_enrichment"), dict) else {}
    share = (
        cid.get("shareholding")
        if isinstance(cid.get("shareholding"), dict)
        else cid.get("ownership")
        if isinstance(cid.get("ownership"), dict)
        else yfp.get("ownership")
        if isinstance(yfp.get("ownership"), dict)
        else {}
    )
    name = company_name(ctx)

    announcements = as_list(leo.get("announcements_used"), limit=6)
    evidence = [a for a in announcements if "share" in a.lower() or "holding" in a.lower()]
    evidence = evidence or announcements[:3] or [f"Shareholding disclosures for {name}"]

    return opinion(
        role="ownership",
        question="Who owns this business?",
        headline=f"{name}: ownership structure and trends signal alignment and free-float dynamics.",
        sections={
            "promoters": scrub_public(share.get("promoters") or share.get("promoter") or "Promoter holding under disclosure", limit=160),
            "institutions": scrub_public(share.get("institutions") or share.get("institutional") or "Institutional ownership present in large-cap names", limit=160),
            "mutual_funds": scrub_public(share.get("mutual_funds") or share.get("mf") or "Domestic mutual-fund participation", limit=120),
            "fiis": scrub_public(share.get("fiis") or share.get("fii") or "Foreign institutional ownership", limit=120),
            "diis": scrub_public(share.get("diis") or share.get("dii") or "Domestic institutional ownership", limit=120),
            "insiders": scrub_public(share.get("insiders") or "Insider activity monitored around windows", limit=120),
            "ownership_trend": scrub_public(share.get("trend") or share.get("ownership_trend") or "Track sequential changes in promoter and institutional stakes", limit=200),
        },
        evidence=evidence,
        confidence=pick_confidence(share.get("confidence"), default=0.5),
        word_limit=350,
    )
