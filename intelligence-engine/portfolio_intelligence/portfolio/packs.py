"""Institutional portfolio memory — V1 seed books (not live brokerage sync)."""

from __future__ import annotations

from typing import Any

from portfolio_intelligence.schema import Holding, PortfolioProfile

PORTFOLIOS: dict[str, dict[str, Any]] = {
    "agib_core_india": {
        "profile": PortfolioProfile(
            portfolio_id="agib_core_india",
            name="AGIB Core India Equity",
            objective="Long-term compounding via high-quality India franchises",
            benchmark="Nifty 50 TRI",
            base_currency="INR",
            risk_tolerance="moderate",
            horizon="7y+",
            target_return="CPI+6% to CPI+8%",
            max_drawdown=0.28,
            liquidity_requirement="T+5 institutional",
            tax_preferences="long_term_capital_gains_aware",
            sector_limits={"banks": 0.35, "it_services": 0.25, "fmcg": 0.20, "consumer_internet": 0.15},
            single_name_limit=0.12,
        ).to_dict(),
        "holdings": [
            Holding(
                "HDFCBANK",
                0.11,
                "banks",
                "private_bank",
                "IN",
                "large",
                "quality",
                "Liability franchise rebuild + capital resilience",
                "high",
                "2024-03-15",
                1450.0,
                {"quality": 0.8, "value": 0.4, "growth": 0.5, "momentum": 0.3, "low_vol": 0.6, "dividend": 0.4, "leverage": 0.5, "profitability": 0.7},
            ).to_dict(),
            Holding(
                "ICICIBANK",
                0.09,
                "banks",
                "private_bank",
                "IN",
                "large",
                "quality",
                "Retail franchise + underwriting discipline",
                "high",
                "2023-11-01",
                920.0,
                {"quality": 0.75, "value": 0.45, "growth": 0.55, "momentum": 0.4, "low_vol": 0.55, "dividend": 0.35, "leverage": 0.55, "profitability": 0.72},
            ).to_dict(),
            Holding(
                "TCS",
                0.10,
                "it_services",
                "it_services",
                "IN",
                "large",
                "quality",
                "Cash-rich IT franchise, capital return discipline",
                "high",
                "2022-06-01",
                3200.0,
                {"quality": 0.9, "value": 0.35, "growth": 0.45, "momentum": 0.35, "low_vol": 0.7, "dividend": 0.55, "leverage": 0.15, "profitability": 0.9},
            ).to_dict(),
            Holding(
                "INFY",
                0.08,
                "it_services",
                "it_services",
                "IN",
                "large",
                "quality",
                "Digital services quality compounder",
                "medium",
                "2023-01-20",
                1400.0,
                {"quality": 0.85, "value": 0.4, "growth": 0.5, "momentum": 0.4, "low_vol": 0.65, "dividend": 0.5, "leverage": 0.2, "profitability": 0.85},
            ).to_dict(),
            Holding(
                "NESTLEIND",
                0.07,
                "fmcg",
                "staples",
                "IN",
                "large",
                "quality",
                "Pricing power + distribution moat",
                "medium",
                "2021-09-10",
                18000.0,
                {"quality": 0.88, "value": 0.2, "growth": 0.55, "momentum": 0.35, "low_vol": 0.75, "dividend": 0.45, "leverage": 0.2, "profitability": 0.88},
            ).to_dict(),
            Holding(
                "RELIANCE",
                0.08,
                "energy_conglomerate",
                "conglomerate",
                "IN",
                "large",
                "blend",
                "Energy + retail + digital platform optionality",
                "medium",
                "2022-02-01",
                2400.0,
                {"quality": 0.65, "value": 0.5, "growth": 0.6, "momentum": 0.45, "low_vol": 0.4, "dividend": 0.35, "leverage": 0.55, "profitability": 0.6},
            ).to_dict(),
            Holding(
                "BHARTIARTL",
                0.06,
                "telecom",
                "telecom",
                "IN",
                "large",
                "growth",
                "Industry consolidation + ARPU recovery",
                "medium",
                "2023-05-01",
                850.0,
                {"quality": 0.6, "value": 0.35, "growth": 0.7, "momentum": 0.55, "low_vol": 0.35, "dividend": 0.2, "leverage": 0.65, "profitability": 0.55},
            ).to_dict(),
            Holding(
                "ASIANPAINT",
                0.05,
                "fmcg",
                "decorative_paints",
                "IN",
                "large",
                "quality",
                "Brand + distribution pricing power",
                "medium",
                "2020-11-01",
                2800.0,
                {"quality": 0.85, "value": 0.25, "growth": 0.5, "momentum": 0.3, "low_vol": 0.7, "dividend": 0.4, "leverage": 0.15, "profitability": 0.82},
            ).to_dict(),
            Holding(
                "AXISBANK",
                0.05,
                "banks",
                "private_bank",
                "IN",
                "large",
                "blend",
                "Franchise recovery / underwriting watch",
                "low",
                "2024-08-01",
                1100.0,
                {"quality": 0.55, "value": 0.55, "growth": 0.5, "momentum": 0.4, "low_vol": 0.4, "dividend": 0.25, "leverage": 0.6, "profitability": 0.58},
            ).to_dict(),
            Holding(
                "ETERNAL",
                0.04,
                "consumer_internet",
                "food_delivery",
                "IN",
                "large",
                "growth",
                "Unit economics path + competitive intensity watch",
                "low",
                "2025-01-15",
                220.0,
                {"quality": 0.45, "value": 0.3, "growth": 0.85, "momentum": 0.6, "low_vol": 0.2, "dividend": 0.0, "leverage": 0.25, "profitability": 0.35},
            ).to_dict(),
        ],
        "cash_weight": 0.27,
        "watchlist": [
            {"ticker": "KOTAKBANK", "priority": "research", "note": "Private bank diversification vs HDFC/ICICI overlap"},
            {"ticker": "HINDUNILVR", "priority": "monitor", "note": "Staples quality; valuation discipline required"},
            {"ticker": "SBIN", "priority": "research", "note": "PSU bank — portfolio fit only if quality gates clear"},
        ],
        "benchmark_sector_weights": {
            "banks": 0.28,
            "it_services": 0.14,
            "fmcg": 0.10,
            "energy_conglomerate": 0.10,
            "telecom": 0.04,
            "consumer_internet": 0.03,
            "cash": 0.0,
        },
    }
}


def list_portfolios() -> list[str]:
    return sorted(PORTFOLIOS.keys())


def portfolio_for(portfolio_id: str) -> dict[str, Any] | None:
    pid = (portfolio_id or "").strip().lower().replace(" ", "_")
    aliases = {
        "default": "agib_core_india",
        "core": "agib_core_india",
        "india": "agib_core_india",
        "agib": "agib_core_india",
    }
    pid = aliases.get(pid, pid)
    p = PORTFOLIOS.get(pid)
    return dict(p) if p else None


def default_portfolio_id() -> str:
    return "agib_core_india"
