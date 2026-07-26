"""Step 3 — Financial intelligence from CID / DVC / FIE-like dossier fields (no raw providers)."""

from __future__ import annotations

from typing import Any

from company_analysis.flags import flag_financial


def _num(v: Any) -> float | None:
    try:
        if v is None or v == "":
            return None
        return float(v)
    except Exception:
        return None


def _pick(d: dict[str, Any], *keys: str) -> Any:
    for k in keys:
        if k in d and d[k] not in (None, "", []):
            return d[k]
    return None


def analyse_financials(
    *,
    identity: dict[str, Any],
    cid: dict[str, Any] | None = None,
    dvc_pkg: dict[str, Any] | None = None,
    leo_pkg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not flag_financial():
        return {"enabled": False, "bypassed": True}

    cid = cid or {}
    dvc = dvc_pkg or {}
    validated = dict(dvc.get("validated_fields") or cid.get("validated_fields") or {})
    fin = dict(cid.get("financials") or cid.get("financial_intelligence") or {})
    hist = dict(cid.get("financial_history") or {})
    metrics = {**fin, **validated}

    growth = _pick(metrics, "revenue_growth", "sales_growth", "loan_growth", "growth")
    margins = _pick(metrics, "operating_margin", "npm", "nim", "ebitda_margin", "margin")
    returns = _pick(metrics, "roe", "roic", "roa", "return_on_equity")
    cash = _pick(metrics, "fcf", "operating_cash_flow", "cash_conversion")
    leverage = _pick(metrics, "debt_to_equity", "leverage", "cet1", "capital_adequacy")
    credit = _pick(metrics, "credit_cost", "gnpa", "nnpa", "provision_coverage")

    improved: list[str] = []
    deteriorated: list[str] = []
    monitor: list[str] = []

    # Trend hints from history blocks if present
    trends = hist.get("trends") if isinstance(hist.get("trends"), dict) else {}
    for label, key in (
        ("growth", "growth"),
        ("margins", "margins"),
        ("returns", "returns"),
        ("cash_flow", "cash_flow"),
        ("asset_quality", "asset_quality"),
    ):
        direction = str((trends.get(key) or "")).lower()
        if direction in {"up", "improving", "better"}:
            improved.append(label)
        elif direction in {"down", "deteriorating", "worse"}:
            deteriorated.append(label)

    sector = str(identity.get("sector_id") or identity.get("sector") or "").lower()
    if "bank" in sector:
        monitor.extend(["NIM trajectory", "Credit cost", "CASA mix", "Loan growth vs deposit growth", "Capital (CET1)"])
        if credit is None:
            deteriorated.append("credit_cost_coverage_missing")
        if returns is not None:
            monitor.append("ROE sustainability vs leverage/credit cost")
    elif "fmcg" in sector or "staple" in sector:
        monitor.extend(["Volume vs pricing", "Gross margin", "Working capital days", "A&P intensity", "ROIC"])
    else:
        monitor.extend(["Revenue growth quality", "Margin durability", "Cash conversion", "Balance-sheet risk"])

    # Evidence from LEO objects (typed, not raw)
    leo_types = []
    for obj in (leo_pkg or {}).get("evidence_objects") or []:
        if isinstance(obj, dict) and obj.get("type"):
            leo_types.append(str(obj.get("type")))

    coverage = 0
    for v in (growth, margins, returns, cash, leverage):
        if v is not None:
            coverage += 20
    if hist:
        coverage = min(100, coverage + 10)
    if validated:
        coverage = min(100, coverage + 10)

    narrative_bits = []
    if returns is not None:
        narrative_bits.append(f"Return metric observed: {returns}.")
    if margins is not None:
        narrative_bits.append(f"Margin / spread signal: {margins}.")
    if growth is not None:
        narrative_bits.append(f"Growth signal: {growth}.")
    if not narrative_bits:
        narrative_bits.append(
            "Financial fields are incomplete in CID/DVC — analysis limited to available institutional evidence; no raw provider fill-in."
        )

    return {
        "enabled": True,
        "growth": growth,
        "margins": margins,
        "capital_allocation": _pick(metrics, "capital_allocation", "dividend_payout", "buyback"),
        "cash_flow": cash,
        "balance_sheet": {
            "leverage": leverage,
            "credit_or_asset_quality": credit,
        },
        "returns": returns,
        "historical_trends": trends or hist.get("summary") or {},
        "financial_health": "monitored" if coverage >= 40 else "insufficient_coverage",
        "what_improved": improved,
        "what_deteriorated": deteriorated,
        "what_deserves_monitoring": monitor[:8],
        "coverage_pct": coverage,
        "narrative": " ".join(narrative_bits),
        "leo_evidence_types": sorted(set(leo_types))[:12],
        "sources": ["cid.financials", "cid.financial_history", "dvc.validated_fields", "leo.evidence_objects"],
    }
