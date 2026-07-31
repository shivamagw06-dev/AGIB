"""Bulk company-info sheet ingest (Excel/CSV → IKT facts).

Drop a spreadsheet with one row per company and columns like
"Company Name", "Ticker", "Sector", "CEO", "PE", "Market Cap"... Each
recognized column is written as a versioned IKT fact, keyed to the
ticker resolved from the uploaded universe registry — never a
hardcoded company list, never a fabricated ticker match.
"""

from __future__ import annotations

import io
import re
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any

from institutional_knowledge_tables.schema import TABLE_DEFS
from institutional_knowledge_tables.store import upsert_fact

# normalized header -> (table, field)
_COLUMN_MAP: dict[str, tuple[str, str]] = {
    "company name": ("company_master", "company_name"),
    "company": ("company_master", "company_name"),
    "name": ("company_master", "company_name"),
    "ticker": ("company_master", "ticker"),
    "symbol": ("company_master", "ticker"),
    "nse symbol": ("company_master", "ticker"),
    "nse code": ("company_master", "ticker"),
    "stock symbol": ("company_master", "ticker"),
    "isin": ("company_master", "isin"),
    "isin code": ("company_master", "isin"),
    "sector": ("company_master", "sector"),
    "industry": ("company_master", "industry"),
    "exchange": ("company_master", "exchange"),
    "website": ("company_master", "website"),
    "web site": ("company_master", "website"),
    "cin": ("company_master", "cin"),
    "country": ("company_master", "country"),
    "status": ("company_master", "status"),
    "fiscal year end": ("company_master", "fiscal_year_end"),
    "fye": ("company_master", "fiscal_year_end"),
    "ceo": ("management", "ceo"),
    "chief executive officer": ("management", "ceo"),
    "cfo": ("management", "cfo"),
    "chief financial officer": ("management", "cfo"),
    "auditor": ("management", "auditor"),
    "board": ("management", "board"),
    "independent directors": ("management", "independent_directors"),
    "market cap": ("market_data", "market_cap"),
    "marketcap": ("market_data", "market_cap"),
    "market capitalization": ("market_data", "market_cap"),
    "pe": ("valuation", "pe"),
    "p/e": ("valuation", "pe"),
    "pe ratio": ("valuation", "pe"),
    "pb": ("valuation", "pb"),
    "p/b": ("valuation", "pb"),
    "ev/ebitda": ("valuation", "ev_ebitda"),
    "ev ebitda": ("valuation", "ev_ebitda"),
    "ev/sales": ("valuation", "ev_sales"),
    "dividend yield": ("valuation", "dividend_yield"),
    "fcf yield": ("valuation", "fcf_yield"),
    "peg": ("valuation", "peg"),
    "business segments": ("business_model", "business_segments"),
    "segments": ("business_model", "business_segments"),
    "revenue mix": ("business_model", "revenue_mix"),
    "products": ("business_model", "products"),
    "services": ("business_model", "services"),
    "customers": ("business_model", "customers"),
    "geography": ("business_model", "geography"),
    "competitive position": ("business_model", "competitive_position"),
    "credit rating": ("credit_ratings", "rating"),
    "rating": ("credit_ratings", "rating"),
    "rating agency": ("credit_ratings", "agency"),
    "outlook": ("credit_ratings", "outlook"),
    # Capital IQ / screener-style exports (verbose headers, snapshot pulls)
    "primary sector": ("company_master", "sector"),
    "primary industry": ("company_master", "industry"),
    "trading status": ("company_master", "status"),
    "exchange country/region": ("company_master", "country"),
    "product name": ("products", "product"),
    "competitors": ("competitors", "peer"),
    "long business description": ("business_model", "description"),
    "price change 1 month": ("market_data", "returns_1m"),
    "price change 1 year": ("market_data", "returns_1y"),
}

# Prefix-matched (regex) for headers whose suffix varies by export settings,
# e.g. "EBITDA [LTM] ($USDmm, Historical rate)" or "Market Capitalization
# [My Setting] [Latest] ($USDmm, Historical rate)". Evaluated only when an
# exact _COLUMN_MAP lookup misses.
_PREFIX_PATTERNS: tuple[tuple[re.Pattern[str], str, str, str], ...] = (
    (re.compile(r"^day close price"), "market_data", "close", "latest"),
    (re.compile(r"^daily volume"), "market_data", "volume", "latest"),
    (re.compile(r"^total enterprise value"), "market_data", "enterprise_value", "latest"),
    (re.compile(r"^market capitalization"), "market_data", "market_cap", "latest"),
    (re.compile(r"^ebitda\b"), "financial_statements", "ebitda", "LTM"),
    (re.compile(r"^total revenue\b"), "financial_statements", "revenue", "LTM"),
)

_TICKER_HEADERS = {"ticker", "symbol", "nse symbol", "nse code", "stock symbol"}
_NAME_HEADERS = {"company name", "company", "name"}
_PERIOD_HEADERS = {"as of", "date", "period", "quarter", "fy", "as of date"}


def _norm(header: Any) -> str:
    h = str(header or "").strip().lower().replace("_", " ")
    h = re.sub(r"[^a-z0-9/ ]", " ", h)
    return re.sub(r"\s+", " ", h).strip()


def _today() -> str:
    return date.today().isoformat()


def _to_python(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return value


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    try:
        import pandas as pd

        if pd.isna(value):
            return True
    except Exception:
        pass
    return str(value).strip() == ""


def read_sheet_rows(
    content_bytes: bytes,
    filename: str,
    *,
    sheet_name: Any = 0,
    column_names: list[str] | None = None,
) -> Any:
    """Return a pandas DataFrame for .xlsx/.xls/.csv content.

    Some export tools (e.g. Capital IQ "continuation" batches) omit the
    header row on subsequent files from the same saved screen. Pass the
    header list from the first file as `column_names` to reuse it — the
    file is then read with no header row and those names applied positionally.
    """
    import pandas as pd

    ext = Path(filename or "").suffix.lower()
    header = None if column_names else 0
    if ext in {".xlsx", ".xls", ".xlsm"}:
        df = pd.read_excel(io.BytesIO(content_bytes), sheet_name=sheet_name, header=header)
    elif ext == ".csv":
        df = pd.read_csv(io.BytesIO(content_bytes), header=header)
    else:
        raise ValueError(f"unsupported_file_type:{ext or 'unknown'} (use .xlsx, .xls, or .csv)")
    if isinstance(df, dict):  # sheet_name=None returns {sheet: df}
        df = next(iter(df.values()))
    if column_names:
        if len(column_names) != df.shape[1]:
            raise ValueError(
                f"column_count_mismatch: file has {df.shape[1]} columns, "
                f"column_names has {len(column_names)}"
            )
        df.columns = column_names
    return df.where(df.notnull(), None)


_LEGAL_SUFFIXES = re.compile(
    r"\b(limited|ltd|pvt|private|company|co|corporation|corp|inc|plc|llp)\b",
    re.I,
)
_LEADING_ARTICLE = re.compile(r"^the\s+", re.I)
_EXCHANGE_PREFIX = re.compile(r"^(nse|bse)\s*:\s*", re.I)


_JOINER_WORD = re.compile(r"\band\b", re.I)


def normalize_company_name(name: Any) -> str:
    """Strip legal suffixes, articles, initials-punctuation, and '&'/'and'
    so 'L.G. Balakrishnan & Bros Ltd' and 'Oil and Natural Gas Corporation
    Limited' compare equal to their catalog forms. Matching-only, never stored.
    """
    n = str(name or "").strip().lower()
    n = unicodedata.normalize("NFKD", n).encode("ascii", "ignore").decode("ascii")  # Nestlé -> Nestle
    n = n.replace(".", "")  # "L.G." -> "lg" (no inserted space, unlike other punctuation)
    n = _LEGAL_SUFFIXES.sub(" ", n)
    n = n.replace("&", " ")
    n = _JOINER_WORD.sub(" ", n)
    n = re.sub(r"[^a-z0-9 ]", " ", n)
    n = _LEADING_ARTICLE.sub("", n)
    return re.sub(r"\s+", " ", n).strip()


def _normalized_universe_index() -> list[tuple[str, str, str]]:
    """(normalized_name, symbol, raw_name) for every row in the uploaded
    trading universe — comparison is normalized on both sides so legal
    suffixes/punctuation differences ('Dr. Reddy's' vs 'Dr Reddys') don't
    block a real match.
    """
    from trading_universe.loader import load_rows

    return [(normalize_company_name(r["name"]), r["symbol"], r["name"]) for r in load_rows()]


def resolve_ticker(ticker_raw: Any, name_raw: Any) -> tuple[str | None, str]:
    """Resolve a row to a real, uploaded-universe ticker. Never invents one."""
    from trading_universe.loader import get_symbol

    if not _is_blank(ticker_raw):
        t = _EXCHANGE_PREFIX.sub("", str(ticker_raw).strip()).upper()
        t = t.replace(".NS", "").replace(".BO", "")
        if get_symbol(t):
            return t, "exact_ticker"
    if not _is_blank(name_raw):
        norm_query = normalize_company_name(name_raw)
        if not norm_query:
            return None, "unresolved"
        index = _normalized_universe_index()
        exact = [(sym, raw) for norm, sym, raw in index if norm == norm_query]
        if exact:
            if len(exact) == 1:
                return exact[0][0], "exact_name_match"
            return exact[0][0], "ambiguous_name_match_top1"
        # Substring both directions on normalized names (short-code queries
        # like "hmt" only match if the stored name is short too — avoids a
        # 3-letter fragment matching an unrelated long company name).
        contains = [
            (sym, raw)
            for norm, sym, raw in index
            if len(norm_query) >= 4
            and (norm_query in norm or norm in norm_query)
        ]
        if contains:
            if len(contains) == 1:
                return contains[0][0], "fuzzy_name_match_top1"
            return contains[0][0], "ambiguous_name_match_top1"
    return None, "unresolved"


def _detect_columns(columns: list[Any]) -> dict[str, Any]:
    header_by_norm: dict[str, Any] = {}
    mapped: dict[str, tuple[str, str]] = {}
    period_override: dict[str, str] = {}
    unmapped: list[str] = []
    ticker_col = None
    name_col = None
    period_col = None
    for col in columns:
        norm = _norm(col)
        if not norm:
            continue
        header_by_norm[norm] = col
        if norm in _TICKER_HEADERS and ticker_col is None:
            ticker_col = col
        if norm in _NAME_HEADERS and name_col is None:
            name_col = col
        if norm in _PERIOD_HEADERS and period_col is None:
            period_col = col
        if norm in _COLUMN_MAP:
            mapped[norm] = _COLUMN_MAP[norm]
            continue
        prefix_hit = next((p for p in _PREFIX_PATTERNS if p[0].search(norm)), None)
        if prefix_hit:
            _, table, field, period_label = prefix_hit
            mapped[norm] = (table, field)
            period_override[norm] = period_label
        else:
            unmapped.append(str(col))
    return {
        "header_by_norm": header_by_norm,
        "mapped": mapped,
        "period_override": period_override,
        "unmapped": unmapped,
        "ticker_col": ticker_col,
        "name_col": name_col,
        "period_col": period_col,
    }


def ingest_company_sheet(
    content_bytes: bytes,
    filename: str,
    *,
    sheet_name: Any = 0,
    dry_run: bool = False,
    source_label: str | None = None,
    column_names: list[str] | None = None,
) -> dict[str, Any]:
    """Parse a company-info spreadsheet and write recognized columns as
    versioned IKT facts. Rows whose company can't be resolved against the
    uploaded universe registry are reported, never guessed.

    `column_names`: pass the header list from a sibling file when this file
    is a headerless continuation batch of the same export (same column
    order, header only on the first chunk).
    """
    try:
        df = read_sheet_rows(content_bytes, filename, sheet_name=sheet_name, column_names=column_names)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}
    detected = _detect_columns(list(df.columns))
    mapped, unmapped = detected["mapped"], detected["unmapped"]
    period_override = detected["period_override"]
    ticker_col, name_col, period_col = (
        detected["ticker_col"],
        detected["name_col"],
        detected["period_col"],
    )
    header_by_norm = detected["header_by_norm"]

    if ticker_col is None and name_col is None:
        return {
            "ok": False,
            "error": "no_ticker_or_company_name_column",
            "hint": "Include a 'Ticker'/'Symbol' or 'Company Name' column so rows can be resolved.",
            "columns_seen": [str(c) for c in df.columns],
        }

    source = source_label or f"bulk_upload:{filename}"
    resolved: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    fields_written_total = 0
    tables_touched: set[str] = set()

    for idx, row in df.iterrows():
        ticker_raw = row.get(ticker_col) if ticker_col is not None else None
        name_raw = row.get(name_col) if name_col is not None else None
        ticker, method = resolve_ticker(ticker_raw, name_raw)
        if not ticker:
            unresolved.append(
                {
                    "row": int(idx) + 2,  # +2 ≈ human spreadsheet row (header + 1-index)
                    "company_name": _to_python(name_raw),
                    "ticker_raw": _to_python(ticker_raw),
                    "reason": method,
                }
            )
            continue

        period_val = row.get(period_col) if period_col is not None else None
        row_period = str(period_val) if not _is_blank(period_val) else None
        written_fields: list[str] = []
        for norm, (table, field) in mapped.items():
            if table == "company_master" and field == "ticker":
                # Always the resolved, canonical ticker — never the raw sheet
                # cell (which may be an exchange-prefixed code like
                # "BSE:500002" that would contradict the entity key itself).
                value = ticker
            else:
                raw_val = row.get(header_by_norm[norm])
                if _is_blank(raw_val):
                    continue
                value = _to_python(raw_val)
            if not dry_run:
                kwargs: dict[str, Any] = {"source": source, "trigger": "bulk_sheet_upload"}
                if TABLE_DEFS[table]["keyed_by_period"]:
                    # Priority: an explicit per-row period column > a
                    # column-specific label (e.g. "LTM", "latest" inferred
                    # from the header itself) > today's upload date.
                    kwargs["period"] = row_period or period_override.get(norm) or _today()
                upsert_fact(ticker, table, field, value, **kwargs)
            written_fields.append(f"{table}.{field}")
            tables_touched.add(table)
            fields_written_total += 1
        resolved.append(
            {
                "row": int(idx) + 2,
                "ticker": ticker,
                "method": method,
                "fields_written": written_fields,
            }
        )

    return {
        "ok": True,
        "dry_run": dry_run,
        "filename": filename,
        "source": source,
        "total_rows": int(len(df)),
        "resolved_count": len(resolved),
        "unresolved_count": len(unresolved),
        "unresolved_rows": unresolved[:50],
        "resolved_sample": resolved[:20],
        "mapped_columns": {header_by_norm[n]: f"{t}.{f}" for n, (t, f) in mapped.items()},
        "unmapped_columns": unmapped,
        "tables_touched": sorted(tables_touched),
        "fields_written_total": fields_written_total,
        "ticker_column": str(ticker_col) if ticker_col is not None else None,
        "name_column": str(name_col) if name_col is not None else None,
        "period_column": str(period_col) if period_col is not None else None,
    }
