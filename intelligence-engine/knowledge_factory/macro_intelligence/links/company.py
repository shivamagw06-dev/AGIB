"""Company ↔ macro knowledge links (knowledge only)."""

from __future__ import annotations

from typing import Any

from knowledge_factory.macro_intelligence import store as imi_store
from knowledge_factory.macro_intelligence.producers.impacts import relationship, shock_impact, usd_strength_it_impact
from knowledge_factory.macro_intelligence.producers.regime import classify_current
from knowledge_factory.macro_intelligence.schema import IMI_VERSION

# Representative company → institutional sector affinity (knowledge overlay).
COMPANY_SECTOR = {
    "TCS": "it_services",
    "INFY": "it_services",
    "HCLTECH": "it_services",
    "WIPRO": "it_services",
    "HDFCBANK": "banks",
    "ICICIBANK": "banks",
    "SBIN": "banks",
    "BAJFINANCE": "nbfc",
    "RELIANCE": "oil_gas",
    "ONGC": "oil_gas",
    "INDIGO": "logistics",
    "ASIANPAINT": "chemicals",
    "HINDUNILVR": "fmcg",
    "ITC": "fmcg",
    "TATASTEEL": "metals",
    "JSWSTEEL": "metals",
    "NTPC": "utilities",
    "POWERGRID": "utilities",
    "DLF": "real_estate",
    "MARUTI": "auto",
}


def company_macro_link(symbol: str) -> dict[str, Any]:
    sector = COMPANY_SECTOR.get(symbol.upper())
    classified = classify_current()
    regimes = list(classified.get("active_regimes") or [])
    drivers: list[str] = []
    sensitivity: list[dict[str, Any]] = []
    risks: list[str] = []
    if sector:
        for macro in ("interest_rates", "oil", "inflation", "usd", "dxy"):
            rel = relationship(macro, sector)
            if not rel.get("found"):
                continue
            drivers.append(macro)
            sensitivity.append(
                {
                    "macro": macro,
                    "sector": sector,
                    "direction": rel.get("direction"),
                    "strength": rel.get("strength"),
                    "confidence": rel.get("confidence"),
                    "historical_validation": rel.get("historical_validation"),
                }
            )
            if rel.get("direction", 0) < 0 and float(rel.get("strength") or 0) >= 1:
                risks.append(f"{macro}_adverse_for_{sector}")
    oil = shock_impact("oil", 0.30)
    usd = usd_strength_it_impact()
    link = {
        "link_type": "company_macro",
        "symbol": symbol.upper(),
        "sector_affinity": sector,
        "macro_sensitivity": sensitivity,
        "macro_drivers": drivers,
        "macro_risk": risks,
        "historical_macro_behaviour": {
            "oil_shock_proxy": oil.get("company_impacts"),
            "usd_strength_proxy": usd if sector == "it_services" else None,
        },
        "historical_regime_performance": {
            "active_regimes": regimes,
            "primary_regime": classified.get("primary_regime"),
            "note": "Knowledge overlay only; no portfolio reasoning changes.",
        },
        "imi_version": IMI_VERSION,
        "knowledge_only": True,
        "insufficient": sector is None,
        "reason": None if sector else "no_sector_affinity_mapping",
        "fabricated": False,
    }
    return link


def compile_company_links(symbols: list[str] | None = None) -> dict[str, Any]:
    symbols = symbols or list(COMPANY_SECTOR.keys())
    links = {s.upper(): company_macro_link(s) for s in symbols}
    payload = {
        "kind": "company_macro",
        "n": len(links),
        "links": links,
        "imi_version": IMI_VERSION,
        "knowledge_only": True,
    }
    imi_store.put_links("company", payload)
    return payload
