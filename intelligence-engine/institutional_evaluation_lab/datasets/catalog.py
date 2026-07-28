"""Unified question catalog — CIO gold + institutional 1000+."""

from __future__ import annotations

from typing import Any

from institutional_evaluation_lab.datasets.cio_frozen_25 import CIO_FROZEN_25
from institutional_evaluation_lab.datasets.generator import generate_institutional_library

_CACHE: dict[str, list[dict[str, Any]]] = {}


def load_suite(suite: str = "institutional_1000") -> list[dict[str, Any]]:
    if suite in _CACHE:
        return list(_CACHE[suite])
    if suite == "cio_frozen_25":
        rows = list(CIO_FROZEN_25)
    elif suite == "smoke":
        rows = list(CIO_FROZEN_25[:5]) + generate_institutional_library(target=20)[:15]
    elif suite in {"institutional_1000", "all"}:
        gen = generate_institutional_library(target=1000)
        if suite == "all":
            rows = list(CIO_FROZEN_25) + gen
        else:
            rows = gen
    else:
        raise ValueError(f"unknown_suite:{suite}")
    _CACHE[suite] = rows
    return list(rows)


def catalog_stats() -> dict[str, Any]:
    cio = load_suite("cio_frozen_25")
    inst = load_suite("institutional_1000")
    all_rows = load_suite("all")
    by_cat: dict[str, int] = {}
    for r in all_rows:
        by_cat[str(r.get("category"))] = by_cat.get(str(r.get("category")), 0) + 1
    return {
        "cio_frozen_25": len(cio),
        "institutional_1000": len(inst),
        "all": len(all_rows),
        "by_category": by_cat,
        "min_required": 1000,
        "meets_1000_plus": len(inst) >= 1000,
    }


def get_question(question_id: str) -> dict[str, Any] | None:
    for suite in ("cio_frozen_25", "institutional_1000"):
        for q in load_suite(suite):
            if q.get("question_id") == question_id:
                return q
    return None
