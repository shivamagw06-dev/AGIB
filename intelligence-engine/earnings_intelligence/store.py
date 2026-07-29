"""Persist parsed financial statement series into historical_depth when available."""

from __future__ import annotations

from typing import Any


def persist_pack(pack: dict[str, Any]) -> dict[str, Any]:
    ticker = str(pack.get("ticker") or "").upper()
    if not ticker or not pack.get("ok"):
        return {"written": 0, "ticker": ticker, "skipped": True}
    try:
        from knowledge_factory.historical_depth import store as hd_store
        from knowledge_factory.historical_depth.schema import pit_record
    except Exception as exc:  # pragma: no cover
        return {"written": 0, "ticker": ticker, "error": str(exc)[:160]}

    pits = []
    for row in list(pack.get("quarter_history") or []) + list(pack.get("annual_history") or []):
        pe = row.get("period_end")
        if not pe:
            continue
        inc = row.get("income_statement") or {}
        bal = row.get("balance_sheet") or {}
        cf = row.get("cash_flow") or {}
        freq = row.get("frequency") or "quarterly"
        pits.append(
            pit_record(
                entity=ticker,
                kind="financials_quarterly" if freq == "quarterly" else "financials_annual",
                period=str(row.get("quarter_label") or row.get("fiscal_year_label") or pe),
                period_end=str(pe)[:10],
                available_from=str(row.get("filing_date") or pe)[:10],
                payload={
                    "statement": "mixed",
                    "frequency": freq,
                    "revenue": inc.get("revenue_from_operations"),
                    "ebitda": inc.get("ebitda"),
                    "ebit": inc.get("ebit"),
                    "net_income": inc.get("pat_owners") or inc.get("pat"),
                    "eps": inc.get("eps_basic"),
                    "ocf": cf.get("operating_cash_flow"),
                    "fcf": cf.get("free_cash_flow"),
                    "cash": bal.get("cash"),
                    "total_debt": bal.get("total_debt"),
                    "equity": bal.get("total_equity"),
                    "source": "earnings_intelligence_p21",
                },
                source="earnings_intelligence_p21",
                confidence=float(pack.get("confidence") or 0.9),
            )
        )
    # Store under both series names used by HD
    q_pits = [p for p in pits if (p.get("payload") or {}).get("frequency") == "quarterly"]
    a_pits = [p for p in pits if (p.get("payload") or {}).get("frequency") == "annual"]
    written = 0
    if q_pits:
        hd_store.put_series("financials_quarterly", ticker, q_pits)
        written += len(q_pits)
    if a_pits:
        hd_store.put_series("financials_annual", ticker, a_pits)
        written += len(a_pits)
    return {"written": written, "ticker": ticker, "skipped": False}
