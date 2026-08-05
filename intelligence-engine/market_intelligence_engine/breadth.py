"""Market breadth from warehouse price history."""

from __future__ import annotations

from typing import Any, Optional


def market_breadth(*, sample_limit: int = 3000) -> dict[str, Any]:
    from institutional_warehouse import db, store

    table = db.physical_table("daily_market_history")
    dates = db.query(f'SELECT DISTINCT "date" AS d FROM {table} ORDER BY d DESC LIMIT 2')
    if len(dates) < 2:
        return {"ok": False, "error": "insufficient_price_history", "advancing": 0, "declining": 0}

    latest, prior = dates[0]["d"], dates[1]["d"]
    latest_rows = {
        str(r.get("symbol") or "").upper(): r
        for r in store.fetch("daily_market_history", filters={"date": latest}, limit=sample_limit)["rows"]
    }
    prior_rows = {
        str(r.get("symbol") or "").upper(): r
        for r in store.fetch("daily_market_history", filters={"date": prior}, limit=sample_limit)["rows"]
    }

    advancing = declining = unchanged = 0
    returns: list[float] = []
    for sym, row in latest_rows.items():
        prev = prior_rows.get(sym)
        if not prev:
            continue
        try:
            close = float(row.get("close") or row.get("adjusted_close") or 0)
            old = float(prev.get("close") or prev.get("adjusted_close") or 0)
        except (TypeError, ValueError):
            continue
        if old <= 0:
            continue
        chg = 100.0 * (close - old) / old
        returns.append(chg)
        if chg > 0.05:
            advancing += 1
        elif chg < -0.05:
            declining += 1
        else:
            unchanged += 1

    avg_ret = round(sum(returns) / len(returns), 2) if returns else None
    med_ret = None
    if returns:
        ordered = sorted(returns)
        mid = len(ordered) // 2
        med_ret = ordered[mid] if len(ordered) % 2 else (ordered[mid - 1] + ordered[mid]) / 2
        med_ret = round(med_ret, 2)

    sentiment = "Neutral"
    if avg_ret is not None:
        if avg_ret >= 0.35:
            sentiment = "Risk On"
        elif avg_ret <= -0.35:
            sentiment = "Risk Off"

    heatmap = "Neutral"
    ratio = advancing / max(1, advancing + declining)
    if ratio >= 0.65:
        heatmap = "Strong Bullish"
    elif ratio >= 0.55:
        heatmap = "Bullish"
    elif ratio <= 0.35:
        heatmap = "Strong Bearish"
    elif ratio <= 0.45:
        heatmap = "Bearish"

    return {
        "ok": True,
        "date": latest,
        "prior_date": prior,
        "advancing": advancing,
        "declining": declining,
        "unchanged": unchanged,
        "average_return_pct": avg_ret,
        "median_return_pct": med_ret,
        "sentiment": sentiment,
        "heatmap": heatmap,
        "sample_size": len(returns),
        "tracked_universe": len(returns),
        "universe_definition": (
            "Breadth uses symbols with consecutive daily closes in warehouse.daily_market_history "
            f"for {latest} vs {prior}. Moves beyond ±0.05% count as advancing/declining; "
            f"within ±0.05% count as unchanged. Sample capped at {sample_limit} symbols per session."
        ),
        "untracked_reasons": [
            "No consecutive price history in warehouse for the latest two sessions",
            "Illiquid or suspended names excluded from daily_market_history",
            "Recently listed symbols pending history accumulation",
            "Valuation universe exceeds price-history coverage",
        ],
        "coverage": {
            "history": len(returns),
            "confidence": "high" if len(returns) >= 500 else "moderate" if len(returns) >= 100 else "low",
            "source": "warehouse.daily_market_history",
        },
    }
