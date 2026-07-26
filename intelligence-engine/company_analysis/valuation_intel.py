"""Step 4 — Valuation intelligence (interpret multiples; do not only display them)."""

from __future__ import annotations

from typing import Any

from company_analysis.flags import flag_valuation


def _num(v: Any) -> float | None:
    try:
        if v is None or v == "":
            return None
        return float(v)
    except Exception:
        return None


def analyse_valuation(
    *,
    identity: dict[str, Any],
    cid: dict[str, Any] | None = None,
    valuation_pack: dict[str, Any] | None = None,
    dvc_pkg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not flag_valuation():
        return {"enabled": False, "bypassed": True}

    cid = cid or {}
    val = dict(cid.get("valuation") or {})
    ve = valuation_pack or {}
    company_ve = ve.get("company") if isinstance(ve.get("company"), dict) else {}
    validated = dict((dvc_pkg or {}).get("validated_fields") or cid.get("validated_fields") or {})

    pe = _num(val.get("pe") or validated.get("pe") or company_ve.get("pe") or company_ve.get("trailing_pe"))
    pb = _num(val.get("pb") or validated.get("pb") or company_ve.get("pb"))
    hist_pe = _num(val.get("historical_pe") or val.get("pe_median") or val.get("avg_pe"))
    peer_pe = _num(val.get("peer_pe") or val.get("sector_pe"))
    expected_growth = val.get("expected_growth") or company_ve.get("growth") or validated.get("earnings_growth")
    intrinsic = company_ve.get("intrinsic_value") or val.get("intrinsic_value")
    mos = company_ve.get("margin_of_safety") or val.get("margin_of_safety")

    premium_discount = None
    implication = []
    if pe is not None and hist_pe is not None and hist_pe > 0:
        premium_discount = round((pe / hist_pe - 1.0) * 100.0, 1)
        if premium_discount > 10:
            implication.append(
                f"Current PE {pe} is ~{premium_discount}% above historical PE {hist_pe} — market embeds above-average expectations."
            )
        elif premium_discount < -10:
            implication.append(
                f"Current PE {pe} is ~{abs(premium_discount)}% below historical PE {hist_pe} — either a discount opportunity or lower embedded growth/quality."
            )
        else:
            implication.append(f"Current PE {pe} is near historical PE {hist_pe} — valuation close to own history.")
    elif pe is not None:
        implication.append(f"Current PE {pe} observed; historical PE range incomplete in dossier — avoid single-multiple conclusions.")
    else:
        implication.append("PE not available from CID/DVC/VE — valuation discussion withheld on multiples.")

    if peer_pe is not None and pe is not None and peer_pe > 0:
        vs_peer = round((pe / peer_pe - 1.0) * 100.0, 1)
        implication.append(
            f"Vs peer/sector PE {peer_pe}: company trades {vs_peer}% {'premium' if vs_peer > 0 else 'discount'} — justify via growth, ROE/ROIC and risk."
        )

    if expected_growth is not None:
        implication.append(f"Embedded / expected growth signal: {expected_growth}.")
    if intrinsic is not None:
        implication.append(f"Intrinsic value reference from VE/CID: {intrinsic}.")
    if mos is not None:
        implication.append(f"Margin of safety reference: {mos}.")

    sector = str(identity.get("sector_id") or "").lower()
    if "bank" in sector:
        implication.append("For banks, prefer P/B + ROE/COE framing beside PE; PE alone misleads across credit cycles.")
    if "fmcg" in sector or "staple" in sector:
        implication.append("For premium FMCG, PE premium must be earned by ROIC durability, pricing power and cash conversion.")

    coverage = 0
    for v in (pe, hist_pe, peer_pe, intrinsic, mos):
        if v is not None:
            coverage += 20

    return {
        "enabled": True,
        "current_pe": pe,
        "historical_pe": hist_pe,
        "pb": pb,
        "premium_discount_vs_history_pct": premium_discount,
        "expected_growth": expected_growth,
        "embedded_expectations": implication[:3],
        "peer_valuation": {"peer_pe": peer_pe, "peers": identity.get("peers") or []},
        "historical_valuation_range": val.get("pe_range") or val.get("historical_range"),
        "intrinsic_value": intrinsic,
        "margin_of_safety": mos,
        "narrative": " ".join(implication),
        "coverage_pct": min(100, coverage),
        "sources": ["cid.valuation", "dvc.validated_fields", "ve.consult"],
    }
