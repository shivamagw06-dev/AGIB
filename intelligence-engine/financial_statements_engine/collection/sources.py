"""Official source registry and hierarchy (FSE-02 §3)."""

from __future__ import annotations

from typing import Any

# Lower integer = higher priority (official first / hierarchy)
SOURCE_PRIORITY: dict[str, int] = {
    "nse_xbrl": 10,
    "nse_integrated_filing": 20,
    "nse_corporates_financial_results": 30,
    "bse_xbrl": 40,
    "bse_filing": 50,
    "xbrl_repository": 60,
    "company_ir": 70,
    "quarterly_results": 80,
    "annual_report_pdf": 90,
    "mca_validation": 100,  # validation only — never canonical overwrite
}

# Document-type hierarchy within the same period (FSE-02 §3.2)
DOCUMENT_PRIORITY: dict[str, int] = {
    "xbrl": 10,  # Official XBRL
    "html": 20,  # Official exchange filing (often HTML)
    "pdf": 30,  # Company IR / annual report PDF
    "xlsx": 40,
    "zip": 50,
    "unknown": 90,
}

OFFICIAL_ORDER = (
    "nse",
    "bse",
    "company_ir",
    "xbrl_repositories",
    "annual_reports",
    "quarterly_results",
    "mca",
)


def source_rank(source: str | None) -> int:
    if not source:
        return 999
    return int(SOURCE_PRIORITY.get(str(source), 500))


def document_rank(document_type: str | None) -> int:
    if not document_type:
        return 999
    return int(DOCUMENT_PRIORITY.get(str(document_type).lower(), 500))


def is_higher_priority(candidate: dict[str, Any], incumbent: dict[str, Any]) -> bool:
    """Return True if candidate may supersede incumbent for the same period.

    Lower-priority sources must not overwrite higher-priority evidence.
    """
    c_src = source_rank(candidate.get("source"))
    i_src = source_rank(incumbent.get("source"))
    if c_src != i_src:
        return c_src < i_src
    c_doc = document_rank(candidate.get("document_type"))
    i_doc = document_rank(incumbent.get("document_type"))
    return c_doc < i_doc


def logical_key(
    *,
    ticker: str,
    period_type: str | None,
    period_end: str | None,
    document_type: str | None,
    consolidation: str | None = None,
) -> str:
    parts = [
        str(ticker or "").upper().strip(),
        str(period_type or "unknown"),
        str(period_end or "unknown"),
        str(document_type or "unknown").lower(),
        str(consolidation or "unspecified"),
    ]
    return "|".join(parts)


def sources_manifest() -> dict[str, Any]:
    return {
        "official_order": list(OFFICIAL_ORDER),
        "source_priority": dict(sorted(SOURCE_PRIORITY.items(), key=lambda kv: kv[1])),
        "document_priority": dict(sorted(DOCUMENT_PRIORITY.items(), key=lambda kv: kv[1])),
    }
