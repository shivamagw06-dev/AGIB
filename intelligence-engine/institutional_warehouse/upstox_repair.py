"""Safe one-time repair for annual Upstox data that was labelled as quarterly Q4."""

from __future__ import annotations

from institutional_warehouse import store


def repair_annual_as_quarterly(*, actor: str = "system", apply: bool = False) -> dict:
    """Retire only exact annual/Q4 duplicates; never delete source rows."""
    annual = store.all_rows("financials_annual", limit=50000)
    quarterly = store.all_rows("financials_quarterly", limit=50000)
    index = {
        (r.get("symbol"), r.get("fiscal_year"), r.get("statement_type")): r
        for r in annual
        if str(r.get("source") or "").lower() == "upstox"
    }
    candidates: list[str] = []
    for row in quarterly:
        if (
            str(row.get("source") or "").lower() != "upstox"
            or not str(row.get("fiscal_period") or "").upper().endswith("Q4")
        ):
            continue
        annual_row = index.get((row.get("symbol"), row.get("fiscal_year"), row.get("statement_type")))
        if not annual_row:
            continue
        fields = ("revenue", "pbt", "pat", "eps")
        shared = [field for field in fields if row.get(field) is not None and annual_row.get(field) is not None]
        if shared and all(float(row[field]) == float(annual_row[field]) for field in shared):
            row_id = str(row.get("row_id") or "")
            if row_id:
                candidates.append(row_id)
    result = {
        "ok": True,
        "candidates": len(candidates),
        "row_ids": candidates[:100],
        "applied": False,
        "rule": "same Upstox source, symbol, fiscal year, statement type and Q4 values exactly equal to annual values",
    }
    if apply and candidates:
        result.update(store.retire_rows(
            "financials_quarterly",
            candidates,
            actor=actor,
            reason="upstox annual full_statement mislabelled as quarterly Q4",
        ))
        result["applied"] = True
    return result
