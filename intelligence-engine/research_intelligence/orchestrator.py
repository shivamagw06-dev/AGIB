"""Phase 3.4 Research Intelligence orchestrator — executive research note order."""

from __future__ import annotations

import re
from typing import Any, Optional

from investment_intelligence.policy import assert_no_recommendation, strip_recommendation_language

from research_intelligence import engines
from research_intelligence.corpus import get_corpus, list_entities, resolve_entity
from research_intelligence.schema import (
    ASK_WIRED,
    RI_VERSION,
    RECOMMENDATION_POLICY,
    ResearchPackage,
)


def detect_intents(question: str) -> list[str]:
    q = (question or "").lower()
    intents: list[str] = []
    # Knowledge evolution before generic "evolution" deep-research matches
    if re.search(r"\b(knowledge evolution|updates knowledge|learning becomes|long-lived|from research to)\b", q):
        intents.append("knowledge_evolution")
    if re.search(
        r"\b(deep research|five years|5 years|10 years|fy2022|fy2026|"
        r"management evolution|industry evolution|competitive evolution|risk evolution|"
        r"consistently emphasized|recurring themes?)\b",
        q,
    ):
        intents.append("deep_research")
    if re.search(r"\b(annual report|fy20|business model|segments?|governance|financial changes)\b", q):
        intents.append("annual_report")
    if re.search(r"\b(transcript|earnings call|conference call|management commentary|analyst questions?|pricing commentary)\b", q):
        intents.append("transcript")
    if re.search(r"\b(management|ceo|cfo|chairman|leadership|communication|execution|philosophy)\b", q):
        intents.append("management")
    if re.search(r"\b(guidance|vs consensus|vs actual|vs previous|revenue guidance|margin guidance|capex guidance)\b", q):
        intents.append("guidance")
    if re.search(r"\b(estimate|consensus|revision|expectation gap|ebitda|eps)\b", q):
        intents.append("estimates")
    if re.search(r"\b(event|acquisition|divestiture|buyback|dividend|capital raise|debt issue|litigation|product launch|regulatory action|factory)\b", q):
        intents.append("events")
    if re.search(r"\b(research memory|remember|company history|never duplicate|conclusions)\b", q):
        intents.append("memory")
    if re.search(r"\b(cross-?document|document linkage|investor presentation|press release|filings?|one timeline)\b", q):
        intents.append("cross_document")
    if re.search(r"\b(timeline|chronolog|ipo|major risks|important decisions|history of)\b", q):
        intents.append("timeline")
    if re.search(r"\b(research quality|freshness|coverage|contradiction|completeness|missing information)\b", q):
        intents.append("quality")
    if re.search(r"\b(capital allocat\w*)\b", q):
        intents.append("deep_research")
        intents.append("annual_report")
    if re.search(r"\b(research object|workspace|canonical research)\b", q):
        intents.append("research_object")
    if re.search(r"\b(monitor|monitoring)\b", q):
        intents.append("monitoring")
    if not intents:
        intents.append("overview")
    seen: set[str] = set()
    out: list[str] = []
    for i in intents:
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out


def analyse(question: str, *, entity: Optional[str] = None) -> dict[str, Any]:
    intents = detect_intents(question)
    key = entity or resolve_entity(question)
    pkg = ResearchPackage(ok=False, question=question, recommendation_policy=RECOMMENDATION_POLICY)

    if not key:
        pkg.executive_summary = (
            "Research Intelligence needs a supported company "
            "(Reliance, TCS, Infosys, HDFC Bank, Asian Paints). "
            "Ask about annual reports, transcripts, guidance, management, events, "
            "timeline, deep research, or research memory. No BUY/SELL recommendations are issued."
        )
        pkg.summary = pkg.executive_summary
        pkg.unknowns = ["Entity not resolved"]
        pkg.confidence = 0.25
        return pkg.to_dict()

    c = get_corpus(key)
    assert c is not None
    pkg.entity = key
    pkg.company = c["name"]
    modules: list[str] = []

    # Always attach workspace object + quality + memory scaffolding
    robj = engines.research_object(c)
    pkg.research_object = robj["research_object"]
    modules.append("research_object")

    ar = engines.annual_report_intelligence(c)
    pkg.annual_report = ar
    modules.append("annual_report")

    tx = engines.transcript_intelligence(c)
    pkg.transcript = tx
    modules.append("transcript")

    mg = engines.management_intelligence(c)
    pkg.management = mg
    modules.append("management")

    gd = engines.guidance_intelligence(c)
    pkg.guidance = gd
    modules.append("guidance")

    est = engines.estimate_intelligence(c)
    pkg.estimates = est
    modules.append("estimates")

    ev = engines.event_intelligence(c)
    pkg.events = ev
    modules.append("events")

    mem = engines.research_memory(c)
    pkg.memory = mem
    modules.append("memory")

    xd = engines.cross_document(c)
    pkg.cross_document = xd
    modules.append("cross_document")

    tl = engines.timeline_engine(c)
    pkg.timeline = tl
    modules.append("timeline")

    ql = engines.quality_engine(c)
    pkg.quality = ql
    modules.append("quality")

    ke = engines.knowledge_evolution(c)
    pkg.knowledge_evolution = ke
    modules.append("knowledge_evolution")

    dr = engines.deep_research(c)
    pkg.deep_research = dr
    modules.append("deep_research")

    brief = engines.executive_brief_bits(c)
    pkg.whats_new = list(brief["whats_new"])
    pkg.business_impact = brief["business_impact"]
    pkg.financial_impact = brief["financial_impact"]
    pkg.industry_impact = brief["industry_impact"]
    pkg.investment_implications = brief["investment_implications"]
    pkg.unknowns = list(c.get("unknowns") or [])[:8]
    pkg.monitoring_points = list(c.get("monitoring") or [])[:8]
    pkg.evidence = {
        "sources": c.get("documents") or [],
        "strength": (ql.get("dimensions") or {}).get("research_completeness"),
        "summary": f"Evidence for {c['name']} is structured from Research Memory corpus documents and extracts.",
    }

    intent_map = {
        "deep_research": dr["summary"],
        "annual_report": ar["summary"],
        "transcript": tx["summary"],
        "management": mg["summary"],
        "guidance": gd["summary"],
        "estimates": est["summary"],
        "events": ev["summary"],
        "memory": mem["summary"],
        "cross_document": xd["summary"],
        "timeline": tl["summary"],
        "quality": ql["summary"],
        "knowledge_evolution": ke["summary"],
        "research_object": robj["summary"],
        "monitoring": strip_recommendation_language(
            f"Monitoring points for {c['name']}: " + "; ".join(pkg.monitoring_points)
            + ". Track business/financial/industry changes via Research Memory updates. Observations only."
        ),
        "overview": strip_recommendation_language(
            f"Executive research note for {c['name']}: {'; '.join((c.get('memory') or {}).get('conclusions') or [])}. "
            f"What's new — {'; '.join(pkg.whats_new[:2])}. "
            f"Recurring themes — {', '.join(((c.get('memory') or {}).get('recurring_themes') or [])[:5])}. "
            f"Research is structured institutional memory, not document summarization. No BUY/SELL."
        ),
    }
    primary = intents[0]
    summary = intent_map.get(primary) or intent_map["overview"]

    pkg.executive_summary = strip_recommendation_language(summary)[:1400]
    pkg.summary = pkg.executive_summary
    pkg.modules_used = []
    seen: set[str] = set()
    for m in modules:
        if m not in seen:
            seen.add(m)
            pkg.modules_used.append(m)
    if "monitoring" in intents and "monitoring" not in pkg.modules_used:
        pkg.modules_used.append("monitoring")
    pkg.ok = bool(pkg.executive_summary)
    pkg.confidence = float((ql.get("dimensions") or {}).get("confidence") or 0.85)
    pkg.fabricated = False
    pkg.recommendation = None
    pkg.recommendation_policy = RECOMMENDATION_POLICY
    pkg.ask_wired = ASK_WIRED

    out = pkg.to_dict()
    out["executive_summary"] = strip_recommendation_language(out.get("executive_summary") or "")
    out["summary"] = out["executive_summary"]
    out["recommendation"] = None
    out["recommendation_policy"] = RECOMMENDATION_POLICY
    out["ask_wired"] = ASK_WIRED
    out["version"] = RI_VERSION
    out["available_entities"] = list_entities()
    out["executive_note_order"] = [
        "executive_summary",
        "whats_new",
        "business_impact",
        "financial_impact",
        "industry_impact",
        "investment_implications",
        "evidence",
        "unknowns",
        "monitoring_points",
    ]
    if not assert_no_recommendation(out):
        out["executive_summary"] = strip_recommendation_language(
            (out.get("executive_summary") or "")
            + " Observations only under recommendation policy (no buy / no sell)."
        )
        out["summary"] = out["executive_summary"]
    return out
