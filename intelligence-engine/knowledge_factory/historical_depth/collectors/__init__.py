"""Historical collectors — fixture-first, append-only into HD store."""

from __future__ import annotations

from typing import Any

from knowledge_factory.historical_depth import store as hd_store
from knowledge_factory.historical_depth.fixtures.seed_history import (
    annual_records,
    corporate_action_records,
    macro_history,
    market_regimes,
    monthly_prices,
    quarterly_records,
    seed_universe,
    timeline_records,
)


def collect_entity_history(entity: str) -> dict[str, Any]:
    e = entity.upper()
    annual = annual_records(e)
    quarterly = quarterly_records(e)
    prices = monthly_prices(e)
    actions = corporate_action_records(e)
    timeline = timeline_records(e)

    hd_store.put_series("financials_annual", e, annual)
    hd_store.put_series("financials_quarterly", e, quarterly)
    hd_store.put_series("prices", e, prices)
    hd_store.put_series("corporate_actions", e, actions)
    hd_store.put_series("timeline", e, timeline)

    years = len(annual)
    return {
        "entity": e,
        "annual_periods": years,
        "quarterly_periods": len(quarterly),
        "price_points": len(prices),
        "timeline_events": len(timeline),
        "corporate_actions": len(actions),
        "history_years": years,
        "status": "ok",
    }


def collect_market_history() -> dict[str, Any]:
    regimes = market_regimes()
    macro = macro_history()
    hd_store.put_regimes(regimes)
    hd_store.put_macro_history(macro)
    return {"regimes": len(regimes), "macro_periods": len(macro), "status": "ok"}


def collect_universe(entities: list[str] | None = None) -> dict[str, Any]:
    entities = entities or seed_universe()
    market = collect_market_history()
    rows = []
    for e in entities:
        rows.append(collect_entity_history(e))
    return {
        "entities": len(rows),
        "market": market,
        "rows": rows,
        "status": "ok",
    }
