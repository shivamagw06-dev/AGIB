"""Build a seamless institutional research brief from canonical AGI packages.

Consumes CID / Company Analysis / Monitor / KF / Academy / LEO / DVC / ECP / IRP.
Never mentions providers. Interpretive prose only — no raw dumps.
"""

from __future__ import annotations

from typing import Any

from company_analysis.cid_bridge import market_snapshot, ownership_snapshot
from intelligence_construction.flags import flags_dict, is_enabled
from intelligence_construction.schema import ARCHITECTURE_STATUS, IC_VERSION, PROGRAMME


def _txt(v: Any, limit: int = 420) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    if not s:
        return None
    return s[:limit]


def _list(v: Any, limit: int = 6) -> list[str]:
    if not isinstance(v, list):
        return []
    out: list[str] = []
    for item in v:
        t = _txt(item, 280)
        if t and t not in out:
            out.append(t)
        if len(out) >= limit:
            break
    return out


def _market_narrative(cid: dict[str, Any], company_analysis: dict[str, Any]) -> str | None:
    snap = market_snapshot(cid)
    if not snap:
        return None
    price = snap.get("current_price")
    hi = snap.get("fifty_two_week_high")
    lo = snap.get("fifty_two_week_low")
    pos = snap.get("range_position_0_1")
    bits: list[str] = []
    name = ((company_analysis.get("identity") or {}).get("company_name") or cid.get("ticker") or "The company")
    if price is not None:
        bits.append(f"{name} currently trades near {price}")
        if snap.get("currency"):
            bits[-1] += f" {snap['currency']}"
        bits[-1] += "."
    if pos is not None:
        if pos >= 0.75:
            bits.append(
                "Price sits toward the upper end of the 52-week range, signalling constructive market momentum while reducing valuation comfort."
            )
        elif pos <= 0.35:
            bits.append(
                "Price remains in the lower half of the 52-week range, reflecting cautious positioning and a wider path for either recovery or further stress."
            )
        else:
            bits.append("Price occupies a mid-range 52-week position — neither extreme momentum nor deep distress.")
    elif hi is not None and lo is not None:
        bits.append(f"The observed 52-week band runs from about {lo} to {hi}.")
    if snap.get("market_cap") is not None:
        bits.append("Market capitalisation in the living dossier anchors scale for peer and ownership context.")
    if snap.get("volume") is not None:
        bits.append("Recent volume is available as a liquidity/context check rather than a standalone signal.")
    return " ".join(bits) if bits else None


def _ownership_narrative(cid: dict[str, Any]) -> str | None:
    own = ownership_snapshot(cid)
    bits: list[str] = []
    inst = own.get("institutions_percent")
    insider = own.get("insiders_percent")
    try:
        if inst is not None:
            iv = float(inst)
            if iv > 1.5:
                iv = iv  # already percent
            else:
                iv = iv * 100
            bits.append(
                f"Institutional ownership near {iv:.1f}% is a useful conviction signal and should be read alongside valuation and business developments."
            )
    except (TypeError, ValueError):
        pass
    try:
        if insider is not None:
            iv = float(insider)
            if iv <= 1.5:
                iv = iv * 100
            bits.append(
                f"Insider ownership around {iv:.1f}% warrants qualitative judgement — selling or buying only matters in context of price and strategy."
            )
    except (TypeError, ValueError):
        pass
    if own.get("ceo"):
        bits.append(f"Leadership context includes CEO {own['ceo']}.")
    return " ".join(bits) if bits else None


def _calendar_narrative(cid: dict[str, Any], company_monitor: dict[str, Any]) -> str | None:
    bits: list[str] = []
    anns = list(cid.get("announcements") or [])[:4]
    for a in anns:
        if not isinstance(a, dict):
            continue
        title = a.get("title") or a.get("headline") or a.get("type")
        if title:
            bits.append(str(title)[:160])
    changed = company_monitor.get("what_changed") if isinstance(company_monitor, dict) else {}
    if isinstance(changed, dict):
        for item in (changed.get("changes") or changed.get("items") or [])[:3]:
            if isinstance(item, dict) and item.get("detail"):
                bits.append(str(item["detail"])[:160])
            elif isinstance(item, str):
                bits.append(item[:160])
    if not bits:
        return None
    return "Upcoming / recent corporate calendar context: " + "; ".join(bits[:4]) + "."


def build_institutional_research_brief(
    *,
    query: str = "",
    ticker: str | None = None,
    cid: dict[str, Any] | None = None,
    company_analysis: dict[str, Any] | None = None,
    company_monitor: dict[str, Any] | None = None,
    finance_academy: dict[str, Any] | None = None,
    knowledge_foundation: dict[str, Any] | None = None,
    live_evidence: dict[str, Any] | None = None,
    data_validation: dict[str, Any] | None = None,
    evidence_completion: dict[str, Any] | None = None,
    irp: dict[str, Any] | None = None,
    investment_office: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not is_enabled():
        return {
            "enabled": False,
            "programme": PROGRAMME,
            "version": IC_VERSION,
            "bypassed": True,
            "architecture_status": ARCHITECTURE_STATUS,
        }

    cid = cid if isinstance(cid, dict) else {}
    ca = company_analysis if isinstance(company_analysis, dict) else {}
    cm = company_monitor if isinstance(company_monitor, dict) else {}
    irp = irp if isinstance(irp, dict) else {}
    academy = finance_academy if isinstance(finance_academy, dict) else {}
    kf = knowledge_foundation if isinstance(knowledge_foundation, dict) else {}
    leo = live_evidence if isinstance(live_evidence, dict) else {}
    dvc = data_validation if isinstance(data_validation, dict) else {}
    ecp = evidence_completion if isinstance(evidence_completion, dict) else {}
    io = investment_office if isinstance(investment_office, dict) else {}

    identity = ca.get("identity") or cid.get("identity") or {}
    name = identity.get("company_name") or ticker or cid.get("ticker") or "the company"
    financial = ca.get("financial_intelligence") or {}
    valuation = ca.get("valuation_intelligence") or {}
    bq = ca.get("business_quality") or {}
    thesis = _txt(ca.get("investment_thesis") or (irp.get("reasoning") or {}).get("what_is_happening"))
    irp_brief = irp.get("institutional_briefing") if isinstance(irp.get("institutional_briefing"), dict) else {}

    market_n = _market_narrative(cid, ca)
    ownership_n = _ownership_narrative(cid)
    calendar_n = _calendar_narrative(cid, cm)
    financial_n = _txt(financial.get("narrative"), 600)
    valuation_n = _txt(valuation.get("narrative"), 600)
    bq_score = bq.get("business_quality_score")

    why: list[str] = []
    if market_n:
        why.append(market_n)
    if financial_n:
        why.append(financial_n)
    if valuation_n:
        why.append(valuation_n)
    if ownership_n:
        why.append(ownership_n)
    if bq_score is not None:
        why.append(
            f"Business quality scores {bq_score}/100 in the institutional company analysis — use as a structured quality scaffold, not a trade signal."
        )
    for hint in (ca.get("ask_agi_hints") or [])[:3]:
        t = _txt(hint, 280)
        if t and t not in why:
            why.append(t)
    for hint in (cm.get("ask_agi_hints") or [])[:2]:
        t = _txt(hint, 260)
        if t and t not in why:
            why.append(t)
    for hint in (academy.get("answer_hints") or [])[:2]:
        t = _txt(hint, 240)
        if t and t not in why:
            why.append(t)
    for hint in (leo.get("answer_hints") or [])[:2]:
        t = _txt(hint, 240)
        if t and t not in why:
            why.append(t)
    for hint in (ecp.get("ask_agi_hints") or [])[:2]:
        t = _txt(hint, 240)
        if t and t not in why:
            why.append(t)
    for hint in (io.get("ask_agi_hints") or [])[:2]:
        t = _txt(hint, 240)
        if t and t not in why:
            why.append(t)
    if calendar_n:
        why.append(calendar_n)
    if dvc.get("research_grade") or dvc.get("data_grade"):
        why.append(
            f"Data confidence grades — research {dvc.get('research_grade') or 'n/a'}, "
            f"data {dvc.get('data_grade') or 'n/a'} — frame how firmly conclusions can be held."
        )

    exec_bits = []
    if thesis:
        exec_bits.append(thesis)
    elif market_n:
        exec_bits.append(market_n)
    if financial_n:
        exec_bits.append(financial_n.split(".")[0] + ".")
    if valuation_n:
        exec_bits.append(valuation_n.split(".")[0] + ".")
    executive = " ".join(exec_bits)[:900] if exec_bits else (
        f"Institutional research brief on {name}: synthesising the living company dossier, "
        "financial intelligence, valuation context and monitored changes."
    )

    key_drivers = _list(
        (irp_brief.get("key_drivers") or [])
        + _list(financial.get("what_improved"), 3)
        + _list((ca.get("catalysts") or []), 3),
        8,
    )
    risks = _list((ca.get("risks") or []) + _list((irp.get("reasoning") or {}).get("risks"), 4), 6)
    catalysts = _list((ca.get("catalysts") or []) + _list((irp.get("reasoning") or {}).get("catalysts"), 4), 6)

    sections = {
        "market_performance": {"narrative": market_n, "snapshot": market_snapshot(cid)},
        "business_quality": {
            "score": bq_score,
            "grade": bq.get("grade"),
            "narrative": _txt(bq.get("narrative") or bq.get("summary"), 400),
        },
        "financial_intelligence": {
            "narrative": financial_n,
            "coverage_pct": financial.get("coverage_pct"),
            "what_improved": financial.get("what_improved") or [],
            "what_deteriorated": financial.get("what_deteriorated") or [],
        },
        "valuation": {
            "narrative": valuation_n,
            "current_pe": valuation.get("current_pe"),
            "forward_pe": valuation.get("forward_pe"),
            "pb": valuation.get("pb"),
            "coverage_pct": valuation.get("coverage_pct"),
        },
        "ownership": {"narrative": ownership_n, "snapshot": ownership_snapshot(cid)},
        "capital_allocation": {
            "signal": financial.get("capital_allocation"),
            "dividend_yield": valuation.get("dividend_yield"),
        },
        "what_changed": cm.get("what_changed") or ca.get("what_changed") or {},
        "calendar": {"narrative": calendar_n},
        "academy": {
            "hints": _list(academy.get("answer_hints"), 4),
            "concepts": len(academy.get("concepts") or academy.get("concept_ids") or []),
        },
        "knowledge_foundation": {
            "hits": len(kf.get("hits") or kf.get("results") or []),
        },
        "live_evidence": {
            "count": leo.get("evidence_count") or len(leo.get("evidence_objects") or []),
        },
        "risks": risks,
        "catalysts": catalysts,
    }

    return {
        "enabled": True,
        "programme": PROGRAMME,
        "version": IC_VERSION,
        "architecture_status": ARCHITECTURE_STATUS,
        "not_an_engine": True,
        "flags": flags_dict(),
        "query": query,
        "ticker": (ticker or identity.get("ticker") or cid.get("ticker") or None),
        "company_name": name,
        "executive_brief": executive,
        "sections": sections,
        "answer_enrichment": {
            "executive_summary": executive,
            "why_bullets": why[:12],
            "valuation_perspective": valuation_n or _txt(irp_brief.get("valuation_perspective"), 400),
            "key_drivers": key_drivers,
            "current_outlook": _txt(irp_brief.get("current_outlook") or thesis, 400),
            "risks": risks,
            "catalysts": catalysts,
        },
        "answer_policy": "institutional_research_brief_from_validated_intelligence",
        "never_expose_providers": True,
    }
