"""Institutional writing benchmark — editorial curriculum registry."""

from __future__ import annotations

from typing import Any

from institutional_writing_benchmark.schema import (
    LIFECYCLE_PLAYBOOKS,
    PHASE2_COMPANIES,
    PHASE2_TARGET_BENCHMARK_COUNT,
    PLAYBOOK_COUNT,
    PLAYBOOK_TITLES,
    QUESTIONS_PER_PLAYBOOK,
    TARGET_BENCHMARK_COUNT,
)
from institutional_writing_benchmark.tcs_curriculum import TCS_CURRICULUM

BENCHMARK_QUESTIONS: tuple[dict[str, Any], ...] = TCS_CURRICULUM


def list_playbooks() -> list[dict[str, Any]]:
    """Return 20 lifecycle playbooks with metadata."""
    return [
        {
            "playbook": slug,
            "title": PLAYBOOK_TITLES[slug],
            "playbook_number": i + 1,
            "questions_per_playbook": QUESTIONS_PER_PLAYBOOK,
            "question_ids": [
                q["id"]
                for q in BENCHMARK_QUESTIONS
                if q.get("playbook") == slug
            ],
        }
        for i, slug in enumerate(LIFECYCLE_PLAYBOOKS)
    ]


def list_benchmarks(
    *,
    category: str | None = None,
    playbook: str | None = None,
    ticker: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    items = list(BENCHMARK_QUESTIONS)
    if category:
        items = [q for q in items if q.get("category") == category or q.get("playbook") == category]
    if playbook:
        items = [q for q in items if q.get("playbook") == playbook]
    if ticker:
        items = [q for q in items if q.get("ticker") == ticker]
    return items[:limit]


def get_benchmark(benchmark_id: str) -> dict[str, Any] | None:
    for q in BENCHMARK_QUESTIONS:
        if q.get("id") == benchmark_id:
            return dict(q)
    return None


def get_playbook(playbook: str) -> dict[str, Any] | None:
    questions = list_benchmarks(playbook=playbook)
    if not questions:
        return None
    return {
        "playbook": playbook,
        "title": PLAYBOOK_TITLES.get(playbook, playbook),
        "questions": questions,
    }


def phase2_expansion_plan() -> dict[str, Any]:
    """Phase 2 — replicate TCS curriculum for 10 additional companies → 1,000 questions."""
    return {
        "phase": 2,
        "anchor_complete": "TCS",
        "companies_pending": [{"ticker": t, "company": n} for t, n in PHASE2_COMPANIES],
        "questions_per_company": TARGET_BENCHMARK_COUNT,
        "playbooks_per_company": PLAYBOOK_COUNT,
        "target_total": PHASE2_TARGET_BENCHMARK_COUNT,
        "method": "Replicate 20 playbooks × 5 questions per company after TCS curriculum is consistently excellent.",
    }
