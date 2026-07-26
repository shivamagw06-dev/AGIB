"""Book ingestion pipeline: extract → chapters → concepts/frameworks/formulas → graph."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from academy.books.chapters import detect_hierarchy, hierarchy_stats
from academy.books.extract import extract_from_text
from academy.books.graph import rebuild_graph
from academy.books.schema import BOOKS_VERSION, BookMeta
from academy.books.seed import (
    all_seed_concepts,
    seed_books,
    seed_chapters,
    seed_formulas,
    seed_frameworks,
)
from academy.books.store import BooksStore, get_books_store
from academy.books.text_extract import extract_text


def ensure_seeded(store: BooksStore | None = None) -> dict[str, Any]:
    store = store or get_books_store()
    if store.books:
        return {"seeded": False, **store.snapshot()}
    for b in seed_books():
        store.upsert_book(b)
    for ch in seed_chapters():
        store.upsert_chapter(ch)
    for c in all_seed_concepts():
        store.upsert_concept(c)
    for f in seed_formulas():
        store.upsert_formula(f)
    for fw in seed_frameworks():
        store.upsert_framework(fw)
    rebuild_graph(store)
    return {"seeded": True, **store.snapshot()}


def ingest_book(
    *,
    title: str,
    authors: list[str] | None = None,
    content: str = "",
    content_bytes: bytes | None = None,
    filename: str = "",
    subject: str | None = None,
    difficulty: str = "intermediate",
    publication_year: int | None = None,
    publisher: str | None = None,
    edition: str | None = None,
    language: str = "en",
    store: BooksStore | None = None,
) -> dict[str, Any]:
    """
    Ingest one book into structured knowledge.
    Raw text is transient — only short AGI-owned objects are stored.
    """
    store = store or get_books_store()
    ensure_seeded(store)

    extracted = extract_text(filename=filename, content=content, content_bytes=content_bytes)
    text = extracted.get("text") or content or ""
    if not text.strip():
        return {"ok": False, "reason": "no_text", "needs_ocr": bool(extracted.get("needs_ocr"))}

    book_id = _book_id(title, filename)
    meta = BookMeta(
        book_id=book_id,
        title=title or book_id,
        authors=list(authors or []),
        edition=edition,
        publisher=publisher,
        publication_year=publication_year,
        language=language,
        subject=subject,
        topics=_guess_topics(text),
        difficulty=difficulty,
        source_format=str(extracted.get("format") or "text"),
        academies=[],
    )
    store.upsert_book(meta)

    chapters = detect_hierarchy(book_id, text)
    for ch in chapters:
        store.upsert_chapter(ch)

    academies: set[str] = set()
    concept_n = formula_n = framework_n = 0

    # Extract per chapter using chapter summary + local window from headings
    for ch in chapters:
        # Use summary as AGI-owned working text; if empty, skip heavy extract
        working = ch.summary or ""
        # Lightly include nearby heading title for keyword hits
        working = f"{ch.title}. {working}"
        pack = extract_from_text(book_id=book_id, text=working, chapter_title=ch.title)
        for c in pack["concepts"]:
            store.upsert_concept(c)
            academies.add(c.academy)
            concept_n += 1
        for f in pack["formulas"]:
            store.upsert_formula(f)
            academies.add(f.academy)
            formula_n += 1
        for fw in pack["frameworks"]:
            store.upsert_framework(fw)
            academies.add(fw.academy)
            framework_n += 1

    # Whole-book pass for named formulas/frameworks (titles only + short slices)
    head = text[:6000]
    pack = extract_from_text(book_id=book_id, text=head, chapter_title="front_matter")
    for f in pack["formulas"]:
        store.upsert_formula(f)
        academies.add(f.academy)
        formula_n += 1
    for fw in pack["frameworks"]:
        store.upsert_framework(fw)
        academies.add(fw.academy)
        framework_n += 1

    meta.academies = sorted(academies)
    meta.topics = list(dict.fromkeys(meta.topics + list(academies)))[:16]
    store.upsert_book(meta)
    rebuild_graph(store)

    return {
        "ok": True,
        "book_id": book_id,
        "version": meta.version,
        "format": extracted.get("format"),
        "pages_approx": extracted.get("pages_approx"),
        "hierarchy": hierarchy_stats(chapters),
        "extracted": {
            "concepts": concept_n,
            "formulas": formula_n,
            "frameworks": framework_n,
        },
        "academies": meta.academies,
        "books_version": BOOKS_VERSION,
        # Prove we do not return raw book text
        "raw_text_retained": False,
    }


def _book_id(title: str, filename: str) -> str:
    base = title or (Path(filename).stem.replace("_", " ") if filename else "") or "book"
    slug = re.sub(r"[^a-z0-9]+", "_", base.lower()).strip("_")[:48]
    return f"book_{slug}" if not slug.startswith("book_") else slug


def _guess_topics(text: str) -> list[str]:
    keys = [
        "valuation", "dcf", "accounting", "wacc", "roic", "moat", "portfolio",
        "macro", "banking", "fmcg", "behavioural", "risk",
    ]
    blob = (text or "").lower()
    return [k for k in keys if k in blob][:10]


def ingest_markdown_fixture(title: str, markdown: str, **kwargs: Any) -> dict[str, Any]:
    """Test helper — ingest short AGI-authored markdown (not copyrighted books)."""
    return ingest_book(title=title, content=markdown, filename=f"{title}.md", **kwargs)
