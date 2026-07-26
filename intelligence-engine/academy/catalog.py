"""Multi-course catalog — additive aggregation without redesigning Academy APIs."""

from __future__ import annotations

from typing import Any

from academy import accounting
from academy.accounting import causal_models as acc_causal
from academy.accounting import mental_models as acc_mental
from academy.accounting import teaching as acc_teaching
from academy.accounting.curriculum import CONCEPT_CHAPTER_MAP as ACC_CHAPTER_MAP
from academy.accounting.curriculum import course_manifest as accounting_manifest
from academy.accounting.earnings_quality import score_earnings_quality
from academy.accounting.knowledge_objects import all_knowledge_objects as accounting_objects
from academy.accounting.red_flags import list_red_flags, score_red_flags
from academy.causal_models import all_causal_models as economics_causal
from academy.curriculum import CONCEPT_CHAPTER_MAP as ECO_CHAPTER_MAP
from academy.curriculum import course_manifest as economics_manifest
from academy.knowledge_objects import all_knowledge_objects as economics_objects
from academy.mental_models import all_mental_models as economics_mental
from academy.schema import ACADEMY_VERSION, COURSE_ID, KnowledgeObject
from academy.teaching import EXAMS as ECO_EXAMS
from academy.teaching import answer_question as eco_answer
from academy.teaching import run_exam_suite as eco_exams
from academy.teaching import teach as eco_teach


def list_courses() -> list[dict[str, Any]]:
    return [economics_manifest(), accounting_manifest()]


def course_manifest(course_id: str | None = None) -> dict[str, Any]:
    if not course_id or course_id in (COURSE_ID, "economics", "mankiw"):
        return economics_manifest()
    if course_id in (accounting.COURSE_ID, "accounting", "damodaran", "minimalist_accounting"):
        return accounting_manifest()
    raise KeyError(f"Unknown course: {course_id}")


def all_knowledge_objects(course_id: str | None = None) -> list[KnowledgeObject]:
    eco = economics_objects()
    for k in eco:
        if not k.course_id:
            k.course_id = COURSE_ID
        if "course:economics" not in k.tags:
            k.tags = list(k.tags) + ["course:economics"]
    acc = accounting_objects()
    if course_id in (None, "", "all"):
        return eco + acc
    if course_id in (COURSE_ID, "economics", "mankiw"):
        return eco
    if course_id in (accounting.COURSE_ID, "accounting", "damodaran", "minimalist_accounting"):
        return acc
    raise KeyError(f"Unknown course: {course_id}")


def knowledge_by_id() -> dict[str, KnowledgeObject]:
    return {k.concept_id: k for k in all_knowledge_objects()}


def list_concept_ids(course_id: str | None = None) -> list[str]:
    return [k.concept_id for k in all_knowledge_objects(course_id)]


def concept_chapter_map() -> dict[str, int]:
    out = dict(ECO_CHAPTER_MAP)
    out.update(ACC_CHAPTER_MAP)
    return out


def all_causal_models():
    return economics_causal() + acc_causal.all_causal_models()


def all_mental_models():
    return economics_mental() + acc_mental.all_mental_models()


def all_exams() -> list[dict[str, Any]]:
    eco = [{**e, "course": COURSE_ID} for e in ECO_EXAMS]
    acc = [{**e, "course": accounting.COURSE_ID} for e in acc_teaching.EXAMS]
    return eco + acc


def answer_question(question_id: str) -> dict[str, Any]:
    try:
        return eco_answer(question_id)
    except KeyError:
        return acc_teaching.answer_question(question_id)


def run_exam_suite(course_id: str | None = None) -> dict[str, Any]:
    if course_id in (accounting.COURSE_ID, "accounting", "damodaran"):
        return acc_teaching.run_exam_suite()
    if course_id in (COURSE_ID, "economics", "mankiw"):
        return eco_exams()
    eco = eco_exams()
    acc = acc_teaching.run_exam_suite()
    return {
        "total": eco["total"] + acc["total"],
        "passed": eco["passed"] + acc["passed"],
        "failed": eco["failed"] + acc["failed"],
        "complete": eco["complete"] and acc["complete"],
        "by_course": {
            COURSE_ID: eco,
            accounting.COURSE_ID: acc,
        },
    }


def teach(concept_id: str) -> dict[str, Any]:
    kb = knowledge_by_id()
    if concept_id not in kb:
        raise KeyError(concept_id)
    if kb[concept_id].course_id == accounting.COURSE_ID or "course:accounting" in kb[concept_id].tags:
        return acc_teaching.teach(concept_id)
    return eco_teach(concept_id)


def accounting_toolkit() -> dict[str, Any]:
    return {
        "course": accounting_manifest(),
        "red_flags": list_red_flags(),
        "earnings_quality_methodology": score_earnings_quality({}),
        "version": ACADEMY_VERSION,
    }
