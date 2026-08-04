"""Sector rotation and market explainability."""

from __future__ import annotations

from typing import Any


def market_rotation(sectors: list[dict[str, Any]], universe: dict[str, Any]) -> dict[str, Any]:
    if not sectors:
        return {"ok": False, "error": "no_sectors"}

    # Rank sectors by median PE change in member stocks.
    sector_moves: dict[str, list[float]] = {}
    for row in universe.get("rows") or []:
        sector = row.get("sector")
        chg = row.get("pe_change_pct")
        if sector and chg is not None:
            sector_moves.setdefault(str(sector), []).append(float(chg))

    ranked = []
    for sector, moves in sector_moves.items():
        avg = sum(moves) / len(moves) if moves else 0
        ranked.append({"sector": sector, "avg_pe_change_pct": round(avg, 2), "companies": len(moves)})
    ranked.sort(key=lambda r: r["avg_pe_change_pct"])

    leaving = ranked[:3]
    entering = list(reversed(ranked[-3:]))

    explanation_parts = []
    if entering:
        top = entering[0]
        explanation_parts.append(
            f"Valuation expansion is concentrated in {top['sector']} "
            f"(average P/E change {top['avg_pe_change_pct']:+.1f}%), "
            "indicating multiple-led moves rather than a uniform market re-rating."
        )
    premium = sorted(
        [s for s in sectors if s.get("historical_percentile") is not None],
        key=lambda s: -(s.get("historical_percentile") or 0),
    )
    if premium:
        explanation_parts.append(
            f"{premium[0]['sector']} remains in the upper historical valuation band "
            f"(percentile ~{premium[0]['historical_percentile']:.0f}%)."
        )
    explanation_parts.append("Rotation context only — not a recommendation.")

    return {
        "ok": True,
        "leaving": leaving,
        "entering": entering,
        "rows": ranked,
        "explanation": " ".join(explanation_parts),
    }


def market_explainability(universe: dict[str, Any], *, limit: int = 6) -> list[dict[str, Any]]:
    """Explain major sector-level multiple moves using attribution pattern."""
    from valuation_engine import attribution

    rows = universe.get("rows") or []
    sector_groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if row.get("sector"):
            sector_groups.setdefault(str(row["sector"]), []).append(row)

    narratives = []
    for sector, members in sector_groups.items():
        if len(members) < 8:
            continue
        pe_changes = [m.get("pe_change_pct") for m in members if m.get("pe_change_pct") is not None]
        if not pe_changes:
            continue
        avg_pe_chg = sum(pe_changes) / len(pe_changes)
        if abs(avg_pe_chg) < 1.5:
            continue
        # Representative member with largest move
        rep = max(members, key=lambda m: abs(m.get("pe_change_pct") or 0))
        before = {"pe": rep.get("prev_pe"), "pb": rep.get("prev_pb"), "cmp": rep.get("cmp")}
        after = {"pe": rep.get("pe"), "pb": rep.get("pb"), "cmp": rep.get("cmp")}
        entry = attribution.explain_change("pe", before, after)
        narratives.append({
            "sector": sector,
            "symbol": rep.get("symbol"),
            "metric": "pe",
            "change_pct": round(avg_pe_chg, 2),
            "summary": entry.get("summary") or f"{sector} P/E moved {avg_pe_chg:+.1f}% on average.",
            "drivers": entry.get("drivers") or [],
        })
        if len(narratives) >= limit:
            break
    return narratives
