"""KIP feature flags — Architecture v1.0.1 P0 defaults."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import Settings, get_settings


@dataclass(frozen=True)
class KipFlags:
    kip: bool = True
    kip_rag: bool = True
    kip_graph: bool = True
    kip_versioning: bool = True
    kip_ocr: bool = True
    kip_llm_summary: bool = True

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> "KipFlags":
        s = settings or get_settings()
        return cls(
            kip=bool(getattr(s, "kip", True)),
            kip_rag=bool(getattr(s, "kip_rag", True)),
            kip_graph=bool(getattr(s, "kip_graph", True)),
            kip_versioning=bool(getattr(s, "kip_versioning", True)),
            kip_ocr=bool(getattr(s, "kip_ocr", True)),
            kip_llm_summary=bool(getattr(s, "kip_llm_summary", True)),
        )

    def as_dict(self) -> dict[str, bool]:
        return {
            "KIP": self.kip,
            "KIP_RAG": self.kip_rag,
            "KIP_GRAPH": self.kip_graph,
            "KIP_VERSIONING": self.kip_versioning,
            "KIP_OCR": self.kip_ocr,
            "KIP_LLM_SUMMARY": self.kip_llm_summary,
        }
