#!/usr/bin/env python3
"""
Nifty 500 research engine — read-only, research-only output.

Requirements:
  pip install growwapi pandas

Configuration:
  export GROWW_ACCESS_TOKEN="..."
  export NIFTY500_CONSTITUENTS_PATH="/path/to/nifty500_constituents.csv"
  export SUPABASE_URL="https://your-project.supabase.co"
  export SUPABASE_SERVICE_ROLE_KEY="server-only-service-role-key"

The CSV must be a current, licensed constituent export with one `symbol` column.
This script validates and de-duplicates symbols through Groww before analysis.
It does not place orders and does not generate investment recommendations.
"""

import csv
import json
import math
import os
import time
from datetime import datetime, timedelta, time as clock_time
from pathlib import Path
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

import pandas as pd
from growwapi import GrowwAPI


SERVER_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"


def load_server_env() -> None:
    """Load server/.env without requiring python-dotenv or shell `source`.

    Existing non-empty environment variables take precedence, which keeps
    Render/cron configuration authoritative while making local `--once` runs
    work from the server directory.
    """
    if not SERVER_ENV_PATH.exists():
        return

    for raw_line in SERVER_ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip().removeprefix("export ").strip()
        if not key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        if not os.environ.get(key):
            os.environ[key] = value


load_server_env()

IST = ZoneInfo("Asia/Kolkata")
OUTPUT_PATH = Path(os.getenv("NIFTY500_RESEARCH_OUTPUT", "nifty500_research.json"))
DEFAULT_CONSTITUENTS_PATH = Path(__file__).resolve().parents[2] / "Nifty500.csv"
CONSTITUENTS_PATH = Path(os.getenv("NIFTY500_CONSTITUENTS_PATH", DEFAULT_CONSTITUENTS_PATH))

CONFIG = {
    "exchange": "NSE",
    "segment": "CASH",
    "lookback_days": 380,  # enough calendar history for 200+ trading sessions
    "top_n": 20,
    "schedule_times_ist": tuple(
        value.strip()
        for value in os.getenv("NIFTY500_SCHEDULE_TIMES_IST", "16:15").split(",")
        if value.strip()
    ),
    "rsi_period": 14,
    "sma_short": 20,
    "sma_long": 50,
    "sma_200": 200,
    "volume_average_period": 20,
    "minimum_publish_coverage": float(os.getenv("NIFTY500_MINIMUM_PUBLISH_COVERAGE", "0.95")),
}


def now_ist() -> datetime:
    return datetime.now(IST)


def load_constituents(path: Path) -> list[str]:
    """Load, normalize and de-duplicate a licensed Nifty 500 CSV export."""
    if not path.exists():
        raise FileNotFoundError(
            f"Missing constituent file: {path}. Supply a current licensed CSV with a 'symbol' column."
        )

    seen: set[str] = set()
    symbols: list[str] = []
    with path.open(newline="", encoding="utf-8-sig") as source:
        for row in csv.DictReader(source):
            raw = str(row.get("symbol") or row.get("Symbol") or "").strip().upper()
            if raw and raw not in seen:
                seen.add(raw)
                symbols.append(raw)

    if not symbols:
        raise ValueError("No symbols found. The CSV must include a 'symbol' column.")
    return symbols


def chunks(values: list[Any], size: int) -> list[list[Any]]:
    return [values[index : index + size] for index in range(0, len(values), size)]


def supabase_request(
    method: str,
    table: str,
    *,
    body: Optional[dict | list[dict]] = None,
    query: Optional[dict[str, str]] = None,
    prefer: str = "return=minimal",
) -> Any:
    """Call Supabase REST with server-only credentials; never use these in the browser."""
    base_url = os.getenv("SUPABASE_URL", "").rstrip("/")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not base_url or not service_key:
        raise RuntimeError(
            "Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY to publish Nifty 500 research."
        )
    if not base_url.startswith(("https://", "http://")):
        raise RuntimeError(
            "SUPABASE_URL must be only the project URL, for example "
            "https://your-project.supabase.co. Remove any duplicated SUPABASE_URL= prefix."
        )

    url = f"{base_url}/rest/v1/{table}"
    if query:
        url = f"{url}?{urlencode(query)}"
    payload = json.dumps(body).encode("utf-8") if body is not None else None
    request = Request(
        url,
        data=payload,
        method=method,
        headers={
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Prefer": prefer,
        },
    )
    try:
        with urlopen(request, timeout=45) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else None
    except HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Supabase {method} {table} failed ({error.code}): {details}") from error
    except URLError as error:
        raise RuntimeError(f"Supabase {method} {table} connection failed: {error.reason}") from error


def validate_publish_config() -> None:
    base_url = os.getenv("SUPABASE_URL", "").strip()
    if not base_url or not os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip():
        raise RuntimeError(
            "Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in server/.env before running "
            "the Nifty 500 worker. The service-role key is required to publish the completed run."
        )
    if not base_url.startswith(("https://", "http://")):
        raise RuntimeError(
            "SUPABASE_URL must be only the project URL, for example "
            "https://your-project.supabase.co. Remove any duplicated SUPABASE_URL= prefix."
        )


def publish_to_supabase(output: dict) -> str:
    """Publish only a fully written draft run; draft/failed runs stay private."""
    meta = output["meta"]
    run_rows = supabase_request(
        "POST",
        "nifty500_research_runs",
        body={
            "generated_at": meta["generated_at"],
            "run_name": meta["run_name"],
            "total_stocks_analyzed": meta["total_stocks_analyzed"],
            "rejected_symbols": meta["rejected_symbols"],
            "disclaimer": meta["disclaimer"],
            "status": "draft",
        },
        prefer="return=representation",
    )
    if not run_rows or not run_rows[0].get("id"):
        raise RuntimeError("Supabase did not return a research run id.")
    run_id = run_rows[0]["id"]

    records = [{"run_id": run_id, **stock} for stock in output["stocks"].values()]
    for batch in chunks(records, 100):
        supabase_request("POST", "nifty500_stock_research", body=batch)

    # Stock rows are complete before either visibility change. If publishing
    # fails, this draft remains private and the prior published run stays usable.
    supabase_request(
        "PATCH",
        "nifty500_research_runs",
        body={"is_current": False},
        query={"is_current": "eq.true"},
    )
    supabase_request(
        "PATCH",
        "nifty500_research_runs",
        body={
            "status": "published",
            "is_current": True,
            "published_at": now_ist().isoformat(),
        },
        query={"id": f"eq.{run_id}", "status": "eq.draft"},
    )
    return run_id


def publish_existing_output() -> None:
    """Publish an already completed local JSON output without repeating analysis."""
    validate_publish_config()
    if not OUTPUT_PATH.exists():
        raise FileNotFoundError(f"No saved research output exists at {OUTPUT_PATH}. Run with --once first.")
    output = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    stocks = output.get("stocks") or {}
    rejected = output.get("meta", {}).get("rejected_symbols") or []
    total = len(stocks) + len(rejected)
    coverage = len(stocks) / max(total, 1)
    if not stocks or coverage < CONFIG["minimum_publish_coverage"]:
        raise RuntimeError(
            f"Refusing to publish saved output with {coverage:.1%} coverage; "
            f"minimum is {CONFIG['minimum_publish_coverage']:.1%}."
        )
    run_id = publish_to_supabase(output)
    print(f"Published saved Nifty 500 research run {run_id} to Supabase")


def candle_frame(response: dict) -> pd.DataFrame:
    candles = response.get("candles", [])
    if not candles:
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
    # Groww's CASH endpoint currently returns six fields (without open
    # interest), while FNO payloads may include a seventh OI field. Research
    # uses the first six fields only.
    rows = [list(candle[:6]) for candle in candles if len(candle) >= 6]
    frame = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
    for field in ("open", "high", "low", "close", "volume"):
        frame[field] = pd.to_numeric(frame[field], errors="coerce")
    return frame.dropna(subset=["open", "high", "low", "close"]).sort_values("timestamp").reset_index(drop=True)


def fetch_daily_history(access_token: str, instrument: dict) -> pd.DataFrame:
    """Fetch daily candles through Groww's REST endpoint in safe 180-day windows.

    The Python SDK's backtesting method can return empty candle arrays for CASH
    equities even when the corresponding Groww REST endpoint returns data.
    """
    end = now_ist()
    start = end - timedelta(days=CONFIG["lookback_days"])
    cursor = start
    parts: list[pd.DataFrame] = []
    api_base = os.getenv("GROWW_API_BASE", "https://api.groww.in/v1").rstrip("/")
    # Groww documents CASH groww symbols as NSE-<trading_symbol>. Prefer this
    # canonical value: some SDK instrument payloads expose a display symbol
    # with an exchange-series suffix that the historical REST endpoint rejects.
    groww_symbol = str(instrument.get("groww_symbol") or "")
    trading_symbol = groww_symbol.split("-", 1)[-1] if "-" in groww_symbol else (
        instrument.get("symbol") or instrument.get("trading_symbol") or groww_symbol
    )

    while cursor < end:
        finish = min(cursor + timedelta(days=180), end)
        query = urlencode(
            {
                "exchange": instrument["exchange"],
                "segment": instrument["segment"],
                "trading_symbol": trading_symbol,
                "start_time": cursor.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": finish.strftime("%Y-%m-%d %H:%M:%S"),
                "interval_in_minutes": "1440",
            }
        )
        request = Request(
            f"{api_base}/historical/candle/range?{query}",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {access_token}",
                "X-API-VERSION": "1.0",
            },
        )
        try:
            with urlopen(request, timeout=45) as response:
                envelope = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Groww historical request failed ({error.code}): {detail}") from error
        except URLError as error:
            raise RuntimeError(f"Groww historical request failed: {error.reason}") from error

        if envelope.get("status") != "SUCCESS":
            error = envelope.get("error") or {}
            raise RuntimeError(
                f"Groww historical request failed: "
                f"{error.get('message') or error.get('errorMessage') or envelope}"
            )
        payload = envelope.get("payload") or {}
        frame = candle_frame(payload)
        if not frame.empty:
            parts.append(frame)
        cursor = finish
        time.sleep(0.35)

    if not parts:
        return pd.DataFrame()
    return (
        pd.concat(parts, ignore_index=True)
        .drop_duplicates(subset=["timestamp"], keep="last")
        .sort_values("timestamp")
        .reset_index(drop=True)
    )


def last_or_default(series: pd.Series, default: float = 0.0) -> float:
    value = series.iloc[-1] if len(series) else default
    return float(value) if pd.notna(value) else default


def calculate_indicators(frame: pd.DataFrame) -> Optional[dict]:
    if len(frame) < CONFIG["sma_200"]:
        return None

    close, high, low, volume = frame["close"], frame["high"], frame["low"], frame["volume"]
    delta = close.diff()
    gain, loss = delta.clip(lower=0), -delta.clip(upper=0)
    average_gain = gain.ewm(com=CONFIG["rsi_period"] - 1, min_periods=CONFIG["rsi_period"]).mean()
    average_loss = loss.ewm(com=CONFIG["rsi_period"] - 1, min_periods=CONFIG["rsi_period"]).mean()
    rsi = 100 - (100 / (1 + average_gain / average_loss.replace(0, math.nan)))

    ema_fast = close.ewm(span=12, adjust=False).mean()
    ema_slow = close.ewm(span=26, adjust=False).mean()
    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=9, adjust=False).mean()
    histogram = macd - macd_signal

    sma20, sma50, sma200 = close.rolling(20).mean(), close.rolling(50).mean(), close.rolling(200).mean()
    middle = close.rolling(20).mean()
    std = close.rolling(20).std()
    upper, lower = middle + 2 * std, middle - 2 * std
    band_width = upper - lower
    percent_b = (close - lower) / band_width.replace(0, math.nan)

    previous_close = close.shift()
    true_range = pd.concat([high - low, (high - previous_close).abs(), (low - previous_close).abs()], axis=1).max(axis=1)
    atr = true_range.ewm(com=13, min_periods=14).mean()

    average_volume = volume.rolling(CONFIG["volume_average_period"]).mean()
    roc_10 = (close / close.shift(10) - 1) * 100
    change_5 = (close / close.shift(5) - 1) * 100
    change_20 = (close / close.shift(20) - 1) * 100
    change_60 = (close / close.shift(60) - 1) * 100

    high_52 = high.rolling(252).max()
    low_52 = low.rolling(252).min()
    position_52 = (close - low_52) / (high_52 - low_52).replace(0, math.nan)

    return {
        "rsi": last_or_default(rsi, 50),
        "macd_histogram": last_or_default(histogram),
        "macd_positive": last_or_default(macd) > last_or_default(macd_signal),
        "above_sma20": last_or_default(close) > last_or_default(sma20),
        "above_sma50": last_or_default(close) > last_or_default(sma50),
        "above_sma200": last_or_default(close) > last_or_default(sma200),
        "sma20_above_sma50": last_or_default(sma20) > last_or_default(sma50),
        "percent_b": last_or_default(percent_b, 0.5),
        "atr_percent": (last_or_default(atr) / max(last_or_default(close), 0.01)) * 100,
        "volume_ratio": last_or_default(volume) / max(last_or_default(average_volume, 1), 1),
        "change_5d": last_or_default(change_5),
        "change_20d": last_or_default(change_20),
        "change_60d": last_or_default(change_60),
        "roc_10": last_or_default(roc_10),
        "position_52w": last_or_default(position_52, 0.5),
    }


def score_research(indicators: dict) -> float:
    """AGI research score, derived from trend, momentum, participation and structure."""
    score = 50.0
    rsi = indicators["rsi"]
    score += 8 if rsi >= 60 else 3 if rsi >= 50 else -3 if rsi <= 40 else 0
    score += 7 if indicators["macd_positive"] and indicators["macd_histogram"] > 0 else -7 if not indicators["macd_positive"] and indicators["macd_histogram"] < 0 else 0
    score += sum((3 if flag else -3) for flag in (indicators["above_sma20"], indicators["above_sma50"], indicators["above_sma200"]))
    score += 5 if indicators["sma20_above_sma50"] else -5
    score += 5 if indicators["change_20d"] > 2 else -5 if indicators["change_20d"] < -2 else 0
    score += 5 if indicators["change_60d"] > 5 else -5 if indicators["change_60d"] < -5 else 0
    score += 4 if indicators["volume_ratio"] >= 1.2 and indicators["change_5d"] > 0 else -4 if indicators["volume_ratio"] >= 1.2 and indicators["change_5d"] < 0 else 0
    score += 5 if indicators["position_52w"] >= 0.7 else -5 if indicators["position_52w"] <= 0.3 else 0
    score += 3 if indicators["roc_10"] > 0 else -3 if indicators["roc_10"] < 0 else 0
    return round(max(0, min(100, score)), 1)


def category(score: float) -> str:
    if score >= 72:
        return "Strong Bullish"
    if score >= 58:
        return "Bullish"
    if score >= 43:
        return "Neutral"
    if score >= 28:
        return "Bearish"
    return "Strong Bearish"


def confidence(score: float, indicators: dict) -> int:
    direction = score >= 50
    checks = [
        indicators["rsi"] >= 50,
        indicators["macd_histogram"] > 0,
        indicators["above_sma50"],
        indicators["above_sma200"],
        indicators["change_20d"] > 0,
        indicators["change_60d"] > 0,
        indicators["position_52w"] >= 0.5,
    ]
    agreement = sum(check == direction for check in checks) / len(checks)
    return round(min(95, max(40, (50 + abs(score - 50)) * (0.7 + agreement * 0.3))))


def narrative(symbol: str, label: str, indicators: dict) -> dict:
    trend = "constructive" if indicators["above_sma200"] and indicators["sma20_above_sma50"] else "weakened" if not indicators["above_sma200"] else "mixed"
    momentum = "supportive" if indicators["rsi"] >= 50 and indicators["macd_histogram"] > 0 else "soft" if indicators["rsi"] < 45 and indicators["macd_histogram"] < 0 else "mixed"
    participation = "above normal" if indicators["volume_ratio"] >= 1.2 else "below normal" if indicators["volume_ratio"] < 0.8 else "broadly normal"
    volatility = "elevated" if indicators["atr_percent"] > 3 else "contained" if indicators["atr_percent"] < 1.5 else "moderate"
    structure = "upper" if indicators["position_52w"] >= 0.7 else "lower" if indicators["position_52w"] <= 0.3 else "middle"

    supporting = []
    risks = []
    if indicators["above_sma200"]:
        supporting.append("The long-term trend benchmark remains supportive.")
    else:
        risks.append("The stock remains below its long-term trend benchmark.")
    if indicators["macd_histogram"] > 0:
        supporting.append("MACD momentum is positive.")
    else:
        risks.append("MACD momentum remains negative or inconclusive.")
    if indicators["volume_ratio"] >= 1.2:
        supporting.append("Recent volume participation is above its 20-session average.")
    if indicators["atr_percent"] > 3:
        risks.append("Volatility is elevated relative to the recent price range.")
    if not supporting:
        supporting.append("No dominant technical confirmation is currently evident.")
    if not risks:
        risks.append("Normal market and company-specific risks remain.")

    summary = "\n\n".join(
        [
            f"{symbol} currently exhibits a {label.lower()} technical profile. Trend conditions are {trend}, "
            f"while momentum is {momentum}.",
            f"Participation is {participation} and volatility is {volatility}. The stock sits in the "
            f"{structure} portion of its trailing 52-week range.",
            "This is a factual technical assessment for research purposes only. It is not investment advice "
            "or a recommendation to buy or sell securities.",
        ]
    )
    return {
        "research_summary": summary,
        "trend_analysis": f"Trend structure is {trend}, based on moving-average alignment and the long-term trend benchmark.",
        "momentum_analysis": f"Momentum is {momentum}, based on RSI, MACD and recent rate of change.",
        "volume_analysis": f"Volume participation is {participation} versus the 20-session average.",
        "volatility_analysis": f"Volatility is {volatility}, assessed from the average true range as a percentage of price.",
        "market_structure_analysis": f"Price is positioned in the {structure} portion of its trailing 52-week range.",
        "relative_strength_analysis": f"Recent 20-session and 60-session price changes are {indicators['change_20d']:.1f}% and {indicators['change_60d']:.1f}%.",
        "supporting_factors": supporting,
        "risk_factors": risks,
        "key_observations": [
            f"RSI: {indicators['rsi']:.1f}",
            f"20-session change: {indicators['change_20d']:.1f}%",
            f"60-session change: {indicators['change_60d']:.1f}%",
            f"Volume participation: {indicators['volume_ratio']:.2f}x 20-session average",
        ],
    }


def build_output(results: list[dict], run_name: str, rejected: list[dict]) -> dict:
    ordered = sorted(results, key=lambda item: item["agi_research_score"], reverse=True)
    bearish = sorted(results, key=lambda item: item["agi_research_score"])
    return {
        "meta": {
            "generated_at": now_ist().isoformat(),
            "run_name": run_name,
            "total_stocks_analyzed": len(results),
            "rejected_symbols": rejected,
            "disclaimer": "Generated technical research for informational purposes only. Not investment advice or a recommendation to buy or sell securities.",
        },
        "summary": {
            "top_20_most_bullish": ordered[: CONFIG["top_n"]],
            "top_20_most_bearish": bearish[: CONFIG["top_n"]],
            "top_20_neutral_watchlist": [item for item in ordered if item["overall_sentiment"] == "Neutral"][: CONFIG["top_n"]],
        },
        "stocks": {item["symbol"]: item for item in ordered},
    }


def run_once(run_name: str = "After Market Close Research") -> None:
    access_token = os.environ.get("GROWW_ACCESS_TOKEN", "").strip()
    api_key = os.environ.get("GROWW_API_KEY", "").strip()
    api_secret = os.environ.get("GROWW_API_SECRET", "").strip()
    if access_token:
        groww_access_token = access_token
    elif api_key.startswith("eyJ") and len(api_key) > 100:
        # Backward-compatible handling for an access token placed in GROWW_API_KEY.
        # Prefer moving it to GROWW_ACCESS_TOKEN in the environment configuration.
        print("Using JWT-style access token from GROWW_API_KEY; move it to GROWW_ACCESS_TOKEN.")
        groww_access_token = api_key
    elif api_key and api_secret:
        groww_access_token = GrowwAPI.get_access_token(api_key=api_key, secret=api_secret)
    else:
        raise RuntimeError("Set GROWW_ACCESS_TOKEN or GROWW_API_KEY and GROWW_API_SECRET before running.")
    groww = GrowwAPI(groww_access_token)
    validate_publish_config()
    symbols = load_constituents(CONSTITUENTS_PATH)
    results, rejected = [], []

    for index, symbol in enumerate(symbols, start=1):
        try:
            instrument = groww.get_instrument_by_exchange_and_trading_symbol(
                exchange=CONFIG["exchange"], trading_symbol=symbol
            )
            if instrument.get("segment") != CONFIG["segment"]:
                rejected.append({"symbol": symbol, "reason": "not_cash_equity"})
                continue
            history = fetch_daily_history(groww_access_token, instrument)
            if index == 1 and history.empty:
                raise RuntimeError(
                    f"Groww returned no daily candles for {symbol}; "
                    f"resolved trading symbol was {instrument.get('groww_symbol')!r}."
                )
            indicators = calculate_indicators(history)
            if not indicators:
                rejected.append({"symbol": symbol, "reason": "insufficient_history"})
                continue
            score = score_research(indicators)
            label = category(score)
            result = {
                "symbol": symbol,
                "overall_sentiment": label,
                "agi_research_score": score,
                "ai_confidence_percent": confidence(score, indicators),
                "last_updated": now_ist().isoformat(),
                **narrative(symbol, label, indicators),
            }
            results.append(result)
            print(f"[{index}/{len(symbols)}] {symbol}: {label} ({score})")
        except Exception as error:
            rejected.append({"symbol": symbol, "reason": str(error)})

    output = build_output(results, run_name, rejected)
    OUTPUT_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"Saved {len(results)} research records to {OUTPUT_PATH}")

    coverage = len(results) / max(len(symbols), 1)
    if coverage < CONFIG["minimum_publish_coverage"]:
        raise RuntimeError(
            f"Refusing to publish an incomplete run ({coverage:.1%} coverage; "
            f"minimum {CONFIG['minimum_publish_coverage']:.1%})."
        )
    run_id = publish_to_supabase(output)
    print(f"Published Nifty 500 research run {run_id} to Supabase")


def run_scheduler() -> None:
    last_run: set[str] = set()
    while True:
        now = now_ist()
        marker = now.strftime("%Y-%m-%d-%H:%M")
        if now.weekday() < 5 and now.strftime("%H:%M") in CONFIG["schedule_times_ist"] and marker not in last_run:
            run_once()
            last_run.add(marker)
        time.sleep(30)


if __name__ == "__main__":
    # Use --once for an immediate manual run, --publish-existing to publish a
    # completed JSON backup, or no flag for the weekday scheduler.
    import sys

    if "--publish-existing" in sys.argv:
        publish_existing_output()
    elif "--once" in sys.argv:
        run_once("Manual Research Run")
    else:
        run_scheduler()
