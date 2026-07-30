"""Production façades for Nifty / NSE index constituents."""

from __future__ import annotations

from typing import Any

from market_indices.loader import (
    dashboard,
    get_index,
    health,
    list_indices,
    list_members,
    membership_for_symbol,
    search_index,
)


def soft_slice_for_ask_agi(question: str = "", payload: dict[str, Any] | None = None) -> dict[str, Any]:
    _ = payload
    idx = search_index(question) if question else None
    return {
        "market_indices": {
            "enabled": True,
            "matched_index": {
                "index_id": idx.get("index_id"),
                "display_name": idx.get("display_name"),
                "count": idx.get("count"),
            }
            if idx
            else None,
            "health": {"index_count": health().get("available_count")},
        }
    }


__all__ = [
    "dashboard",
    "get_index",
    "health",
    "list_indices",
    "list_members",
    "membership_for_symbol",
    "search_index",
    "soft_slice_for_ask_agi",
]
