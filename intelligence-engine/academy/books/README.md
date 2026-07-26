# AGI Academy Books V2 — Personal Library Knowledge Ingestion

**Architecture status:** v1.0.1 LOCKED  
**Role:** Extend Academy Books only — not an engine redesign.

## Mission

Convert every book / spreadsheet in the configured personal library into **structured institutional knowledge** (concepts, frameworks, formulas, graph). Never build a searchable PDF corpus. Never retain long verbatim copyrighted text.

## Library roots (first existing wins)

1. `ACADEMY_BOOKS_DIR` / settings `academy_books_dir`
2. `/Users/shivamagarwal/Downloads/AGIB/Books` (or `books/`)
3. `/Users/shivamagarwal/Downloads/AGIB` (if books sit directly in that folder)
4. `~/Downloads/AGIB/Books` → `~/Downloads/AGIB`
5. AGIB project root `Books/` / `books/`
6. `/workspace/books`

## Supported formats

- Books: PDF, EPUB, DOCX, Markdown
- Spreadsheets: XLSX, XLS, ODS, CSV → formulas, variables, templates, named ranges

## APIs

- `GET /v1/academy/books/library` — scan
- `POST /v1/academy/books/ingest-library` — batch structured ingest + report
- `GET /v1/academy/books/ingestion-report` — latest validation report
- Plus V1 health/dashboard/ingest/package/graph endpoints

## Flags

`ACADEMY`, `ACADEMY_BOOKS`, `ACADEMY_FRAMEWORKS`, `ACADEMY_FORMULAS`, `ACADEMY_GRAPH`, `ACADEMY_SPREADSHEETS`

## Admin

`/admin/academy` — Books V2 panel with ingest action, spreadsheet count, ingestion report table.
