"""Finance Academy service facade."""

from __future__ import annotations

from typing import Any

from academy.service import AcademyCore
from app.academy.flags import AcademyFlags
from app.academy.store import AcademyStore
from app.core.config import get_settings


class AcademyService:
    """Library access layer for the AGI Finance Academy curriculum."""

    def __init__(
        self,
        *,
        flags: AcademyFlags | None = None,
        store: AcademyStore | None = None,
        core: AcademyCore | None = None,
    ) -> None:
        self.flags = flags or AcademyFlags.from_settings(get_settings())
        self.store = store or AcademyStore()
        self.core = core or AcademyCore()

    def _require(self) -> None:
        if not self.flags.academy:
            raise RuntimeError("Finance Academy is disabled (ACADEMY=false)")

    def health(self) -> dict[str, Any]:
        body = self.core.health(enabled=self.flags.academy)
        body["flags"] = self.flags.as_dict()
        body["snapshot"] = self.store.snapshot() if self.flags.academy else {}
        return body

    def dashboard(self) -> dict[str, Any]:
        self._require()
        out = self.core.dashboard()
        out["flags"] = self.flags.as_dict()
        out["metrics"] = self.store.metrics.model_dump()
        return out

    def course(self) -> dict[str, Any]:
        self._require()
        return self.core.course()

    def list_concepts(self, tag: str | None = None) -> dict[str, Any]:
        self._require()
        return self.core.list_concepts(tag=tag)

    def get_concept(self, concept_id: str) -> dict[str, Any]:
        self._require()
        out = self.core.get_concept(concept_id)
        self.store.observe("concept", {"concept_id": concept_id})
        return out

    def teach(self, concept_id: str) -> dict[str, Any]:
        self._require()
        out = self.core.teach(concept_id)
        self.store.observe("teach", {"concept_id": concept_id})
        return out

    def graph(self) -> dict[str, Any]:
        self._require()
        return self.core.graph()

    def neighborhood(self, concept_id: str) -> dict[str, Any]:
        self._require()
        return self.core.neighborhood(concept_id)

    def causal_models(self) -> dict[str, Any]:
        self._require()
        return self.core.causal_models()

    def mental_models(self) -> dict[str, Any]:
        self._require()
        return self.core.mental_models()

    def quality(self) -> dict[str, Any]:
        self._require()
        return self.core.quality()

    def provenance(self) -> dict[str, Any]:
        self._require()
        if not self.flags.academy_provenance:
            return {"enabled": False}
        return self.core.provenance()

    def enrich(self, concept_id: str) -> dict[str, Any]:
        self._require()
        return self.core.enrich(concept_id)

    def exams(self) -> dict[str, Any]:
        self._require()
        if not self.flags.academy_exams:
            return {"enabled": False}
        out = self.core.exams()
        self.store.observe("exam", {"suite": True})
        return out

    def answer(self, question_id: str) -> dict[str, Any]:
        self._require()
        out = self.core.answer(question_id)
        self.store.observe("exam", {"question_id": question_id})
        return out

    def consumer(self, engine: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        self._require()
        out = self.core.consumer(engine, payload)
        self.store.observe("consumer", {"engine": engine})
        return out

    def search(self, q: str, limit: int = 20) -> dict[str, Any]:
        self._require()
        out = self.core.search(q, limit=limit)
        self.store.observe("search", {"q": q})
        return out

    def completion(self) -> dict[str, Any]:
        self._require()
        return self.core.completion()

    def metrics(self) -> dict[str, Any]:
        self._require()
        return self.store.snapshot()
