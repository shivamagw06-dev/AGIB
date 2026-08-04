"""Ingest exchange-level FII/DII into warehouse via DQIV gateway."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

SOURCE = "upstox"


def normalise_upstox_flow(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalise Upstox market/fii and market/dii responses into warehouse rows."""
    date = str(payload.get("date") or datetime.now(timezone.utc).date().isoformat())
    segment = str(payload.get("segment") or "NSE_EQ")
    fii = payload.get("fii") or {}
    dii = payload.get("dii") or {}

    def _net(block: dict[str, Any]) -> float | None:
        buy = block.get("buy") or block.get("net_buy") or block.get("purchase")
        sell = block.get("sell") or block.get("net_sell") or block.get("sales")
        try:
            if buy is not None and sell is not None:
                return round(float(buy) - float(sell), 2)
            if block.get("net") is not None:
                return round(float(block["net"]), 2)
        except (TypeError, ValueError):
            return None
        return None

    row = {
        "date": date,
        "segment": segment,
        "fii_net": _net(fii),
        "dii_net": _net(dii),
        "fii_buy": fii.get("buy") or fii.get("purchase"),
        "fii_sell": fii.get("sell") or fii.get("sales"),
        "dii_buy": dii.get("buy") or dii.get("purchase"),
        "dii_sell": dii.get("sell") or dii.get("sales"),
        "source": SOURCE,
    }
    return [row]


def ingest_flows(rows: list[dict[str, Any]], *, actor: str = "market_intelligence_engine") -> dict[str, Any]:
    from institutional_warehouse import gateway

    if not rows:
        return {"ok": False, "error": "no_rows"}
    result = gateway.write("institutional_flow", rows, source=SOURCE, actor=actor)
    return {"ok": True, **result}
