"""Durable, read-only snapshot for the Global Markets client surface.

The Global Markets HTTP request must never compose the macro pack, fetch a
vendor, calculate history, or invoke an LLM.  Those jobs run in the macro
runtime; this module only atomically writes their completed output and reads it
back for the web API.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _root() -> Path:
    raw = (os.getenv("KIP_DATA_DIR") or os.getenv("INSTITUTIONAL_WAREHOUSE_ROOT") or "").strip()
    root = Path(raw) if raw else Path(__file__).resolve().parents[1] / "data"
    path = root / "global_market_snapshots"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _key(country: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in (country or "India")).strip("_") or "india"


def _path(country: str) -> Path:
    return _root() / f"{_key(country)}.json"


def save(pack: dict[str, Any], *, country: str) -> dict[str, Any]:
    """Persist a completed runtime pack.  A failed pack is never published."""
    if not isinstance(pack, dict) or not pack.get("ok"):
        return {"ok": False, "reason": "pack_not_publishable"}
    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "ok": True,
        "snapshot_type": "global_macro_snapshot",
        "country": country,
        "generated_at": pack.get("generated_at") or now,
        "published_at": now,
        "data_status": "CACHED",
        "source": "macro_intelligence_runtime",
        "pack": pack,
    }
    target = _path(country)
    temp = target.with_suffix(".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    temp.replace(target)
    return {"ok": True, "path": str(target), "published_at": now}


def read(country: str = "Global") -> dict[str, Any]:
    """Return the latest saved snapshot only; this function performs no calculation."""
    requested = (country or "Global").strip() or "Global"
    candidates = [requested]
    # Global data is introduced independently. Until its feed is connected, the
    # India macro snapshot gives the page an honest India-first read-through.
    if requested.lower() == "global":
        candidates.append("India")
    for candidate in candidates:
        try:
            payload = json.loads(_path(candidate).read_text(encoding="utf-8"))
            if isinstance(payload, dict) and isinstance(payload.get("pack"), dict):
                payload["requested_scope"] = requested
                payload["served_scope"] = candidate
                payload["fallback"] = candidate.lower() != requested.lower()
                return payload
        except FileNotFoundError:
            continue
        except Exception as exc:
            return {
                "ok": False,
                "snapshot_type": "global_macro_snapshot",
                "requested_scope": requested,
                "status": "DATA_QUALITY_WARNING",
                "error": f"snapshot_unreadable:{str(exc)[:120]}",
            }
    return {
        "ok": False,
        "snapshot_type": "global_macro_snapshot",
        "requested_scope": requested,
        "status": "AWAITING_SNAPSHOT",
        "message": "The global snapshot has not been published by the background macro runtime yet.",
    }
