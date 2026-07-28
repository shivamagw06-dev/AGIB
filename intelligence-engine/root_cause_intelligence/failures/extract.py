"""Extract structured failures from an IEL suite summary."""

from __future__ import annotations

from typing import Any

from root_cause_intelligence.failures.models import build_failure


def extract_failures(scored_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in scored_rows or []:
        if row.get("passed"):
            continue
        out.append(build_failure(row))
    return out
