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
}

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


def read_sheet_rows(content_bytes: bytes, filename: str, *, sheet_name: Any = 0) -> Any:
    """Return a pandas DataFrame for .xlsx/.xls/.csv content."""
    import pandas as pd

    ext = Path(filename or "").suffix.lower()
    if ext in {".xlsx", ".xls", ".xlsm"}:
        df = pd.read_excel(io.BytesIO(content_bytes), sheet_name=sheet_name)
    elif ext == ".csv":
        df = pd.read_csv(io.BytesIO(content_bytes))
    else:
        raise ValueError(f"unsupported_file_type:{ext or 'unknown'} (use .xlsx, .xls, or .csv)")
    if isinstance(df, dict):  # sheet_name=None returns {sheet: df}
        df = next(iter(df.values()))
    return df.where(df.notnull(), None)


def resolve_ticker(ticker_raw: Any, name_raw: Any) -> tuple[str | None, str]:
    """Resolve a row to a real, uploaded-universe ticker. Never invents one."""
    from trading_universe.loader import get_symbol, search

    if not _is_blank(ticker_raw):
        t = str(ticker_raw).strip().upper().replace(".NS", "").replace(".BO", "")
        if get_symbol(t):
            return t, "exact_ticker"
    if not _is_blank(name_raw):
        name = str(name_raw).strip()
        hits = search(name, limit=5)
        if hits:
            nlow = name.lower()
            exact = [h for h in hits if str(h.get("name") or "").strip().lower() == nlow]
            if exact:
                return exact[0]["symbol"], "exact_name_match"
            return hits[0]["symbol"], (
                "fuzzy_name_match_top1" if len(hits) == 1 else "ambiguous_name_match_top1"
            )
    return None, "unresolved"


def _detect_columns(columns: list[Any]) -> dict[str, Any]:
    header_by_norm: dict[str, Any] = {}
    mapped: dict[str, tuple[str, str]] = {}
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
        else:
            unmapped.append(str(col))
    return {
        "header_by_norm": header_by_norm,
        "mapped": mapped,
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
) -> dict[str, Any]:
    """Parse a company-info spreadsheet and write recognized columns as
    versioned IKT facts. Rows whose company can't be resolved against the
    uploaded universe registry are reported, never guessed.
    """
    df = read_sheet_rows(content_bytes, filename, sheet_name=sheet_name)
    detected = _detect_columns(list(df.columns))
    mapped, unmapped = detected["mapped"], detected["unmapped"]
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
        period = str(period_val) if not _is_blank(period_val) else _today()
        written_fields: list[str] = []
        for norm, (table, field) in mapped.items():
            raw_val = row.get(header_by_norm[norm])
            if _is_blank(raw_val):
                continue
            value = _to_python(raw_val)
            if not dry_run:
                kwargs: dict[str, Any] = {"source": source, "trigger": "bulk_sheet_upload"}
                if TABLE_DEFS[table]["keyed_by_period"]:
                    kwargs["period"] = period
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
