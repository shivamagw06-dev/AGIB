"""Map Yahoo Finance payloads → AGI canonical models only (never expose Yahoo-native schemas)."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from typing import Any

from app.market_data.models import (
    CalendarEvent,
    CorporateAction,
    FundamentalSnapshot,
    MarketDataQuote,
    OHLCVBar,
    OHLCVSeries,
    OptionChain,
    OptionContract,
    Provenance,
)
from app.market_data.providers.yahoo_symbols import from_yahoo_symbol


def _num(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, dict):
        # Yahoo quoteSummary often wraps as {"raw": x, "fmt": "..."}
        if "raw" in value:
            return _num(value.get("raw"))
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, dict):
        if value.get("fmt") is not None:
            return str(value.get("fmt"))
        if value.get("raw") is not None:
            return str(value.get("raw"))
        return None
    s = str(value).strip()
    return s or None


def _json_metric(obj: Any) -> str | None:
    if obj is None:
        return None
    try:
        return json.dumps(obj, default=str)[:12000]
    except Exception:
        return None


def map_quote_from_chart(payload: dict[str, Any], *, symbol: str, provenance: Provenance) -> MarketDataQuote:
    chart = ((payload.get("chart") or {}).get("result") or [None])[0] or {}
    meta = chart.get("meta") or {}
    indicators = ((chart.get("indicators") or {}).get("quote") or [{}])[0] or {}
    closes = indicators.get("close") or []
    opens = indicators.get("open") or []
    highs = indicators.get("high") or []
    lows = indicators.get("low") or []
    volumes = indicators.get("volume") or []
    last = _num(meta.get("regularMarketPrice")) or (_num(closes[-1]) if closes else None)
    prev = _num(meta.get("chartPreviousClose") or meta.get("previousClose"))
    change = None
    change_pct = None
    if last is not None and prev not in (None, 0):
        change = last - prev
        change_pct = (change / prev) * 100.0
    return MarketDataQuote(
        symbol=from_yahoo_symbol(str(meta.get("symbol") or symbol)),
        exchange=_str(meta.get("exchangeName") or meta.get("fullExchangeName")),
        currency=_str(meta.get("currency")),
        last=last,
        open=_num(opens[-1]) if opens else _num(meta.get("regularMarketOpen")),
        high=_num(highs[-1]) if highs else _num(meta.get("regularMarketDayHigh")),
        low=_num(lows[-1]) if lows else _num(meta.get("regularMarketDayLow")),
        previous_close=prev,
        volume=_num(volumes[-1]) if volumes else _num(meta.get("regularMarketVolume")),
        change=change,
        change_percent=change_pct,
        session_date=date.today(),
        provenance=provenance,
    )


def map_fundamentals_from_chart_meta(
    payload: dict[str, Any],
    *,
    symbol: str,
    provenance: Provenance,
) -> FundamentalSnapshot:
    """Crumb-free fallback: chart meta → canonical fundamentals/metrics subset."""
    chart = ((payload.get("chart") or {}).get("result") or [None])[0] or {}
    meta = chart.get("meta") or {}
    canon = from_yahoo_symbol(str(meta.get("symbol") or symbol))
    metrics: dict[str, float | int | str | None] = {
        "company_name": _str(meta.get("longName") or meta.get("shortName")),
        "ticker": canon,
        "exchange": _str(meta.get("fullExchangeName") or meta.get("exchangeName")),
        "currency": _str(meta.get("currency")),
        "fifty_two_week_high": _num(meta.get("fiftyTwoWeekHigh")),
        "fifty_two_week_low": _num(meta.get("fiftyTwoWeekLow")),
        "volume": _num(meta.get("regularMarketVolume")),
        "instrument_type": _str(meta.get("instrumentType")),
        "last_price": _num(meta.get("regularMarketPrice")),
        "previous_close": _num(meta.get("chartPreviousClose")),
        "day_high": _num(meta.get("regularMarketDayHigh")),
        "day_low": _num(meta.get("regularMarketDayLow")),
        "source_module": "chart.meta",
    }
    metrics = {k: v for k, v in metrics.items() if v is not None}
    return FundamentalSnapshot(
        symbol=canon,
        as_of=date.today().isoformat(),
        currency=_str(meta.get("currency")),
        metrics=metrics,
        provenance=provenance,
    )


def map_ohlcv_from_chart(
    payload: dict[str, Any],
    *,
    symbol: str,
    interval: str,
    provenance: Provenance,
) -> OHLCVSeries:
    chart = ((payload.get("chart") or {}).get("result") or [None])[0] or {}
    meta = chart.get("meta") or {}
    timestamps = chart.get("timestamp") or []
    quote = ((chart.get("indicators") or {}).get("quote") or [{}])[0] or {}
    bars: list[OHLCVBar] = []
    for i, ts in enumerate(timestamps):
        o = _num((quote.get("open") or [None])[i] if i < len(quote.get("open") or []) else None)
        h = _num((quote.get("high") or [None])[i] if i < len(quote.get("high") or []) else None)
        l = _num((quote.get("low") or [None])[i] if i < len(quote.get("low") or []) else None)
        c = _num((quote.get("close") or [None])[i] if i < len(quote.get("close") or []) else None)
        v = _num((quote.get("volume") or [None])[i] if i < len(quote.get("volume") or []) else None)
        if None in (o, h, l, c):
            continue
        bars.append(
            OHLCVBar(
                ts=datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat(),
                open=float(o),
                high=float(h),
                low=float(l),
                close=float(c),
                volume=v,
            )
        )
    return OHLCVSeries(
        symbol=from_yahoo_symbol(str(meta.get("symbol") or symbol)),
        interval=interval,
        bars=bars,
        provenance=provenance,
    )


def map_corporate_actions_from_chart(payload: dict[str, Any], *, symbol: str, provenance: Provenance) -> list[CorporateAction]:
    chart = ((payload.get("chart") or {}).get("result") or [None])[0] or {}
    events = chart.get("events") or {}
    out: list[CorporateAction] = []
    canon = from_yahoo_symbol(symbol)
    for ts, row in (events.get("dividends") or {}).items():
        if not isinstance(row, dict):
            continue
        out.append(
            CorporateAction(
                symbol=canon,
                action_type="dividend",
                ex_date=datetime.fromtimestamp(int(row.get("date") or ts), tz=timezone.utc).date().isoformat(),
                amount=_num(row.get("amount")),
                currency=None,
                details={"source_module": "chart.events.dividends"},
                provenance=provenance,
            )
        )
    for ts, row in (events.get("splits") or {}).items():
        if not isinstance(row, dict):
            continue
        numer = _num(row.get("numerator"))
        denom = _num(row.get("denominator"))
        ratio = (numer / denom) if numer and denom else None
        out.append(
            CorporateAction(
                symbol=canon,
                action_type="split",
                ex_date=datetime.fromtimestamp(int(row.get("date") or ts), tz=timezone.utc).date().isoformat(),
                ratio=ratio,
                details={
                    "numerator": numer,
                    "denominator": denom,
                    "source_module": "chart.events.splits",
                },
                provenance=provenance,
            )
        )
    return out


def map_fundamentals_from_quote_summary(
    payload: dict[str, Any],
    *,
    symbol: str,
    provenance: Provenance,
    modules_enabled: set[str] | None = None,
) -> FundamentalSnapshot:
    """Flatten Yahoo quoteSummary modules into FundamentalSnapshot.metrics (canonical only)."""
    result = ((payload.get("quoteSummary") or {}).get("result") or [None])[0] or {}
    enabled = modules_enabled or set(result.keys())
    metrics: dict[str, float | int | str | None] = {}
    canon = from_yahoo_symbol(symbol)
    currency = None

    if "assetProfile" in enabled and isinstance(result.get("assetProfile"), dict):
        ap = result["assetProfile"]
        metrics.update(
            {
                "sector": _str(ap.get("sector")),
                "industry": _str(ap.get("industry")),
                "business_summary": _str(ap.get("longBusinessSummary")),
                "employees": _num(ap.get("fullTimeEmployees")),
                "website": _str(ap.get("website")),
                "country": _str(ap.get("country")),
                "phone": _str(ap.get("phone")),
                "city": _str(ap.get("city")),
                "state": _str(ap.get("state")),
                "address": _str(ap.get("address1")),
            }
        )
        officers = ap.get("companyOfficers") or []
        if officers:
            metrics["officers_json"] = _json_metric(
                [
                    {
                        "name": o.get("name"),
                        "title": o.get("title"),
                        "age": o.get("age"),
                    }
                    for o in officers[:20]
                    if isinstance(o, dict)
                ]
            )
            for o in officers[:8]:
                if not isinstance(o, dict):
                    continue
                title = (o.get("title") or "").lower()
                if "chief executive" in title or title.startswith("ceo"):
                    metrics["ceo"] = _str(o.get("name"))
                if "chief financial" in title or "cfo" in title:
                    metrics["cfo"] = _str(o.get("name"))

    # price / exchange from price module if present
    price = result.get("price") if isinstance(result.get("price"), dict) else {}
    if price:
        metrics["exchange"] = _str(price.get("exchangeName") or price.get("exchange"))
        metrics["market"] = _str(price.get("market"))
        currency = _str(price.get("currency")) or currency
        metrics["company_name"] = _str(price.get("longName") or price.get("shortName")) or metrics.get("company_name")
        metrics["ticker"] = from_yahoo_symbol(_str(price.get("symbol")) or symbol)

    if "summaryDetail" in enabled and isinstance(result.get("summaryDetail"), dict):
        sd = result["summaryDetail"]
        currency = _str(sd.get("currency")) or currency
        metrics.update(
            {
                "trailing_pe": _num(sd.get("trailingPE")),
                "forward_pe": _num(sd.get("forwardPE")),
                "dividend_yield": _num(sd.get("dividendYield")),
                "market_cap": _num(sd.get("marketCap")),
                "enterprise_value_summary": _num(sd.get("enterpriseValue")),
                "price_to_sales": _num(sd.get("priceToSalesTrailing12Months")),
                "price_to_book_summary": _num(sd.get("priceToBook")),
                "fifty_two_week_high": _num(sd.get("fiftyTwoWeekHigh")),
                "fifty_two_week_low": _num(sd.get("fiftyTwoWeekLow")),
                "average_volume": _num(sd.get("averageVolume")),
                "volume": _num(sd.get("volume")),
                "beta_summary": _num(sd.get("beta")),
            }
        )

    if "defaultKeyStatistics" in enabled and isinstance(result.get("defaultKeyStatistics"), dict):
        ks = result["defaultKeyStatistics"]
        metrics.update(
            {
                "pe": _num(ks.get("forwardPE") or ks.get("trailingPE")),
                "forward_pe_ks": _num(ks.get("forwardPE")),
                "peg": _num(ks.get("pegRatio")),
                "enterprise_value": _num(ks.get("enterpriseValue")),
                "ev_ebitda": _num(ks.get("enterpriseToEbitda")),
                "beta": _num(ks.get("beta")),
                "float_shares": _num(ks.get("floatShares")),
                "shares_outstanding": _num(ks.get("sharesOutstanding")),
                "book_value": _num(ks.get("bookValue")),
                "price_to_book": _num(ks.get("priceToBook")),
                "short_ratio": _num(ks.get("shortRatio")),
            }
        )

    if "financialData" in enabled and isinstance(result.get("financialData"), dict):
        fd = result["financialData"]
        currency = _str(fd.get("financialCurrency")) or currency
        metrics.update(
            {
                "roe": _num(fd.get("returnOnEquity")),
                "roa": _num(fd.get("returnOnAssets")),
                "ebitda": _num(fd.get("ebitda")),
                "revenue": _num(fd.get("totalRevenue")),
                "revenue_growth": _num(fd.get("revenueGrowth")),
                "profit_margin": _num(fd.get("profitMargins")),
                "gross_margin": _num(fd.get("grossMargins")),
                "operating_margin": _num(fd.get("operatingMargins")),
                "total_debt": _num(fd.get("totalDebt")),
                "total_cash": _num(fd.get("totalCash")),
                "current_ratio": _num(fd.get("currentRatio")),
                "quick_ratio": _num(fd.get("quickRatio")),
                "free_cash_flow": _num(fd.get("freeCashflow")),
                "target_mean_price": _num(fd.get("targetMeanPrice")),
                "recommendation_key": _str(fd.get("recommendationKey")),
                "number_of_analyst_opinions": _num(fd.get("numberOfAnalystOpinions")),
            }
        )

    for key, metric_name in (
        ("incomeStatementHistory", "income_statement_annual_json"),
        ("incomeStatementHistoryQuarterly", "income_statement_quarterly_json"),
        ("balanceSheetHistory", "balance_sheet_annual_json"),
        ("balanceSheetHistoryQuarterly", "balance_sheet_quarterly_json"),
        ("cashflowStatementHistory", "cashflow_annual_json"),
        ("cashflowStatementHistoryQuarterly", "cashflow_quarterly_json"),
    ):
        if key in enabled and isinstance(result.get(key), dict):
            statements = result[key].get("incomeStatementHistory") or result[key].get("balanceSheetStatements") or result[key].get("cashflowStatements")
            # Yahoo structure varies by module key
            if statements is None:
                for v in result[key].values():
                    if isinstance(v, list):
                        statements = v
                        break
            metrics[metric_name] = _json_metric(_simplify_statements(statements or []))

    if "earnings" in enabled and isinstance(result.get("earnings"), dict):
        metrics["earnings_json"] = _json_metric(result.get("earnings"))
    if "earningsHistory" in enabled and isinstance(result.get("earningsHistory"), dict):
        metrics["earnings_history_json"] = _json_metric(result.get("earningsHistory"))
    if "earningsTrend" in enabled and isinstance(result.get("earningsTrend"), dict):
        metrics["earnings_trend_json"] = _json_metric(result.get("earningsTrend"))

    if "recommendationTrend" in enabled and isinstance(result.get("recommendationTrend"), dict):
        metrics["recommendation_trend_json"] = _json_metric(result.get("recommendationTrend"))
        trend = (result["recommendationTrend"].get("trend") or [None])[0] or {}
        if isinstance(trend, dict):
            metrics["rec_strong_buy"] = _num(trend.get("strongBuy"))
            metrics["rec_buy"] = _num(trend.get("buy"))
            metrics["rec_hold"] = _num(trend.get("hold"))
            metrics["rec_sell"] = _num(trend.get("sell"))
            metrics["rec_strong_sell"] = _num(trend.get("strongSell"))

    if "upgradeDowngradeHistory" in enabled and isinstance(result.get("upgradeDowngradeHistory"), dict):
        metrics["upgrade_downgrade_json"] = _json_metric(result.get("upgradeDowngradeHistory"))

    if "institutionOwnership" in enabled and isinstance(result.get("institutionOwnership"), dict):
        metrics["institution_ownership_json"] = _json_metric(result.get("institutionOwnership"))
    if "fundOwnership" in enabled and isinstance(result.get("fundOwnership"), dict):
        metrics["fund_ownership_json"] = _json_metric(result.get("fundOwnership"))
    if "majorHoldersBreakdown" in enabled and isinstance(result.get("majorHoldersBreakdown"), dict):
        mhb = result["majorHoldersBreakdown"]
        metrics.update(
            {
                "insiders_percent": _num(mhb.get("insidersPercentHeld")),
                "institutions_percent": _num(mhb.get("institutionsPercentHeld")),
                "institutions_float_percent": _num(mhb.get("institutionsFloatPercentHeld")),
                "institutions_count": _num(mhb.get("institutionsCount")),
            }
        )

    if "insiderTransactions" in enabled and isinstance(result.get("insiderTransactions"), dict):
        metrics["insider_transactions_json"] = _json_metric(result.get("insiderTransactions"))
    if "insiderHolders" in enabled and isinstance(result.get("insiderHolders"), dict):
        metrics["insider_holders_json"] = _json_metric(result.get("insiderHolders"))
    if "netSharePurchaseActivity" in enabled and isinstance(result.get("netSharePurchaseActivity"), dict):
        nspa = result["netSharePurchaseActivity"]
        metrics["net_insider_buy_sell"] = _num(nspa.get("netInfoCount") or nspa.get("buyInfoShares"))
        metrics["net_share_purchase_json"] = _json_metric(nspa)

    if "secFilings" in enabled and isinstance(result.get("secFilings"), dict):
        metrics["sec_filings_json"] = _json_metric(result.get("secFilings"))

    # Drop Nones
    metrics = {k: v for k, v in metrics.items() if v is not None}
    return FundamentalSnapshot(
        symbol=canon,
        as_of=date.today().isoformat(),
        currency=currency,
        metrics=metrics,
        provenance=provenance,
    )


def map_calendar_from_quote_summary(
    payload: dict[str, Any],
    *,
    symbol: str,
    provenance: Provenance,
) -> list[CalendarEvent]:
    result = ((payload.get("quoteSummary") or {}).get("result") or [None])[0] or {}
    canon = from_yahoo_symbol(symbol)
    events: list[CalendarEvent] = []

    # Earnings chart / history
    earnings = result.get("earnings") if isinstance(result.get("earnings"), dict) else {}
    chart = earnings.get("earningsChart") if isinstance(earnings.get("earningsChart"), dict) else {}
    for row in chart.get("quarterly") or []:
        if not isinstance(row, dict):
            continue
        events.append(
            CalendarEvent(
                event_id=f"yahoo-earn-{canon}-{row.get('date')}",
                event_type="earnings",
                symbol=canon,
                title=f"{canon} earnings {row.get('date')}",
                event_time=_str(row.get("date")),
                details={
                    "actual": _num(row.get("actual")),
                    "estimate": _num(row.get("estimate")),
                },
                provenance=provenance,
            )
        )

    hist = result.get("earningsHistory") if isinstance(result.get("earningsHistory"), dict) else {}
    for row in hist.get("history") or []:
        if not isinstance(row, dict):
            continue
        period = _str(row.get("period")) or "hist"
        events.append(
            CalendarEvent(
                event_id=f"yahoo-earn-hist-{canon}-{period}",
                event_type="earnings_history",
                symbol=canon,
                title=f"{canon} EPS {period}",
                event_time=_str((row.get("quarter") or {}).get("fmt") if isinstance(row.get("quarter"), dict) else row.get("quarter")),
                details={
                    "eps_actual": _num(row.get("epsActual")),
                    "eps_estimate": _num(row.get("epsEstimate")),
                    "surprise_percent": _num(row.get("surprisePercent")),
                },
                provenance=provenance,
            )
        )

    upgrades = result.get("upgradeDowngradeHistory") if isinstance(result.get("upgradeDowngradeHistory"), dict) else {}
    for row in (upgrades.get("history") or [])[:40]:
        if not isinstance(row, dict):
            continue
        ts = row.get("epochGradeDate")
        when = datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat() if ts else None
        events.append(
            CalendarEvent(
                event_id=f"yahoo-rating-{canon}-{ts}-{row.get('firm')}",
                event_type="upgrade_downgrade",
                symbol=canon,
                title=f"{row.get('firm')}: {row.get('fromGrade')} → {row.get('toGrade')}",
                event_time=when,
                details={
                    "firm": row.get("firm"),
                    "from_grade": row.get("fromGrade"),
                    "to_grade": row.get("toGrade"),
                    "action": row.get("action"),
                },
                provenance=provenance,
            )
        )

    filings = result.get("secFilings") if isinstance(result.get("secFilings"), dict) else {}
    for row in (filings.get("filings") or [])[:40]:
        if not isinstance(row, dict):
            continue
        events.append(
            CalendarEvent(
                event_id=f"yahoo-sec-{canon}-{row.get('date')}-{row.get('type')}",
                event_type="sec_filing",
                symbol=canon,
                title=f"{row.get('type')} — {row.get('title') or row.get('edgarUrl')}",
                event_time=_str(row.get("date")),
                country="US",
                details={"url": row.get("edgarUrl"), "filing_type": row.get("type")},
                provenance=provenance,
            )
        )
    return events


def map_option_chain(payload: dict[str, Any], *, underlying: str, provenance: Provenance) -> OptionChain:
    result = ((payload.get("optionChain") or {}).get("result") or [None])[0] or {}
    options = (result.get("options") or [None])[0] or {}
    contracts: list[OptionContract] = []
    for side, otype in (("calls", "call"), ("puts", "put")):
        for row in options.get(side) or []:
            if not isinstance(row, dict):
                continue
            exp = row.get("expiration")
            exp_s = datetime.fromtimestamp(int(exp), tz=timezone.utc).date().isoformat() if exp else date.today().isoformat()
            contracts.append(
                OptionContract(
                    symbol=str(row.get("contractSymbol") or underlying),
                    expiry=exp_s,
                    strike=float(_num(row.get("strike")) or 0.0),
                    option_type=otype,  # type: ignore[arg-type]
                    bid=_num(row.get("bid")),
                    ask=_num(row.get("ask")),
                    last=_num(row.get("lastPrice")),
                    volume=_num(row.get("volume")),
                    open_interest=_num(row.get("openInterest")),
                    iv=_num(row.get("impliedVolatility")),
                )
            )
    return OptionChain(
        underlying=from_yahoo_symbol(underlying),
        as_of=date.today().isoformat(),
        contracts=contracts[:500],
        provenance=provenance,
    )


def map_search_results(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Canonical search hits — AGI shape, not Yahoo quoteType dump."""
    out: list[dict[str, Any]] = []
    for row in payload.get("quotes") or []:
        if not isinstance(row, dict):
            continue
        yahoo_sym = _str(row.get("symbol")) or ""
        out.append(
            {
                "symbol": from_yahoo_symbol(yahoo_sym),
                "yahoo_symbol": yahoo_sym,
                "name": _str(row.get("shortname") or row.get("longname")),
                "exchange": _str(row.get("exchange") or row.get("exchDisp")),
                "asset_type": _str(row.get("quoteType") or row.get("typeDisp")),
                "score": _num(row.get("score")),
            }
        )
    return out


def _simplify_statements(rows: list[Any]) -> list[dict[str, Any]]:
    simplified: list[dict[str, Any]] = []
    for row in rows[:12]:
        if not isinstance(row, dict):
            continue
        item: dict[str, Any] = {}
        for k, v in row.items():
            if k in {"maxAge"}:
                continue
            item[k] = _num(v) if isinstance(v, dict) or isinstance(v, (int, float)) else _str(v)
        simplified.append(item)
    return simplified
