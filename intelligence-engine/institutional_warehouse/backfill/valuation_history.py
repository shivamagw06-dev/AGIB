"""Historical valuation reconstruction — what investors could actually see, then.

For every historical observation date this rebuilds the multiples from the price
on that date and the statement that had already been *published* by that date.

The reporting lag is the whole point. A March 2024 annual result did not exist
in the market's hands on 1 April 2024; it arrived weeks later. Computing a P/E
for April on a statement published in May is lookahead bias, and it is the
difference between "what did investors see then" and a backtest that quietly
knows the future. Every period therefore carries an availability date, and an
observation may only use statements available on or before it.

Rows are written as point-in-time observations and never overwritten. Trends,
CAGRs and bands are computed at query time from these observations.
"""

from __future__ import annotations

import statistics
from datetime import date, datetime, timedelta
from typing import Any, Iterable, Optional

from institutional_warehouse import gateway, store, units
from institutional_warehouse.backfill import checkpoints
from institutional_warehouse.values import to_date, to_number

KIND = "valuation_history"
SOURCE = "warehouse_reconstruction"

# Indian listed companies file results well inside these windows; the defaults
# are deliberately conservative so a reconstruction never sees a number early.
ANNUAL_LAG_DAYS = 60
QUARTERLY_LAG_DAYS = 45

CADENCES = ("daily", "weekly", "monthly", "quarterly")


def _num(value: Any) -> Optional[float]:
    return to_number(value)


def _fiscal_period_end(label: str) -> Optional[date]:
    """FY24 -> 2024-03-31, FY24Q2 -> 2023-09-30 (Indian fiscal year)."""
    text = str(label or "").strip().upper().replace(" ", "")
    if not text.startswith("FY") or len(text) < 4:
        return None
    try:
        year = 2000 + int(text[2:4])
    except ValueError:
        return None
    quarter = text[4:6] if len(text) >= 6 and text[4] == "Q" else None
    if not quarter:
        return date(year, 3, 31)
    ends = {"Q1": (year - 1, 6, 30), "Q2": (year - 1, 9, 30), "Q3": (year - 1, 12, 31),
            "Q4": (year, 3, 31)}
    parts = ends.get(quarter)
    return date(*parts) if parts else None


def available_from(label: str, *, quarterly: bool, lag_days: Optional[int] = None) -> Optional[str]:
    period_end = _fiscal_period_end(label)
    if not period_end:
        return None
    lag = lag_days if lag_days is not None else (QUARTERLY_LAG_DAYS if quarterly else ANNUAL_LAG_DAYS)
    return (period_end + timedelta(days=lag)).isoformat()


def _statement_timeline(symbol: str, *, lag_days: Optional[int] = None) -> list[dict[str, Any]]:
    """Statements ordered by the date they became public, not the period they cover.

    Prefer filing_date / effective_date when present (Phase 8.3 chronology),
    otherwise fall back to fiscal-label + conservative lag.
    """
    timeline: list[dict[str, Any]] = []
    for tab, key, quarterly in (("financials_annual", "fiscal_year", False),
                                ("financials_quarterly", "fiscal_period", True)):
        for row in store.all_rows(tab, entity=symbol, limit=400):
            label = str(row.get(key) or "")
            filing = to_date(row.get("filing_date") or row.get("effective_date"))
            known_at = filing or available_from(label, quarterly=quarterly, lag_days=lag_days)
            if not known_at:
                continue
            timeline.append({"known_at": known_at, "label": label, "quarterly": quarterly,
                             "row": row, "release_source": "filing_date" if filing else "lag_heuristic"})
    return sorted(timeline, key=lambda item: item["known_at"])


def _latest_known(timeline: list[dict[str, Any]], observed: str, *, quarterly: bool
                  ) -> Optional[dict[str, Any]]:
    candidate = None
    for entry in timeline:
        if entry["known_at"] > observed:
            break
        if entry["quarterly"] == quarterly:
            candidate = entry
    return candidate


def _sample(dates: list[str], cadence: str) -> list[str]:
    if cadence == "daily" or not dates:
        return dates
    keep: dict[str, str] = {}
    for value in dates:
        moment = datetime.fromisoformat(value).date()
        if cadence == "weekly":
            bucket = f"{moment.isocalendar().year}-W{moment.isocalendar().week:02d}"
        elif cadence == "quarterly":
            bucket = f"{moment.year}-Q{(moment.month - 1) // 3 + 1}"
        else:
            bucket = f"{moment.year}-{moment.month:02d}"
        keep[bucket] = value  # last observation in the bucket wins
    return sorted(keep.values())


def _ttm(rows: list[dict[str, Any]], field: str) -> Optional[float]:
    values = [_num(r.get(field)) for r in rows]
    present = [v for v in values if v is not None]
    if len(present) < 4:
        return None
    return sum(present[-4:])


def reconstruct_company(
    symbol: str,
    *,
    actor: str = "backfill",
    cadence: str = "monthly",
    lag_days: Optional[int] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit_observations: int = 2000,
) -> dict[str, Any]:
    ticker = str(symbol).upper()
    cadence = cadence if cadence in CADENCES else "monthly"

    prices = [r for r in store.all_rows("daily_market_history", entity=ticker, limit=20000)
              if to_date(r.get("date")) and _num(r.get("close"))]
    if not prices:
        checkpoints.save_checkpoint(KIND, ticker, status=checkpoints.SKIPPED,
                                    error="no_price_history")
        return {"ok": False, "symbol": ticker, "error": "no_price_history", "observations": 0}

    by_date = {to_date(r["date"]): r for r in sorted(prices, key=lambda r: str(r["date"]))}
    dates = sorted(by_date)
    if start:
        dates = [d for d in dates if d >= start]
    if end:
        dates = [d for d in dates if d <= end]
    sampled = _sample(dates, cadence)[-max(1, int(limit_observations)):]

    timeline = _statement_timeline(ticker, lag_days=lag_days)
    dividends = sorted(
        [
            {"date": to_date(r.get("action_date")), "amount": _num(r.get("dividend"))}
            for r in store.all_rows("corporate_actions", entity=ticker, limit=2000)
            if str(r.get("action_type")) == "dividend" and _num(r.get("dividend"))
        ],
        key=lambda r: str(r["date"] or ""),
    )

    # A reconstruction is only as good as the statement behind it. Count what was
    # missing so the coverage board can say "no share count, so no P/B" instead of
    # quietly publishing a blank column.
    missing = {"shares_outstanding": 0, "equity": 0, "ebitda": 0, "revenue": 0, "eps": 0}

    observations: list[dict[str, Any]] = []
    for observed in sampled:
        price_row = by_date[observed]
        close = _num(price_row.get("close"))
        if close is None:
            continue

        annual = _latest_known(timeline, observed, quarterly=False)
        quarterly = _latest_known(timeline, observed, quarterly=True)
        statement = (annual or {}).get("row") or {}
        if not statement and not quarterly:
            continue

        shares = _num(statement.get("shares_outstanding")) or _num(price_row.get("shares_outstanding"))
        market_cap = close * shares if shares else _num(price_row.get("market_cap"))

        quarters = [
            entry["row"] for entry in timeline
            if entry["quarterly"] and entry["known_at"] <= observed
        ]
        ttm_pat = _ttm(quarters, "pat")
        ttm_revenue = _ttm(quarters, "revenue")
        ttm_ebitda = _ttm(quarters, "ebitda")

        # Trailing twelve months when four quarters were public; otherwise the last
        # published annual figures. Companies that only file annually still get a
        # multiple, just a coarser one.
        # Statement aggregates are stored in INR million; price, share count and
        # market capitalisation are in rupees. Anything that crosses the two is
        # converted here so a multiple is a multiple and not a scale artefact.
        eps = (units.to_rupees(ttm_pat) / shares) if (ttm_pat is not None and shares) else None
        if eps is None:
            eps = _num(statement.get("eps"))
        if eps is None and shares:
            annual_pat = units.to_rupees(statement.get("pat"))
            eps = (annual_pat / shares) if annual_pat is not None else None
        revenue = ttm_revenue if ttm_revenue is not None else _num(statement.get("revenue"))
        ebitda = ttm_ebitda if ttm_ebitda is not None else _num(statement.get("ebitda"))
        revenue_inr = units.to_rupees(revenue)
        ebitda_inr = units.to_rupees(ebitda)

        equity = _num(statement.get("equity"))
        equity_inr = units.to_rupees(equity)
        book_value = (equity_inr / shares) if (equity_inr is not None and shares) else None
        debt = units.to_rupees(statement.get("debt"))
        cash = units.to_rupees(statement.get("cash"))
        enterprise_value = None
        if market_cap is not None:
            enterprise_value = market_cap + (debt or 0.0) - (cash or 0.0)

        for field, value in (("shares_outstanding", shares), ("equity", equity),
                             ("ebitda", ebitda), ("revenue", revenue), ("eps", eps)):
            if value is None:
                missing[field] += 1

        trailing_dividend = sum(
            d["amount"] for d in dividends
            if d["date"] and d["amount"] and
            (datetime.fromisoformat(observed) - datetime.fromisoformat(d["date"])).days <= 365
            and d["date"] <= observed
        )

        observations.append(
            {
                "date": observed,
                "symbol": ticker,
                "cmp": round(close, 4),
                "market_cap": round(market_cap, 2) if market_cap is not None else None,
                "enterprise_value": round(enterprise_value, 2) if enterprise_value is not None else None,
                "pe": round(close / eps, 4) if eps and eps > 0 else None,
                "pb": round(close / book_value, 4) if book_value and book_value > 0 else None,
                "ev_ebitda": round(enterprise_value / ebitda_inr, 4)
                if enterprise_value is not None and ebitda_inr and ebitda_inr > 0 else None,
                "ev_sales": round(enterprise_value / revenue_inr, 4)
                if enterprise_value is not None and revenue_inr and revenue_inr > 0 else None,
                "price_sales": round(market_cap / revenue_inr, 4)
                if market_cap is not None and revenue_inr and revenue_inr > 0 else None,
                "dividend_yield": round(100.0 * trailing_dividend / close, 4)
                if trailing_dividend else None,
                "source": f"{SOURCE}<-{statement.get('source') or 'unknown'}",
            }
        )

    if not observations:
        checkpoints.save_checkpoint(KIND, ticker, status=checkpoints.SKIPPED,
                                    error="no_statement_available_at_any_observation")
        return {"ok": False, "symbol": ticker, "error": "no_point_in_time_statement",
                "observations": 0}

    written = gateway.write("historical_valuation", observations, source=SOURCE, actor=actor,
                           reason=f"reconstruct:{ticker}")
    checkpoints.save_checkpoint(
        KIND, ticker, status=checkpoints.DONE, rows_written=len(observations),
        first_period=observations[0]["date"], last_period=observations[-1]["date"],
        cursor=observations[-1]["date"], reset_attempts=True,
    )
    total = len(observations)
    return {
        "ok": True,
        "symbol": ticker,
        "observations": total,
        "first": observations[0]["date"],
        "last": observations[-1]["date"],
        "cadence": cadence,
        "written": written,
        "missing_inputs": {k: v for k, v in missing.items() if v},
        "unusable": {
            "market_cap": missing["shares_outstanding"] == total,
            "pb": missing["shares_outstanding"] == total or missing["equity"] == total,
            "ev_multiples": missing["shares_outstanding"] == total,
        },
    }


def rerank_dates(dates: Iterable[str], *, actor: str = "backfill") -> dict[str, Any]:
    """Cross-sectional pass: on each date, place every company against its peers.

    Only the warehouse can do this — it needs the whole market priced on the same
    day, which is exactly what a per-company API cannot see.
    """
    masters = {
        str(r.get("symbol") or "").upper(): r
        for r in store.all_rows("company_master", limit=6000)
    }
    updated = 0
    touched: list[str] = []

    for observed in sorted({str(d) for d in dates if d}):
        rows = store.fetch("historical_valuation", filters={"date": observed}, limit=5000)["rows"]
        if len(rows) < 3:
            continue

        sectors: dict[str, list[float]] = {}
        industries: dict[str, list[float]] = {}
        for row in rows:
            pe = _num(row.get("pe"))
            if not pe or pe <= 0:
                continue
            master = masters.get(str(row.get("symbol") or "").upper()) or {}
            sectors.setdefault(str(master.get("sector") or "Unclassified"), []).append(pe)
            industries.setdefault(str(master.get("industry") or "Unclassified"), []).append(pe)

        sector_median = {k: round(statistics.median(v), 4) for k, v in sectors.items() if len(v) >= 2}
        industry_median = {k: round(statistics.median(v), 4) for k, v in industries.items() if len(v) >= 2}

        staged = []
        for row in rows:
            master = masters.get(str(row.get("symbol") or "").upper()) or {}
            sector = str(master.get("sector") or "Unclassified")
            industry = str(master.get("industry") or "Unclassified")
            pe = _num(row.get("pe"))
            pool = sectors.get(sector) or []
            percentile = None
            if pe and pe > 0 and len(pool) >= 3:
                cheaper = sum(1 for value in pool if value < pe)
                percentile = round(100.0 - (100.0 * cheaper / len(pool)), 2)
            entry = {
                "date": observed,
                "symbol": row.get("symbol"),
                "sector_median": sector_median.get(sector),
                "industry_median": industry_median.get(industry),
                "percentile": percentile,
            }
            if percentile is not None:
                entry["relative_valuation_score"] = percentile
            staged.append(entry)

        result = gateway.write("historical_valuation", staged, source=SOURCE, actor=actor,
                              reason=f"rerank:{observed}")
        updated += int(result.get("updated") or 0)
        touched.append(observed)

    return {"ok": True, "dates": len(touched), "rows_updated": updated,
            "first": touched[0] if touched else None, "last": touched[-1] if touched else None}


def reconstruct(
    universe: Optional[Iterable[str]] = None,
    *,
    actor: str = "backfill",
    limit: int = 25,
    cadence: str = "monthly",
    lag_days: Optional[int] = None,
    rerank: bool = True,
    refresh_done: bool = False,
) -> dict[str, Any]:
    names = list(universe) if universe is not None else store.entities("daily_market_history")
    pending = checkpoints.pending_entities(KIND, names, limit=limit, refresh_done=refresh_done)

    done: list[str] = []
    skipped: list[dict[str, Any]] = []
    observations = 0
    dates: set[str] = set()
    gaps: dict[str, int] = {}
    no_share_count: list[str] = []

    for ticker in pending:
        result = reconstruct_company(ticker, actor=actor, cadence=cadence, lag_days=lag_days)
        if not result.get("ok"):
            skipped.append({"symbol": ticker, "reason": result.get("error")})
            continue
        done.append(ticker)
        observations += int(result.get("observations") or 0)
        dates.add(result["first"])
        dates.add(result["last"])
        for field, count in (result.get("missing_inputs") or {}).items():
            gaps[field] = gaps.get(field, 0) + count
        if (result.get("unusable") or {}).get("market_cap"):
            no_share_count.append(ticker)

    ranked = None
    if rerank and done:
        recent = sorted(
            {
                str(r["date"])
                for r in store.fetch("historical_valuation", sort="date", order="desc",
                                     limit=4000)["rows"]
            }
        )[-240:]
        ranked = rerank_dates(recent, actor=actor)

    return {
        "ok": True,
        "kind": KIND,
        "queued": len(pending),
        "companies_done": len(done),
        "companies_skipped": len(skipped),
        "observations": observations,
        "cadence": cadence,
        "reranked": ranked,
        "skipped": skipped[:20],
        "missing_inputs": gaps,
        "companies_without_share_count": no_share_count[:50],
        "coverage": checkpoints.entity_coverage(KIND),
    }
