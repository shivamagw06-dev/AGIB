# AGI Academy Books V1

**Architecture status:** v1.0.1 LOCKED  
**Role:** Permanent institutional learning layer — not an engine, not an LLM, not a recommender.

## Mission

Extend Academy so AGI learns from curated investment books, textbooks, accounting references, valuation guides, economics books and industry handbooks — as **structured knowledge objects**, never as searchable PDFs or copyrighted verbatim text.

## Pipeline

Books → text extract (transient) → chapter/section detection → concept / framework / formula extraction → knowledge objects → Academy → Knowledge Foundation → CID → IRP → Ask AGI / Research Writer

## Flags

| Flag | Purpose |
|------|---------|
| `ACADEMY` | Master Academy enable |
| `ACADEMY_BOOKS` | Book ingestion + structured learning |
| `ACADEMY_FRAMEWORKS` | Framework objects |
| `ACADEMY_FORMULAS` | Formula objects |
| `ACADEMY_GRAPH` | Knowledge graph edges |

## Copyright policy

- Never store long verbatim passages
- Never build a searchable PDF index
- Store definitions / summaries / formulas / frameworks in AGI's own institutional language
- Keep source book id + chapter attribution + extraction confidence

## Soft wiring

- **Catalog / FAPI** — book concepts participate in finance reasoning packages
- **CID** — Nestlé-class dossiers gain sector/valuation/accounting learning blocks
- **KF** — academy themes soft-attached
- **Ask AGI** — via FAPI package + answer hints (no book quotes)
- **Research Writer** — frameworks/terminology/logic hints only

## Admin

`/admin/academy` — Books panel (counts, gates, flags, linked companies, most-used concepts)
