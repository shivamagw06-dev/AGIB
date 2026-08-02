"""Server-side formula engine.

There are no spreadsheet formulas in the warehouse. Derived values are computed
here, on the server, from the effective rows (imported values with admin
overrides applied) and written back into the computed tabs.

    ROE            = PAT / Average Equity
    Market Cap     = CMP x Shares Outstanding
    Free Cash Flow = CFO - Capex
    Upside         = (Target Price - CMP) / CMP
    Relative Score = weighted sector percentile + consensus + profitability
"""

from __future__ import annotations

import statistics
from typing import Any, Iterable, Optional

from institutional_warehouse import audit, store
from institutional_warehouse.values import now_iso, today_iso

SOURCE = "formula_engine"


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------


def _num(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if out != out:  # NaN
        return None
    return out


def _div(numerator: Any, denominator: Any, *, scale: float = 1.0) -> Optional[float]:
    a, b = _num(numerator), _num(denominator)
    if a is None or b in (None, 0):
        return None
    return round((a / b) * scale, 6)


def _pct(numerator: Any, denominator: Any) -> Optional[float]:
    return _div(numerator, denominator, scale=100.0)


def _avg(*values: Any) -> Optional[float]:
    nums = [v for v in (_num(x) for x in values) if v is not None]
    if not nums:
        return None
    return sum(nums) / len(nums)


def _iter_rows(tab_id: str, *, page: int = 2000, entity: Optional[str] = None) -> Iterable[dict[str, Any]]:
    offset = 0
    while True:
        result = store.fetch(tab_id, limit=page, offset=offset, entity=entity)
        rows = result.get("rows") or []
        if not rows:
            return
        for row in rows:
            yield row
        offset += len(rows)
        if offset >= int(result.get("total") or 0):
            return


def _by_entity(tab_id: str, *, entity: Optional[str] = None) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in _iter_rows(tab_id, entity=entity):
        symbol = str(row.get("symbol") or "").upper()
        if not symbol:
            continue
        grouped.setdefault(symbol, []).append(row)
    return grouped


def _percentile_rank(value: Optional[float], population: list[float], *, lower_is_better: bool = True) -> Optional[float]:
    val = _num(value)
    pool = [p for p in population if p is not None and p > 0]
    if val is None or len(pool) < 3:
        return None
    below = sum(1 for p in pool if p < val)
    rank = 100.0 * below / len(pool)
    return round(100.0 - rank if lower_is_better else rank, 2)


def _clamp(value: Optional[float], low: float = 0.0, high: float = 100.0) -> Optional[float]:
    if value is None:
        return None
    return round(max(low, min(high, value)), 2)


# --------------------------------------------------------------------------
# 1. Derived columns inside the base tabs
# --------------------------------------------------------------------------


def recalc_statement_derivations(*, actor: str = "system", entity: Optional[str] = None) -> dict[str, Any]:
    """free_cash_flow = CFO - Capex, book_value = Equity / Shares."""
    counts = {}
    for tab_id, key in (("financials_annual", "fiscal_year"), ("financials_quarterly", "fiscal_period")):
        updates = []
        for row in _iter_rows(tab_id, entity=entity):
            cfo, capex = _num(row.get("cfo")), _num(row.get("capex"))
            fcf = None
            if cfo is not None:
                fcf = round(cfo - abs(capex), 6) if capex is not None else round(cfo, 6)
            book = _div(row.get("equity"), row.get("shares_outstanding"))
            if fcf is None and book is None:
                continue
            updates.append(
                {
                    "symbol": row.get("symbol"),
                    key: row.get(key),
                    "free_cash_flow": fcf,
                    "book_value": book,
                }
            )
        counts[tab_id] = store.upsert(tab_id, updates, source=SOURCE, actor=actor,
                                      reason="derive_statement_columns")
    return counts


def recalc_market_derivations(*, actor: str = "system", entity: Optional[str] = None) -> dict[str, Any]:
    """market_cap = Close x Shares Outstanding, using the statement share count as fallback."""
    shares_fallback: dict[str, float] = {}
    for symbol, rows in _by_entity("financials_annual", entity=entity).items():
        for row in sorted(rows, key=lambda r: str(r.get("fiscal_year") or ""), reverse=True):
            value = _num(row.get("shares_outstanding"))
            if value:
                shares_fallback[symbol] = value
                break

    updates = []
    for row in _iter_rows("daily_market_history", entity=entity):
        symbol = str(row.get("symbol") or "").upper()
        shares = _num(row.get("shares_outstanding")) or shares_fallback.get(symbol)
        close = _num(row.get("close")) or _num(row.get("adjusted_close"))
        if shares is None or close is None:
            continue
        updates.append(
            {
                "symbol": symbol,
                "date": row.get("date"),
                "shares_outstanding": shares,
                "market_cap": round(close * shares, 2),
            }
        )
    return store.upsert("daily_market_history", updates, source=SOURCE, actor=actor,
                        reason="derive_market_cap")


def recalc_consensus_derivations(*, actor: str = "system", entity: Optional[str] = None) -> dict[str, Any]:
    updates = []
    for row in _iter_rows("consensus", entity=entity):
        buckets = [row.get("buy"), row.get("outperform"), row.get("hold"), row.get("sell"), row.get("no_opinion")]
        counted = [int(v) for v in (_num(b) for b in buckets) if v is not None]
        analysts = sum(counted) if counted else None
        high, low, target = _num(row.get("high_target")), _num(row.get("low_target")), _num(row.get("target_price"))
        dispersion = None
        if high is not None and low is not None and target:
            dispersion = round(100.0 * (high - low) / target, 4)
        if analysts is None and dispersion is None:
            continue
        updates.append(
            {
                "symbol": row.get("symbol"),
                "consensus_date": row.get("consensus_date"),
                "analyst_count": analysts,
                "target_dispersion": dispersion,
            }
        )
    return store.upsert("consensus", updates, source=SOURCE, actor=actor, reason="derive_consensus")


# --------------------------------------------------------------------------
# 2. Historical ratios
# --------------------------------------------------------------------------


def _ratio_row(symbol: str, period: str, basis: str, current: dict[str, Any],
               previous: Optional[dict[str, Any]]) -> dict[str, Any]:
    equity_avg = _avg(current.get("equity"), (previous or {}).get("equity")) or _num(current.get("equity"))
    assets_avg = _avg(current.get("assets"), (previous or {}).get("assets")) or _num(current.get("assets"))
    debt = _num(current.get("debt"))
    equity = _num(current.get("equity"))
    capital_employed = None
    if equity is not None:
        capital_employed = equity + (debt or 0.0)
    revenue = _num(current.get("revenue"))
    ebit = _num(current.get("ebit"))
    interest = None
    pbt, ebit_val = _num(current.get("pbt")), ebit
    if pbt is not None and ebit_val is not None:
        interest = ebit_val - pbt
    current_assets = _num(current.get("current_assets"))
    current_liabilities = _num(current.get("current_liabilities"))
    inventory = _num(current.get("inventory"))
    quick_assets = None
    if current_assets is not None:
        quick_assets = current_assets - (inventory or 0.0)

    fcf = _num(current.get("free_cash_flow"))
    if fcf is None:
        cfo, capex = _num(current.get("cfo")), _num(current.get("capex"))
        if cfo is not None:
            fcf = cfo - abs(capex or 0.0)

    return {
        "symbol": symbol,
        "period": period,
        "basis": basis,
        "roe": _pct(current.get("pat"), equity_avg),
        "roce": _pct(ebit, capital_employed),
        "roa": _pct(current.get("pat"), assets_avg),
        "gross_margin": _pct(current.get("gross_profit"), revenue),
        "ebitda_margin": _pct(current.get("ebitda"), revenue),
        "operating_margin": _pct(ebit, revenue),
        "net_margin": _pct(current.get("pat"), revenue),
        "asset_turnover": _div(revenue, assets_avg),
        "debt_equity": _div(debt, equity),
        "interest_coverage": _div(ebit, interest) if interest and interest > 0 else None,
        "current_ratio": _div(current_assets, current_liabilities),
        "quick_ratio": _div(quick_assets, current_liabilities),
        "fcf_margin": _pct(fcf, revenue),
        "source": SOURCE,
    }


def recalc_ratios(*, actor: str = "system", entity: Optional[str] = None) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for tab_id, key, basis in (
        ("financials_annual", "fiscal_year", "annual"),
        ("financials_quarterly", "fiscal_period", "quarterly"),
    ):
        for symbol, statements in _by_entity(tab_id, entity=entity).items():
            ordered = sorted(statements, key=lambda r: str(r.get(key) or ""))
            for idx, current in enumerate(ordered):
                period = str(current.get(key) or "").strip()
                if not period:
                    continue
                previous = ordered[idx - 1] if idx else None
                rows.append(_ratio_row(symbol, period, basis, current, previous))
    return store.upsert("historical_ratios", rows, source=SOURCE, actor=actor, reason="recalc_ratios")


# --------------------------------------------------------------------------
# 3. Historical valuation
# --------------------------------------------------------------------------


def _latest(rows: list[dict[str, Any]], key: str) -> Optional[dict[str, Any]]:
    ordered = [r for r in rows if r.get(key)]
    if not ordered:
        return None
    return sorted(ordered, key=lambda r: str(r.get(key)), reverse=True)[0]


def recalc_valuation(*, actor: str = "system", as_of: Optional[str] = None,
                     entity: Optional[str] = None) -> dict[str, Any]:
    stamp = as_of or today_iso()
    market = _by_entity("daily_market_history", entity=entity)
    annual = _by_entity("financials_annual", entity=entity)
    consensus = _by_entity("consensus", entity=entity)
    ratios = _by_entity("historical_ratios", entity=entity)
    masters = {str(r.get("symbol") or "").upper(): r for r in _iter_rows("company_master", entity=entity)}

    staged: dict[str, dict[str, Any]] = {}
    for symbol, prices in market.items():
        latest_price = _latest(prices, "date")
        if not latest_price:
            continue
        cmp_price = _num(latest_price.get("close")) or _num(latest_price.get("adjusted_close"))
        if cmp_price is None:
            continue
        statement = _latest(annual.get(symbol, []), "fiscal_year") or {}
        broker = _latest(consensus.get(symbol, []), "consensus_date") or {}

        shares = _num(latest_price.get("shares_outstanding")) or _num(statement.get("shares_outstanding"))
        market_cap = _num(latest_price.get("market_cap"))
        if market_cap is None and shares:
            market_cap = cmp_price * shares
        debt, cash = _num(statement.get("debt")), _num(statement.get("cash"))
        enterprise_value = None
        if market_cap is not None:
            enterprise_value = market_cap + (debt or 0.0) - (cash or 0.0)

        eps = _num(statement.get("eps"))
        if eps is None and shares:
            eps = _div(statement.get("pat"), shares)
        book_value = _num(statement.get("book_value")) or _div(statement.get("equity"), shares)

        pe = _div(cmp_price, eps) if eps and eps > 0 else None
        pb = _div(cmp_price, book_value) if book_value and book_value > 0 else None
        ev_ebitda = _div(enterprise_value, statement.get("ebitda"))
        ev_sales = _div(enterprise_value, statement.get("revenue"))
        price_sales = _div(market_cap, statement.get("revenue"))
        dividend = _num(latest_price.get("dividend"))
        dividend_yield = _pct(dividend, cmp_price) if dividend else None
        target = _num(broker.get("target_price"))
        upside = round(100.0 * (target - cmp_price) / cmp_price, 3) if target and cmp_price else None

        staged[symbol] = {
            "date": stamp,
            "symbol": symbol,
            "cmp": round(cmp_price, 4),
            "market_cap": round(market_cap, 2) if market_cap is not None else None,
            "enterprise_value": round(enterprise_value, 2) if enterprise_value is not None else None,
            "pe": pe,
            "pb": pb,
            "ev_ebitda": ev_ebitda,
            "ev_sales": ev_sales,
            "price_sales": price_sales,
            "dividend_yield": dividend_yield,
            "upside": upside,
            "source": SOURCE,
            "_sector": str((masters.get(symbol) or {}).get("sector") or "").strip() or "Unclassified",
            "_industry": str((masters.get(symbol) or {}).get("industry") or "").strip() or "Unclassified",
        }

    # growth for PEG, from annual earnings history
    for symbol, row in staged.items():
        history = sorted(annual.get(symbol, []), key=lambda r: str(r.get("fiscal_year") or ""))
        eps_series = [_num(r.get("eps")) for r in history if _num(r.get("eps")) is not None]
        growth = None
        if len(eps_series) >= 2 and eps_series[0] and eps_series[0] > 0 and eps_series[-1] > 0:
            years = max(len(eps_series) - 1, 1)
            growth = ((eps_series[-1] / eps_series[0]) ** (1.0 / years) - 1.0) * 100.0
        if growth and growth > 0 and row.get("pe"):
            row["peg"] = round(row["pe"] / growth, 4)
        row["_growth"] = round(growth, 3) if growth is not None else None

    # sector / industry medians and percentiles
    def _medians(group_key: str) -> dict[str, float]:
        buckets: dict[str, list[float]] = {}
        for row in staged.values():
            pe = _num(row.get("pe"))
            if pe and pe > 0:
                buckets.setdefault(row[group_key], []).append(pe)
        return {k: round(statistics.median(v), 4) for k, v in buckets.items() if len(v) >= 2}

    sector_medians = _medians("_sector")
    industry_medians = _medians("_industry")
    sector_pools: dict[str, list[float]] = {}
    for row in staged.values():
        pe = _num(row.get("pe"))
        if pe and pe > 0:
            sector_pools.setdefault(row["_sector"], []).append(pe)

    output = []
    for symbol, row in staged.items():
        sector, industry = row.pop("_sector"), row.pop("_industry")
        growth = row.pop("_growth", None)
        row["sector_median"] = sector_medians.get(sector)
        row["industry_median"] = industry_medians.get(industry)
        row["percentile"] = _percentile_rank(row.get("pe"), sector_pools.get(sector, []), lower_is_better=True)

        cheapness = row.get("percentile")
        upside = _num(row.get("upside"))
        consensus_component = _clamp(50.0 + (upside or 0.0) / 2.0) if upside is not None else None
        annual_ratios = [
            r for r in ratios.get(symbol, [])
            if r.get("basis") == "annual" and _num(r.get("roe")) is not None
        ]
        roe = None
        if annual_ratios:
            latest_ratio = sorted(annual_ratios, key=lambda r: str(r.get("period")))[-1]
            roe = _num(latest_ratio.get("roe"))
        profitability = _clamp((roe or 0.0) * 2.5) if roe is not None else None

        weights = [(cheapness, 0.5), (consensus_component, 0.25), (profitability, 0.25)]
        available = [(v, w) for v, w in weights if v is not None]
        if available:
            total_weight = sum(w for _, w in available)
            row["relative_valuation_score"] = round(sum(v * w for v, w in available) / total_weight, 2)
        row["beta"] = _beta_from_history(market.get(symbol, []))
        if growth is not None and row.get("pe") and growth > 0:
            row.setdefault("peg", round(row["pe"] / growth, 4))
        output.append(row)

    result = store.upsert("historical_valuation", output, source=SOURCE, actor=actor,
                          reason="recalc_valuation")
    result["as_of"] = stamp
    return result


def _beta_from_history(prices: list[dict[str, Any]]) -> Optional[float]:
    closes = [
        _num(p.get("close"))
        for p in sorted(prices, key=lambda r: str(r.get("date") or ""))
        if _num(p.get("close")) is not None
    ]
    if len(closes) < 30:
        return None
    returns = [
        (closes[i] - closes[i - 1]) / closes[i - 1]
        for i in range(1, len(closes))
        if closes[i - 1]
    ]
    if len(returns) < 20:
        return None
    try:
        vol = statistics.pstdev(returns)
    except statistics.StatisticsError:
        return None
    # Market-relative beta needs an index series; until one is warehoused we report
    # normalised volatility against a 1.2% daily reference so the column is honest.
    return round(vol / 0.012, 3) if vol else None


# --------------------------------------------------------------------------
# 4. Hedge fund factors
# --------------------------------------------------------------------------


def recalc_factors(*, actor: str = "system", as_of: Optional[str] = None,
                   entity: Optional[str] = None) -> dict[str, Any]:
    stamp = as_of or today_iso()
    valuation = {str(r.get("symbol")).upper(): r for r in _iter_rows("historical_valuation", entity=entity)}
    ratios = _by_entity("historical_ratios", entity=entity)
    consensus = _by_entity("consensus", entity=entity)
    market = _by_entity("daily_market_history", entity=entity)

    rows = []
    for symbol, val in valuation.items():
        annual_ratios = sorted(
            [r for r in ratios.get(symbol, []) if r.get("basis") == "annual"],
            key=lambda r: str(r.get("period") or ""),
        )
        latest_ratio = annual_ratios[-1] if annual_ratios else {}
        broker = _latest(consensus.get(symbol, []), "consensus_date") or {}

        value_score = _clamp(_num(val.get("percentile")))
        roe = _num(latest_ratio.get("roe"))
        debt_equity = _num(latest_ratio.get("debt_equity"))
        quality_bits = []
        if roe is not None:
            quality_bits.append(_clamp(roe * 2.5))
        if debt_equity is not None:
            quality_bits.append(_clamp(100.0 - min(debt_equity, 3.0) * 33.0))
        margin = _num(latest_ratio.get("net_margin"))
        if margin is not None:
            quality_bits.append(_clamp(margin * 3.0))
        quality_score = round(sum(quality_bits) / len(quality_bits), 2) if quality_bits else None

        growth_score = None
        if len(annual_ratios) >= 2:
            first, last = annual_ratios[0], annual_ratios[-1]
            delta = None
            if _num(last.get("net_margin")) is not None and _num(first.get("net_margin")) is not None:
                delta = _num(last["net_margin"]) - _num(first["net_margin"])
            if delta is not None:
                growth_score = _clamp(50.0 + delta * 5.0)

        momentum_score = _momentum(market.get(symbol, []))
        upside = _num(val.get("upside"))
        consensus_score = _clamp(50.0 + (upside or 0.0) / 2.0) if upside is not None else None
        dividend_yield = _num(val.get("dividend_yield"))
        dividend_score = _clamp((dividend_yield or 0.0) * 20.0) if dividend_yield is not None else None
        beta = _num(val.get("beta"))
        risk_score = _clamp(100.0 - (beta or 1.0) * 40.0) if beta is not None else None

        components = [
            (value_score, 0.3),
            (quality_score, 0.25),
            (growth_score, 0.15),
            (momentum_score, 0.15),
            (consensus_score, 0.15),
        ]
        available = [(v, w) for v, w in components if v is not None]
        opportunity = None
        if available:
            weight = sum(w for _, w in available)
            opportunity = round(sum(v * w for v, w in available) / weight, 2)
        agreement = sum(1 for v, _ in components if v is not None and v >= 60.0)

        rows.append(
            {
                "symbol": symbol,
                "as_of": stamp,
                "value_score": value_score,
                "quality_score": quality_score,
                "growth_score": growth_score,
                "momentum_score": momentum_score,
                "consensus_score": consensus_score,
                "dividend_score": dividend_score,
                "risk_score": risk_score,
                "opportunity_score": opportunity,
                "strategy_agreement": agreement,
                "source": SOURCE,
            }
        )
    return store.upsert("hedge_fund_factors", rows, source=SOURCE, actor=actor, reason="recalc_factors")


def _momentum(prices: list[dict[str, Any]]) -> Optional[float]:
    ordered = sorted(
        [p for p in prices if _num(p.get("close")) is not None],
        key=lambda r: str(r.get("date") or ""),
    )
    if len(ordered) < 2:
        return None
    first, last = _num(ordered[0]["close"]), _num(ordered[-1]["close"])
    if not first:
        return None
    change = 100.0 * (last - first) / first
    return _clamp(50.0 + change / 2.0)


# --------------------------------------------------------------------------
# 5. Data quality board
# --------------------------------------------------------------------------


def recalc_quality(*, actor: str = "system") -> dict[str, Any]:
    from institutional_warehouse.schema import TABS
    from institutional_warehouse.validation import validate_tab

    rows = []
    for tab in TABS:
        if tab.id == "data_quality":
            continue
        stats = store.tab_stats(tab.id)
        report = validate_tab(tab.id, sample=500)
        missing = report.get("missing_values", 0)
        cells = report.get("checked_cells", 0) or 1
        rows.append(
            {
                "table_id": tab.id,
                "rows": stats.get("rows"),
                "companies": stats.get("companies"),
                "missing_values": missing,
                "missing_pct": round(100.0 * missing / cells, 2),
                "last_refresh": stats.get("last_updated"),
                "errors": len(report.get("errors") or []),
                "validation_status": report.get("status"),
                "freshness": report.get("freshness"),
                "source": SOURCE,
            }
        )
    return store.upsert("data_quality", rows, source=SOURCE, actor=actor, reason="recalc_quality")


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------

STAGES = (
    "statement_derivations",
    "market_derivations",
    "consensus_derivations",
    "ratios",
    "valuation",
    "factors",
    "quality",
)


def recalculate(
    *,
    actor: str = "system",
    stages: Optional[Iterable[str]] = None,
    entity: Optional[str] = None,
    as_of: Optional[str] = None,
) -> dict[str, Any]:
    wanted = [s for s in (stages or STAGES) if s in STAGES]
    started = now_iso()
    out: dict[str, Any] = {}
    errors: list[dict[str, str]] = []

    runners = {
        "statement_derivations": lambda: recalc_statement_derivations(actor=actor, entity=entity),
        "market_derivations": lambda: recalc_market_derivations(actor=actor, entity=entity),
        "consensus_derivations": lambda: recalc_consensus_derivations(actor=actor, entity=entity),
        "ratios": lambda: recalc_ratios(actor=actor, entity=entity),
        "valuation": lambda: recalc_valuation(actor=actor, as_of=as_of, entity=entity),
        "factors": lambda: recalc_factors(actor=actor, as_of=as_of, entity=entity),
        "quality": lambda: recalc_quality(actor=actor),
    }
    for stage in wanted:
        try:
            out[stage] = runners[stage]()
        except Exception as exc:  # keep going: one bad stage must not stall the rest
            errors.append({"stage": stage, "error": str(exc)})
            out[stage] = {"ok": False, "error": str(exc)}

    audit.record("recalculate", actor=actor, detail={"stages": wanted, "errors": errors},
                 ok=not errors)
    return {
        "ok": not errors,
        "started_at": started,
        "finished_at": now_iso(),
        "stages": out,
        "errors": errors,
    }
