"""Optional PDF provenance enrichment — never requires committing the book."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from academy.curriculum import CHAPTERS, PDF_PAGE_OFFSET, chapter_meta


DEFAULT_PDF_CANDIDATES = [
    Path("/workspace/books/Mankiw_Principles_of_Economics.pdf"),
    Path.home() / "Downloads" / "AGIB" / "books" / "Mankiw_Principles_of_Economics.pdf",
    Path.home() / "Downloads" / "AGIB" / "Books" / "Mankiw_Principles_of_Economics.pdf",
]


def locate_pdf(explicit: str | None = None) -> Path | None:
    if explicit:
        p = Path(explicit)
        return p if p.exists() else None
    env = os.environ.get("AGI_ACADEMY_MANKIW_PDF")
    if env and Path(env).exists():
        return Path(env)
    for cand in DEFAULT_PDF_CANDIDATES:
        if cand.exists():
            return cand
    return None


def provenance_status(pdf_path: str | None = None) -> dict[str, Any]:
    path = locate_pdf(pdf_path)
    chapters = []
    for row in CHAPTERS:
        meta = chapter_meta(row["chapter"])
        chapters.append(
            {
                "chapter": meta["chapter"],
                "title": meta["title"],
                "printed_page": meta["printed_page"],
                "pdf_page_estimate": meta["pdf_page"],
            }
        )
    page_count = None
    if path is not None:
        try:
            from pypdf import PdfReader

            page_count = len(PdfReader(str(path)).pages)
        except Exception as exc:  # noqa: BLE001 — soft provenance
            return {
                "pdf_found": True,
                "pdf_path": str(path),
                "error": str(exc),
                "pdf_page_offset": PDF_PAGE_OFFSET,
                "chapters": chapters,
            }
    return {
        "pdf_found": path is not None,
        "pdf_path": str(path) if path else None,
        "pdf_pages": page_count,
        "pdf_page_offset": PDF_PAGE_OFFSET,
        "note": "Copyrighted PDFs are gitignored; provenance uses local path only",
        "chapters": chapters,
    }


def enrich_concept_pages(concept_id: str, section_hint: str | None = None) -> dict[str, Any]:
    """Best-effort page hit search inside local PDF; soft-fails if unavailable."""
    from academy.knowledge_objects import knowledge_by_id

    ko = knowledge_by_id().get(concept_id)
    if not ko:
        raise KeyError(concept_id)
    base = {
        "concept_id": concept_id,
        "sources": [s.to_dict() for s in ko.sources],
        "section_hint": section_hint,
    }
    path = locate_pdf()
    if path is None:
        return {**base, "enriched": False, "reason": "pdf_not_found"}
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        needle = ko.concept.split()[0].lower()
        # Search near the primary chapter's estimated pdf page
        primary = ko.sources[0]
        start = max(0, (primary.pdf_page or 40) - 5)
        end = min(len(reader.pages), start + 40)
        hits = []
        for i in range(start, end):
            text = (reader.pages[i].extract_text() or "").lower()
            if needle in text:
                hits.append(i + 1)
            if len(hits) >= 5:
                break
        return {**base, "enriched": True, "pdf_path": str(path), "page_hits": hits}
    except Exception as exc:  # noqa: BLE001
        return {**base, "enriched": False, "reason": str(exc)}
