"""Living peer packs."""

from __future__ import annotations

from typing import Any

from peer_intelligence.peer_database.packs import (
    banks_india,
    consumer_internet,
    fmcg_india,
    it_services,
)

PACKS = {
    banks_india.PACK_ID: banks_india.pack,
    fmcg_india.PACK_ID: fmcg_india.pack,
    it_services.PACK_ID: it_services.pack,
    consumer_internet.PACK_ID: consumer_internet.pack,
}


def all_packs() -> list[dict[str, Any]]:
    return [fn() for fn in PACKS.values()]


def pack_by_id(pack_id: str) -> dict[str, Any] | None:
    fn = PACKS.get(pack_id)
    return fn() if fn else None
