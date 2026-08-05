"""Institutional writing benchmark package."""

from institutional_writing_benchmark.hall_of_fame import (
    HALL_OF_FAME_COUNT,
    compare_and_maybe_update,
    hall_of_fame_ids,
    load_hall_of_fame,
)
from institutional_writing_benchmark.registry import (
    BENCHMARK_QUESTIONS,
    get_benchmark,
    get_playbook,
    list_benchmarks,
    list_playbooks,
    phase2_expansion_plan,
)
from institutional_writing_benchmark.schema import (
    LIFECYCLE_PLAYBOOKS,
    PHASE2_COMPANIES,
    PHASE2_TARGET_BENCHMARK_COUNT,
    PLAYBOOK_COUNT,
    PLAYBOOK_TITLES,
    QUESTIONS_PER_PLAYBOOK,
    TARGET_BENCHMARK_COUNT,
)

__all__ = [
    "BENCHMARK_QUESTIONS",
    "HALL_OF_FAME_COUNT",
    "LIFECYCLE_PLAYBOOKS",
    "PHASE2_COMPANIES",
    "PHASE2_TARGET_BENCHMARK_COUNT",
    "PLAYBOOK_COUNT",
    "PLAYBOOK_TITLES",
    "QUESTIONS_PER_PLAYBOOK",
    "TARGET_BENCHMARK_COUNT",
    "compare_and_maybe_update",
    "get_benchmark",
    "get_playbook",
    "hall_of_fame_ids",
    "list_benchmarks",
    "list_playbooks",
    "load_hall_of_fame",
    "phase2_expansion_plan",
]
