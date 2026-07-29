"""Institutional Readiness Gate — evidence coverage before conviction.

Separates:
  • Company quality (franchise strength)
  • Market opportunity (timing / payoff)
  • Evidence confidence (data completeness)

Never conflate thin research packs with a weak business.
"""

from __future__ import annotations

from typing import Any

# Coverage → allowed conviction band
# >95 high · 80–95 moderate · 60–80 watchlist · <60 deferred
HIGH_CONVICTION_COVERAGE = 95.0
MODERATE_CONVICTION_COVERAGE = 80.0
WATCHLIST_COVERAGE = 60.0
# Absolute floor: never High Conviction below this evidence confidence
HIGH_CONVICTION_EVIDENCE_FLOOR = 80.0


def _pct(*vals: Any, default: float = 0.0) -> float:
    for v in vals:
        if v is None:
            continue
        try:
            n = float(v)
        except (TypeError, ValueError):
            continue
        if n <= 1.5:
            n *= 100.0
        return max(0.0, min(100.0, n))
    return float(default)


def _has_records(series: Any) -> bool:
    if not isinstance(series, dict):
        return False
    return bool(series.get("records") or series.get("items") or series.get("documents"))


def _layer_status_score(layers: dict[str, Any], key: str) -> tuple[float, str]:
    row = layers.get(key) or {}
    st = str(row.get("status") or "incomplete")
    sc = row.get("score")
    if st == "complete" and sc is not None:
        return 100.0, "available"
    if st == "partial":
        return 65.0, "partial"
    if sc is not None:
        return 45.0, "thin"
    return 15.0, "missing"


def compute_coverage_board(
    *,
    layers: dict[str, Any] | None = None,
    company_analysis: dict[str, Any] | None = None,
    cid: dict[str, Any] | None = None,
    live_evidence: dict[str, Any] | None = None,
    evidence_completion: dict[str, Any] | None = None,
    valuation_pack: dict[str, Any] | None = None,
    irp: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Per-domain coverage % used by the readiness gate."""
    layers = layers if isinstance(layers, dict) else {}
    ca = company_analysis if isinstance(company_analysis, dict) else {}
    cid = cid if isinstance(cid, dict) else {}
    leo = live_evidence if isinstance(live_evidence, dict) else {}
    ecp = evidence_completion if isinstance(evidence_completion, dict) else {}
    ve = valuation_pack if isinstance(valuation_pack, dict) else {}
    irp = irp if isinstance(irp, dict) else {}
    readiness = ca.get("recommendation_readiness") or {}
    r_scores = readiness.get("scores") or {}
    fin = ca.get("financial_intelligence") or {}
    val = ca.get("valuation_intelligence") or {}
    panel = ecp.get("quality_panel") or {}

    # Financials
    financials = _pct(
        fin.get("coverage_pct"),
        r_scores.get("financial_intelligence"),
        default=0,
    )
    if financials < 20 and (fin.get("narrative") or fin.get("enabled")):
        financials = max(financials, 40.0)

    # Ownership / shareholding
    ownership = 0.0
    sh = cid.get("shareholding") or cid.get("ownership") or ca.get("shareholding") or ca.get("ownership")
    if _has_records(sh) or (isinstance(sh, dict) and (sh.get("promoter") is not None or sh.get("fii") is not None)):
        ownership = 90.0
    elif isinstance(sh, dict) and sh:
        ownership = 55.0
    elif r_scores.get("evidence_confidence"):
        ownership = min(50.0, _pct(r_scores.get("evidence_confidence"), default=0) * 0.5)

    # Valuation
    valuation = _pct(val.get("coverage_pct"), r_scores.get("valuation"), default=0)
    if valuation < 20 and (val.get("current_pe") is not None or ve.get("latest_valuation") or val.get("narrative")):
        valuation = max(valuation, 55.0 if val.get("current_pe") is not None else 40.0)
    peer_ok = bool(val.get("peer_pe") or val.get("peer_comparison") or (ca.get("identity") or {}).get("peers"))
    if not peer_ok and valuation > 0:
        valuation = min(valuation, 70.0)

    # Macro / industry
    macro_s, _ = _layer_status_score(layers, "macro")
    industry_s, _ = _layer_status_score(layers, "industry")
    macro = round(0.5 * macro_s + 0.5 * industry_s, 1)
    if r_scores.get("sector_intelligence"):
        macro = max(macro, _pct(r_scores.get("sector_intelligence")))

    # Technicals
    tech_s, tech_state = _layer_status_score(layers, "technical")
    technicals = tech_s
    if tech_state == "missing":
        technicals = 20.0

    # News / filings / research
    news = 30.0
    filings = 30.0
    research = _pct(r_scores.get("research"), default=40)
    objs = leo.get("evidence_objects") or leo.get("objects") or []
    if objs:
        kinds = {str((o or {}).get("kind") or (o or {}).get("type") or "").lower() for o in objs if isinstance(o, dict)}
        if any("news" in k or "announcement" in k for k in kinds):
            news = 85.0
        if any("filing" in k or "annual" in k or "quarter" in k or "result" in k for k in kinds):
            filings = 90.0
        research = max(research, 70.0)
    if cid.get("evidence_timeline") or cid.get("research") or cid.get("filings"):
        filings = max(filings, 75.0)
        research = max(research, 70.0)
    if irp.get("evidence") or irp.get("ranked_evidence") or irp.get("institutional_briefing"):
        research = max(research, 85.0)
        news = max(news, 55.0)
    if panel.get("coverage_pct") is not None:
        research = max(research, min(95.0, _pct(panel.get("coverage_pct"))))

    board = {
        "financials": round(financials, 1),
        "ownership": round(ownership, 1),
        "valuation": round(valuation, 1),
        "macro": round(macro, 1),
        "technicals": round(technicals, 1),
        "news": round(news, 1),
        "filings": round(filings, 1),
        "research": round(research, 1),
    }
    overall = round(sum(board.values()) / max(1, len(board)), 1)
    return {"dimensions": board, "overall_coverage_pct": overall}


def _checklist_from_coverage(board: dict[str, float], *, layers: dict[str, Any], ca: dict[str, Any], peer_ok: bool) -> list[dict[str, Any]]:
    dims = board.get("dimensions") or {}
    items: list[dict[str, Any]] = []

    def add(label: str, ok: bool, *, warn: bool = False, detail: str = "") -> None:
        if ok:
            mark, state = "✓", "available"
        elif warn:
            mark, state = "⚠", "partial"
        else:
            mark, state = "❌", "missing"
        items.append({"label": label, "present": ok, "warn": warn and not ok, "mark": mark, "status": state, "detail": detail})

    add("Business analysis available", float((layers.get("company_quality") or {}).get("score") or 0) > 0 or bool(ca.get("business_quality")))
    add(
        "Financial statements available",
        float(dims.get("financials") or 0) >= 60,
        warn=float(dims.get("financials") or 0) >= 35,
        detail=f"coverage {dims.get('financials')}%",
    )
    add(
        "Macro analysis available",
        float(dims.get("macro") or 0) >= 55,
        warn=float(dims.get("macro") or 0) >= 35,
    )
    add(
        "Peer valuation complete",
        peer_ok and float(dims.get("valuation") or 0) >= 70,
        warn=float(dims.get("valuation") or 0) >= 40,
        detail="peer comparison incomplete" if not peer_ok else "",
    )
    add(
        "Shareholding current",
        float(dims.get("ownership") or 0) >= 80,
        warn=float(dims.get("ownership") or 0) >= 40,
        detail="ownership pack thin or outdated" if float(dims.get("ownership") or 0) < 80 else "",
    )
    add(
        "Latest earnings / filings indexed",
        float(dims.get("filings") or 0) >= 75,
        warn=float(dims.get("filings") or 0) >= 40,
    )
    add(
        "Technical model confidence",
        float(dims.get("technicals") or 0) >= 70,
        warn=float(dims.get("technicals") or 0) >= 40,
        detail="below institutional threshold" if float(dims.get("technicals") or 0) < 70 else "",
    )
    add(
        "Research corpus available",
        float(dims.get("research") or 0) >= 70,
        warn=float(dims.get("research") or 0) >= 45,
    )
    return items


def compute_quality_opportunity(
    *,
    layers: dict[str, Any] | None = None,
    company_analysis: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Company quality vs market opportunity — independent of evidence confidence."""
    layers = layers if isinstance(layers, dict) else {}
    ca = company_analysis if isinstance(company_analysis, dict) else {}
    bq = ca.get("business_quality") or {}
    fin = ca.get("financial_intelligence") or {}

    cq = _pct(
        (layers.get("company_quality") or {}).get("score"),
        bq.get("business_quality_score"),
        default=55,
    )
    # Financial company quality: use trend signals, NOT coverage blend
    fq_layer = layers.get("financial_quality") or {}
    fq = _pct(fq_layer.get("company_quality_score"), fq_layer.get("score"), default=55)
    mgmt = _pct((layers.get("management") or {}).get("score"), default=55)
    company_quality = round((cq * 0.45 + fq * 0.35 + mgmt * 0.20) / 10.0, 1)  # 0–10 scale

    val = _pct((layers.get("valuation") or {}).get("score"), default=55)
    exp = _pct((layers.get("market_expectations") or {}).get("score"), default=55)
    tech = _pct((layers.get("technical") or {}).get("score"), default=50)
    macro = _pct((layers.get("macro") or {}).get("score"), default=55)
    market_opportunity = round((val * 0.35 + exp * 0.25 + tech * 0.20 + macro * 0.20) / 10.0, 1)

    strengths: list[str] = []
    weaknesses: list[str] = []
    for x in (bq.get("strengths") or fin.get("what_improved") or [])[:4]:
        strengths.append(str(x).replace("_", " ").strip().capitalize())
    for x in (bq.get("weaknesses") or fin.get("what_deteriorated") or [])[:4]:
        weaknesses.append(str(x).replace("_", " ").strip().capitalize())
    model = str((ca.get("identity") or {}).get("business_model") or "").strip()
    if model and not strengths:
        strengths.append(model[:120])
    if cq >= 70 and "Franchise durability" not in strengths:
        strengths.append("Franchise quality signals constructive")
    if fq < 55:
        weaknesses.append("Financial trend evidence still soft")
    if not strengths:
        strengths.append("Identity and sector context available for analysis")
    if not weaknesses:
        weaknesses.append("Incomplete verified datasets limit precision")

    return {
        "company_quality_10": company_quality,
        "market_opportunity_10": market_opportunity,
        "company_quality_100": round(company_quality * 10, 1),
        "market_opportunity_100": round(market_opportunity * 10, 1),
        "strengths": strengths[:5],
        "weaknesses": weaknesses[:5],
    }


def evaluate_readiness_gate(
    *,
    layers: dict[str, Any] | None = None,
    company_analysis: dict[str, Any] | None = None,
    cid: dict[str, Any] | None = None,
    live_evidence: dict[str, Any] | None = None,
    evidence_completion: dict[str, Any] | None = None,
    valuation_pack: dict[str, Any] | None = None,
    irp: dict[str, Any] | None = None,
    external_gate_blocked: bool = False,
    name: str = "this company",
) -> dict[str, Any]:
    """Full Institutional Readiness Gate for Ask / Decision Engine."""
    layers = layers if isinstance(layers, dict) else {}
    ca = company_analysis if isinstance(company_analysis, dict) else {}
    board = compute_coverage_board(
        layers=layers,
        company_analysis=ca,
        cid=cid,
        live_evidence=live_evidence,
        evidence_completion=evidence_completion,
        valuation_pack=valuation_pack,
        irp=irp,
    )
    dims = board["dimensions"]
    overall = float(board["overall_coverage_pct"])
    qo = compute_quality_opportunity(layers=layers, company_analysis=ca)

    # Evidence confidence = overall coverage, tempered by weakest hard pillars
    hard_floor = min(dims.get("financials", 0), dims.get("valuation", 0), dims.get("ownership", 0) or 50)
    evidence_confidence = round(0.7 * overall + 0.3 * hard_floor, 1)

    peer_ok = bool(
        (ca.get("valuation_intelligence") or {}).get("peer_pe")
        or (ca.get("valuation_intelligence") or {}).get("peer_comparison")
        or (ca.get("identity") or {}).get("peers")
    )
    checklist = _checklist_from_coverage(board, layers=layers, ca=ca, peer_ok=peer_ok)
    missing = [c["label"] for c in checklist if not c["present"]]
    warnings = [c["label"] for c in checklist if c.get("warn")]

    if overall >= HIGH_CONVICTION_COVERAGE and evidence_confidence >= HIGH_CONVICTION_EVIDENCE_FLOOR:
        band = "high_conviction_allowed"
        band_label = "High Conviction allowed"
        passed = True
    elif overall >= MODERATE_CONVICTION_COVERAGE:
        band = "moderate_conviction"
        band_label = "Moderate Conviction"
        passed = True
    elif overall >= WATCHLIST_COVERAGE:
        band = "watchlist"
        band_label = "Watchlist"
        passed = False
    else:
        band = "deferred"
        band_label = "Recommendation Deferred"
        passed = False

    # External LEO/SIF block forces deferral even if coverage looks ok
    if external_gate_blocked and band in {"high_conviction_allowed", "moderate_conviction"}:
        band = "watchlist" if overall >= WATCHLIST_COVERAGE else "deferred"
        band_label = "Watchlist" if band == "watchlist" else "Recommendation Deferred"
        passed = False
        if "External evidence gate blocked" not in missing:
            missing.append("External evidence gate blocked")

    # Never High Conviction when evidence confidence < 80
    if evidence_confidence < HIGH_CONVICTION_EVIDENCE_FLOOR and band == "high_conviction_allowed":
        band = "moderate_conviction"
        band_label = "Moderate Conviction"
        passed = True

    gate_failed = band in {"deferred", "watchlist"} or not passed and band == "deferred"
    # Watchlist is soft-fail (can discuss, not high conviction); Deferred is hard-fail
    hard_fail = band == "deferred" or (external_gate_blocked and evidence_confidence < MODERATE_CONVICTION_COVERAGE)

    investment_thesis_status = "INCONCLUSIVE" if hard_fail or band == "watchlist" else "FORMED"
    not_a_negative_view = investment_thesis_status == "INCONCLUSIVE"

    required_evidence = []
    for c in checklist:
        if not c["present"]:
            required_evidence.append(c["label"] + (f" — {c['detail']}" if c.get("detail") else ""))

    status_mark = "FAILED" if hard_fail or band == "watchlist" else "PASSED"
    if band == "watchlist":
        status_mark = "FAILED"
        reason_lead = (
            f"Evidence coverage ({overall:.0f}%) is below the institutional bar for a conviction call. "
            "This is not a negative view of the company — the research pack is incomplete."
        )
    elif band == "deferred":
        status_mark = "FAILED"
        reason_lead = (
            f"Institutional evidence coverage ({overall:.0f}%) is insufficient to reach a recommendation. "
            "This should not be interpreted as a negative view of the company."
        )
    else:
        status_mark = "PASSED"
        reason_lead = (
            f"Evidence coverage ({overall:.0f}%) supports institutional analysis. "
            "High-conviction language remains capped by evidence confidence."
        )

    return {
        "programme": "AGIB_INSTITUTIONAL_READINESS_GATE",
        "version": "readiness-gate-v1.0.0",
        "passed": bool(passed) and not hard_fail,
        "status": status_mark,
        "status_mark": "❌ FAILED" if status_mark == "FAILED" else "✓ PASSED",
        "band": band,
        "band_label": band_label,
        "hard_fail": hard_fail,
        "gate_blocks_high_conviction": evidence_confidence < HIGH_CONVICTION_EVIDENCE_FLOOR,
        "overall_coverage_pct": overall,
        "evidence_confidence_pct": evidence_confidence,
        "required_confidence_pct": HIGH_CONVICTION_EVIDENCE_FLOOR,
        "coverage": dims,
        "checklist": checklist,
        "available": [c["label"] for c in checklist if c["present"]],
        "missing": missing,
        "warnings": warnings,
        "additional_evidence_required": required_evidence[:8],
        "company_quality_10": qo["company_quality_10"],
        "market_opportunity_10": qo["market_opportunity_10"],
        "company_quality_100": qo["company_quality_100"],
        "market_opportunity_100": qo["market_opportunity_100"],
        "strengths": qo["strengths"],
        "weaknesses": qo["weaknesses"],
        "investment_thesis_status": investment_thesis_status,
        "not_a_negative_view": not_a_negative_view,
        "reason": reason_lead,
        "summary_for_user": {
            "title": "Institutional Gate Status",
            "status": status_mark,
            "reason": reason_lead,
            "checklist": checklist,
            "evidence_confidence_pct": evidence_confidence,
            "required_confidence_pct": HIGH_CONVICTION_EVIDENCE_FLOOR,
            "company_quality_10": qo["company_quality_10"],
            "market_opportunity_10": qo["market_opportunity_10"],
            "coverage": dims,
            "overall_coverage_pct": overall,
            "investment_thesis": investment_thesis_status,
            "note": (
                "Insufficient evidence must not be read as a negative company view."
                if not_a_negative_view
                else "Evidence supports analysis; conviction still follows the decision stack."
            ),
        },
        "thresholds": {
            "high_conviction_coverage_pct": HIGH_CONVICTION_COVERAGE,
            "moderate_conviction_coverage_pct": MODERATE_CONVICTION_COVERAGE,
            "watchlist_coverage_pct": WATCHLIST_COVERAGE,
            "high_conviction_evidence_floor_pct": HIGH_CONVICTION_EVIDENCE_FLOOR,
        },
        "company": name,
        "never_conflate_data_with_quality": True,
    }
