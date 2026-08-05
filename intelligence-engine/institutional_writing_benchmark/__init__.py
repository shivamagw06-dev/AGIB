"""Institutional writing benchmark package."""

from institutional_writing_benchmark.hall_of_fame import (
    HALL_OF_FAME_COUNT,
    compare_and_maybe_update,
    hall_of_fame_ids,
    load_hall_of_fame,
)
from institutional_writing_benchmark.schema import HALL_OF_FAME_COUNT, TARGET_BENCHMARK_COUNT
from institutional_writing_benchmark.registry import (
    BENCHMARK_QUESTIONS,
    TARGET_BENCHMARK_COUNT,
    get_benchmark,
    list_benchmarks,
)

__all__ = [
    "BENCHMARK_QUESTIONS",
    "HALL_OF_FAME_COUNT",
    "TARGET_BENCHMARK_COUNT",
    "compare_and_maybe_update",
    "get_benchmark",
    "hall_of_fame_ids",
    "list_benchmarks",
    "load_hall_of_fame",
]
