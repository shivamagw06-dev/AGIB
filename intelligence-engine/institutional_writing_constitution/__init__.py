"""Institutional Writing Constitution v1.0 — IRE communication layer."""

from institutional_writing_constitution.assembler import assemble_writing_sections, infer_answer_length
from institutional_writing_constitution.evaluation import (
    BENCHMARK_QUESTIONS,
    evaluation_rubric,
    list_benchmark_questions,
    score_writing_pack,
)
from institutional_writing_constitution.production import apply_institutional_writing_constitution, health
from institutional_writing_constitution.schema import CONSTITUTION_VERSION, RESPONSE_HIERARCHY
from institutional_writing_constitution.validation import validate_writing_response

__all__ = [
    "BENCHMARK_QUESTIONS",
    "CONSTITUTION_VERSION",
    "RESPONSE_HIERARCHY",
    "apply_institutional_writing_constitution",
    "assemble_writing_sections",
    "evaluation_rubric",
    "health",
    "infer_answer_length",
    "list_benchmark_questions",
    "score_writing_pack",
    "validate_writing_response",
]
