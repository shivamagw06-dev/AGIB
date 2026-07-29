"""Part B — difficult company-type coverage against Golden 200."""

from __future__ import annotations

from typing import Any

REQUIRED_COMPANY_TYPES: tuple[dict[str, Any], ...] = (
    {"id": "large_private_bank", "label": "Large private bank"},
    {"id": "psu_bank", "label": "PSU bank"},
    {"id": "nbfc", "label": "NBFC"},
    {"id": "fmcg", "label": "FMCG"},
    {"id": "it", "label": "IT"},
    {"id": "power", "label": "Power"},
    {"id": "defence", "label": "Defence"},
    {"id": "auto", "label": "Auto"},
    {"id": "cement", "label": "Cement"},
    {"id": "pharma", "label": "Pharma"},
    {"id": "insurance", "label": "Insurance"},
    {"id": "consumer_internet", "label": "Consumer internet"},
    {"id": "loss_making_growth", "label": "Loss-making growth company"},
    {"id": "cyclical_commodity", "label": "Cyclical commodity"},
    {"id": "holding_company", "label": "Holding company"},
    {"id": "conglomerate", "label": "Conglomerate"},
)

# Explicit exemplar tickers preferred when present in Golden 200.
_EXEMPLARS: dict[str, tuple[str, ...]] = {
    "large_private_bank": ("HDFCBANK", "ICICIBANK", "KOTAKBANK", "AXISBANK"),
    "psu_bank": ("SBIN", "BANKBARODA", "PNB", "CANBK", "UNIONBANK"),
    "nbfc": ("BAJFINANCE", "BAJAJFINSV", "CHOLAFIN", "SHRIRAMFIN", "PNBHOUSING", "MUTHOOTFIN"),
    "fmcg": ("HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA", "TATACONSUM", "DABUR", "MARICO"),
    "it": ("TCS", "INFY", "HCLTECH", "WIPRO", "TECHM", "LTM", "PERSISTENT"),
    "power": ("NTPC", "POWERGRID", "TATAPOWER", "ADANIPOWER", "JPPOWER", "RPOWER"),
    "defence": ("HAL", "BEL", "BDL", "MAZDOCK"),
    "auto": ("MARUTI", "M&M", "TMPV", "BAJAJ-AUTO", "EICHERMOT", "HEROMOTOCO", "OLAELEC"),
    "cement": ("ULTRACEMCO", "SHREECEM", "AMBUJACEM", "ACC", "DALBHARAT"),
    "pharma": ("SUNPHARMA", "DRREDDY", "CIPLA", "DIVISLAB", "APOLLOHOSP"),
    "insurance": ("SBILIFE", "HDFCLIFE", "ICICIPRULI", "ICICIGI", "GODFREYPH"),
    "consumer_internet": ("ETERNAL", "NYKAA", "PAYTM", "POLICYBZR", "ZOMATO"),
    "loss_making_growth": ("PAYTM", "NYKAA", "POLICYBZR", "OLAELEC", "DELHIVERY", "IDEA", "TTML"),
    "cyclical_commodity": ("TATASTEEL", "JSWSTEEL", "HINDALCO", "COALINDIA", "VEDL", "NMDC"),
    # Golden v1.0 has no pure HoldCo ticker — use look-through / investment-structure proxies.
    "holding_company": ("RELIANCE", "GRASIM", "ADANIENT"),
    "conglomerate": ("RELIANCE", "ADANIENT", "GRASIM", "LT"),
}


def _classify_row(row: dict[str, Any]) -> set[str]:
    """Heuristic type tags for one golden row."""
    t = str(row.get("ticker") or "").upper()
    sector = str(row.get("sector") or "").lower()
    profile = str(row.get("profile") or "").lower()
    name = str(row.get("name") or "").lower()
    tags: set[str] = set()

    for typ, exemplars in _EXEMPLARS.items():
        if t in exemplars:
            tags.add(typ)

    if "bank" in sector or "bank" in name:
        psu_tokens = ("SBIN", "PNB", "BANKBARODA", "CANBK", "UNIONBANK", "INDIANB", "MAHABANK", "IOB", "CENTRALBK")
        if t in psu_tokens or "psu" in profile:
            tags.add("psu_bank")
        else:
            tags.add("large_private_bank")
    if "nbfc" in sector or "nbfc" in profile or "housing finance" in name:
        tags.add("nbfc")
    if sector in {"fmcg"} or sector.startswith("fmcg"):
        tags.add("fmcg")
    # Avoid false positives: substring "it" matches inside "capital"
    if sector in {"it", "it services"} or "it services" in sector or "information technology" in sector or "software" in sector:
        tags.add("it")
    if sector == "power" or sector.startswith("power"):
        tags.add("power")
    if "defence" in sector or "defense" in sector:
        tags.add("defence")
    if sector in {"auto", "automobile"} or sector.startswith("auto"):
        tags.add("auto")
    if "cement" in sector:
        tags.add("cement")
    if "pharma" in sector or sector == "healthcare":
        tags.add("pharma")
    if "insurance" in sector:
        tags.add("insurance")
    if "internet" in sector or "consumer internet" in sector:
        tags.add("consumer_internet")
    if any(x in profile for x in ("loss", "path_to_profit", "growth_over_profit", "chronic_losses", "ev_oem")):
        tags.add("loss_making_growth")
    if sector in {"metals", "mining", "oil & gas", "energy"} or "commodity" in profile or "cyclical" in profile:
        tags.add("cyclical_commodity")
    if ("holding" in name and "tube" not in name) or "holding" in profile:
        tags.add("holding_company")
    if "conglomerate" in profile or t in {"RELIANCE", "ADANIENT", "GRASIM", "LT"}:
        tags.add("conglomerate")

    return tags


def evaluate_company_types(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Part B coverage against Golden 200 (or provided rows)."""
    if rows is None:
        from knowledge_factory.phase1_golden_test_set import PHASE1_GOLDEN_ROWS

        rows = list(PHASE1_GOLDEN_ROWS)

    by_type: dict[str, list[str]] = {t["id"]: [] for t in REQUIRED_COMPANY_TYPES}
    for row in rows:
        tags = _classify_row(row)
        ticker = str(row.get("ticker") or "").upper()
        for tag in tags:
            if tag in by_type and ticker and ticker not in by_type[tag]:
                by_type[tag].append(ticker)

    missing = [t["id"] for t in REQUIRED_COMPANY_TYPES if not by_type[t["id"]]]
    present = [t["id"] for t in REQUIRED_COMPANY_TYPES if by_type[t["id"]]]
    return {
        "part": "B",
        "title": "Company types",
        "required": [t["id"] for t in REQUIRED_COMPANY_TYPES],
        "labels": {t["id"]: t["label"] for t in REQUIRED_COMPANY_TYPES},
        "coverage": {k: {"n": len(v), "examples": v[:5]} for k, v in by_type.items()},
        "present": present,
        "missing": missing,
        "status": "PASS" if not missing else "FAIL",
        "n_types_required": len(REQUIRED_COMPANY_TYPES),
        "n_types_present": len(present),
    }
