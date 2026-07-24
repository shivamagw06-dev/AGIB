#!/usr/bin/env python3
"""Refresh NIFTYstocks.csv from the official NSE equity securities list.

Usage:
  python3 server/scripts/refresh_nifty_stocks.py
  python3 server/scripts/refresh_nifty_stocks.py --out /path/to/NIFTYstocks.csv

Merges Industry labels from Nifty500.csv when available.
Does not place orders or invent fundamentals.
"""

from __future__ import annotations

import argparse
import csv
import urllib.request
from pathlib import Path

NSE_EQUITY_URL = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = REPO_ROOT / "NIFTYstocks.csv"
NIFTY500_PATH = REPO_ROOT / "Nifty500.csv"
ALLOWED_SERIES = {"EQ", "BE", "SM"}


def fetch_equity_csv(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; AGIB-research/1.0)"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8-sig")


def load_nifty500_industries(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    industries: dict[str, str] = {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            symbol = (row.get("Symbol") or row.get("symbol") or "").strip().upper()
            industry = (row.get("Industry") or "").strip()
            if symbol and industry:
                industries[symbol] = industry
    return industries


def normalize_rows(raw_csv: str, industries: dict[str, str]) -> list[dict[str, str]]:
    reader = csv.DictReader(raw_csv.splitlines())
    field_map = { (k or "").strip().upper(): k for k in (reader.fieldnames or []) }

    def cell(row: dict[str, str], name: str) -> str:
        key = field_map.get(name.upper())
        if key is None:
            return ""
        return (row.get(key) or "").strip()

    seen: set[str] = set()
    rows: list[dict[str, str]] = []
    for row in reader:
        symbol = cell(row, "SYMBOL").upper()
        series = cell(row, "SERIES").upper()
        if not symbol or series not in ALLOWED_SERIES or symbol in seen:
            continue
        seen.add(symbol)
        rows.append(
            {
                "Company Name": cell(row, "NAME OF COMPANY"),
                "Industry": industries.get(symbol, "NSE Equity"),
                "Symbol": symbol,
                "Series": series,
                "ISIN Code": cell(row, "ISIN NUMBER"),
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["Company Name", "Industry", "Symbol", "Series", "ISIN Code"],
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh NIFTYstocks.csv from NSE archives")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--url", default=NSE_EQUITY_URL)
    args = parser.parse_args()

    industries = load_nifty500_industries(NIFTY500_PATH)
    raw = fetch_equity_csv(args.url)
    rows = normalize_rows(raw, industries)
    if not rows:
        raise SystemExit("No EQ/BE/SM symbols parsed from NSE equity list")
    write_csv(args.out, rows)
    labeled = sum(1 for row in rows if row["Industry"] != "NSE Equity")
    print(f"Wrote {len(rows)} NSE equities → {args.out}")
    print(f"Industry labels from Nifty500: {labeled}")


if __name__ == "__main__":
    main()
