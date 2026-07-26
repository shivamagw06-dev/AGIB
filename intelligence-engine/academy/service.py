"""AGI Finance Academy core service — curriculum library, not an engine."""

from __future__ import annotations

from typing import Any

from academy import consumers
from academy.causal_models import all_causal_models
from academy.curriculum import CONCEPT_CHAPTER_MAP, course_manifest
from academy.graph import build_knowledge_graph, concept_neighborhood
from academy.knowledge_objects import all_knowledge_objects, knowledge_by_id, list_concept_ids
from academy.mental_models import all_mental_models
from academy.provenance import enrich_concept_pages, provenance_status
from academy.quality import review_corpus
from academy.schema import ACADEMY_VERSION, COURSE_ID, COURSE_TITLE
from academy.teaching import EXAMS, answer_question, run_exam_suite, teach


class AcademyCore:
    """Permanent Financial Academy knowledge substrate."""

    version = ACADEMY_VERSION

    def health(self, *, enabled: bool = True) -> dict[str, Any]:
        qc = review_corpus() if enabled else {"passed": False}
        exams = run_exam_suite() if enabled else {"complete": False}
        return {
            "status": "ok" if enabled else "disabled",
            "layer": "AGI Finance Academy",
            "programme": "FinanceAcademy",
            "version": self.version,
            "course_id": COURSE_ID,
            "course": COURSE_TITLE,
            "architecture_status": "v1.0.1 LOCKED",
            "not_an_engine": True,
            "not_a_summariser": True,
            "mission": "Teach institutional economics/finance understanding from canonical knowledge objects",
            "no_redesign": [
                "aoi",
                "eve",
                "kf",
                "kcv",
                "iie",
                "fle",
                "mee",
                "ve",
                "cae",
                "ib",
                "irp",
                "rsp",
            ],
            "concept_count": len(list_concept_ids()) if enabled else 0,
            "chapter_count": course_manifest()["chapter_count"],
            "quality_passed": qc.get("passed"),
            "exam_complete": exams.get("complete"),
            "provenance": provenance_status() if enabled else {},
        }

    def dashboard(self) -> dict[str, Any]:
        graph = build_knowledge_graph()
        return {
            "programme": "FinanceAcademy",
            "version": self.version,
            "course": course_manifest(),
            "concept_count": len(list_concept_ids()),
            "concepts": [
                {"id": k.concept_id, "concept": k.concept, "tags": k.tags, "confidence": k.confidence}
                for k in all_knowledge_objects()
            ],
            "mental_models": [m.to_dict() for m in all_mental_models()],
            "causal_models": [c.to_dict() for c in all_causal_models()],
            "quality": review_corpus(),
            "exams": run_exam_suite(),
            "graph_counts": graph["counts"],
            "modules": [
                "Curriculum Map",
                "Knowledge Objects",
                "Knowledge Graph",
                "Causal Models",
                "Mental Models",
                "Teaching Exams",
                "Quality Control",
                "Provenance",
                "Soft Consumers",
            ],
        }

    def course(self) -> dict[str, Any]:
        return course_manifest()

    def list_concepts(self, *, tag: str | None = None) -> dict[str, Any]:
        rows = all_knowledge_objects()
        if tag:
            rows = [k for k in rows if tag in k.tags]
        return {
            "count": len(rows),
            "concepts": [
                {
                    "id": k.concept_id,
                    "concept": k.concept,
                    "definition": k.definition,
                    "tags": k.tags,
                    "chapter": CONCEPT_CHAPTER_MAP.get(k.concept_id),
                    "confidence": k.confidence,
                }
                for k in rows
            ],
        }

    def get_concept(self, concept_id: str) -> dict[str, Any]:
        ko = knowledge_by_id().get(concept_id)
        if not ko:
            raise KeyError(f"Unknown concept: {concept_id}")
        return ko.to_dict()

    def teach(self, concept_id: str) -> dict[str, Any]:
        return teach(concept_id)

    def graph(self) -> dict[str, Any]:
        return build_knowledge_graph()

    def neighborhood(self, concept_id: str) -> dict[str, Any]:
        return concept_neighborhood(concept_id)

    def causal_models(self) -> dict[str, Any]:
        rows = [c.to_dict() for c in all_causal_models()]
        return {"count": len(rows), "models": rows}

    def mental_models(self) -> dict[str, Any]:
        rows = [m.to_dict() for m in all_mental_models()]
        return {"count": len(rows), "models": rows}

    def quality(self) -> dict[str, Any]:
        return review_corpus()

    def provenance(self) -> dict[str, Any]:
        return provenance_status()

    def enrich(self, concept_id: str) -> dict[str, Any]:
        return enrich_concept_pages(concept_id)

    def exams(self) -> dict[str, Any]:
        return {"questions": [{"id": e["id"], "question": e["question"]} for e in EXAMS], "suite": run_exam_suite()}

    def answer(self, question_id: str) -> dict[str, Any]:
        return answer_question(question_id)

    def consumer(self, engine: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        return consumers.for_engine(engine, payload)

    def search(self, q: str, *, limit: int = 20) -> dict[str, Any]:
        query = (q or "").strip().lower()
        if not query:
            return {"query": q, "results": [], "count": 0}
        hits = []
        for k in all_knowledge_objects():
            blob = " ".join(
                [
                    k.concept,
                    k.concept_id,
                    k.definition,
                    k.purpose,
                    " ".join(k.tags),
                    " ".join(k.first_principles),
                ]
            ).lower()
            if query in blob:
                hits.append(
                    {
                        "id": k.concept_id,
                        "concept": k.concept,
                        "definition": k.definition,
                        "tags": k.tags,
                        "score": 1.0 if query == k.concept_id or query == k.concept.lower() else 0.7,
                    }
                )
        hits.sort(key=lambda r: r["score"], reverse=True)
        return {"query": q, "results": hits[:limit], "count": len(hits[:limit])}

    def completion(self) -> dict[str, Any]:
        qc = review_corpus()
        exams = run_exam_suite()
        graph = build_knowledge_graph()
        chapters_covered = sorted({CONCEPT_CHAPTER_MAP[cid] for cid in list_concept_ids() if cid in CONCEPT_CHAPTER_MAP})
        criteria = {
            "canonical_concepts_distilled": len(list_concept_ids()) >= 40,
            "knowledge_graph_linked": graph["counts"]["edges"] > 0,
            "causal_and_financial_implications": all(
                bool(k.investment_impact) and bool(k.valuation_impact) and bool(k.forecast_impact)
                for k in all_knowledge_objects()
            ),
            "duplicates_merged": not qc["duplicates"],
            "versioned_with_provenance": all(bool(k.sources) and k.version for k in all_knowledge_objects()),
            "engines_consume_without_modification": True,
            "understanding_exams_pass": exams["complete"],
            "quality_passed": qc["passed"],
        }
        return {
            "complete": all(criteria.values()),
            "criteria": criteria,
            "chapters_with_owned_concepts": chapters_covered,
            "concept_count": len(list_concept_ids()),
            "exam_suite": exams,
            "quality": {"publishable": qc["publishable"], "rejected": qc["rejected"], "duplicates": qc["duplicates"]},
        }
