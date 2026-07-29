"""Extract structured institutional knowledge from gathered packs.

This is NOT ML model training. It materialises trends, metrics, and themes
that analyst agents can consume on future runs.
"""

from __future__ import annotations

from typing import Any

from continuous_gather_learn import persist as cgl_persist


def _num(v: Any) -> float | None:
    try:
        if v is None:
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def extract_from_hd_pack(pack: dict[str, Any] | None, *, entity: str) -> dict[str, Any]:
    """Soft extraction from a Historical Depth / company pack."""
    pack = pack if isinstance(pack, dict) else {}
    financials = pack.get("financials") or pack.get("financial_history") or {}
    prices = pack.get("prices") or pack.get("ohlcv") or pack.get("market_history") or {}
    narrative = pack.get("narrative") or pack.get("summary") or {}

    metrics: dict[str, Any] = {
        "revenue_cagr": _num(financials.get("revenue_cagr") or financials.get("sales_cagr")),
        "ebitda_cagr": _num(financials.get("ebitda_cagr")),
        "margin_trend": financials.get("margin_trend") or financials.get("operating_margin_trend"),
        "debt_trend": financials.get("debt_trend"),
        "roe_history": financials.get("roe_history") or financials.get("roe"),
        "roce_history": financials.get("roce_history") or financials.get("roce"),
        "cash_conversion": financials.get("cash_conversion"),
        "avg_return": _num(prices.get("avg_return") or prices.get("mean_return")),
        "volatility": _num(prices.get("volatility") or prices.get("stdev")),
        "max_drawdown": _num(prices.get("max_drawdown") or prices.get("drawdown")),
        "beta": _num(prices.get("beta")),
    }
    themes = list(pack.get("themes") or narrative.get("themes") or [])[:12]
    risks = list(pack.get("risks") or narrative.get("risks") or [])[:8]
    catalysts = list(pack.get("catalysts") or [])[:8]

    out = {
        "entity": entity,
        "kind": "structured_knowledge_extract",
        "metrics": {k: v for k, v in metrics.items() if v is not None},
        "themes": themes,
        "risks": risks,
        "catalysts": catalysts,
        "provenance": {
            "source": "knowledge_factory_historical_depth",
            "keys_seen": sorted(list(pack.keys())[:40]),
        },
        "learning_mode": "structured_extraction_not_ml_training",
    }
    cgl_persist.put_knowledge_extract(entity, out)
    return out


def extract_batch_from_daily_report(report: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Walk a KF daily / HD report and extract per-entity knowledge when present."""
    report = report if isinstance(report, dict) else {}
    out: list[dict[str, Any]] = []
    entities = (
        report.get("entities")
        or report.get("tickers")
        or report.get("updated_entities")
        or []
    )
    packs = report.get("packs") or report.get("entity_packs") or {}
    if isinstance(entities, dict):
        entities = list(entities.keys())
    for ent in list(entities)[:40]:
        key = str(ent)
        pack = packs.get(key) if isinstance(packs, dict) else None
        if not isinstance(pack, dict):
            # Still record a thin extract so coverage grows.
            pack = {"summary": report.get("summary") or {}}
        out.append(extract_from_hd_pack(pack, entity=key))
    if not out and report:
        out.append(
            extract_from_hd_pack(
                {"summary": report.get("summary") or report.get("status")},
                entity=str(report.get("universe") or "UNIVERSE"),
            )
        )
    return out
