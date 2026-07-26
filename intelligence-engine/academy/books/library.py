"""Personal library discovery — configured books directories only."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


BOOK_EXTS = {".pdf", ".epub", ".docx", ".md", ".markdown", ".txt"}
SHEET_EXTS = {".xlsx", ".xls", ".ods"}
SUPPORTED_EXTS = BOOK_EXTS | SHEET_EXTS


def candidate_roots() -> list[Path]:
    """Ordered search roots for the personal investment library."""
    roots: list[Path] = []
    env = os.environ.get("ACADEMY_BOOKS_DIR") or os.environ.get("AGI_ACADEMY_BOOKS_DIR")
    if env:
        roots.append(Path(env).expanduser())
    try:
        from app.core.config import get_settings

        s = get_settings()
        cfg = getattr(s, "academy_books_dir", "") or ""
        if cfg:
            roots.append(Path(cfg).expanduser())
    except Exception:
        pass
    roots.extend(
        [
            Path("/workspace/books"),
            Path.home() / "Downloads" / "AGIB" / "Books",
            Path.home() / "Downloads" / "AGIB" / "books",
            Path("/Users/shivamagarwal/Downloads/AGIB/Books"),
            Path("/Users/shivamagarwal/Downloads/AGIB/books"),
        ]
    )
    # de-dupe preserve order
    out: list[Path] = []
    seen: set[str] = set()
    for r in roots:
        key = str(r.resolve()) if r.exists() else str(r)
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def resolve_library_root() -> Path | None:
    for r in candidate_roots():
        if r.is_dir():
            return r
    return None


def scan_library(root: Path | None = None) -> dict[str, Any]:
    root = root or resolve_library_root()
    if root is None or not root.is_dir():
        return {
            "ok": False,
            "root": None,
            "candidates": [str(p) for p in candidate_roots()],
            "files": [],
            "books": [],
            "spreadsheets": [],
            "unsupported": [],
        }
    books: list[dict[str, Any]] = []
    sheets: list[dict[str, Any]] = []
    unsupported: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name.startswith("."):
            continue
        ext = path.suffix.lower()
        rel = str(path.relative_to(root))
        meta = {
            "path": str(path),
            "relative": rel,
            "filename": path.name,
            "ext": ext,
            "bytes": path.stat().st_size,
        }
        if ext in BOOK_EXTS:
            books.append(meta)
        elif ext in SHEET_EXTS:
            sheets.append(meta)
        elif ext in {".csv"}:
            # treat CSV as spreadsheet-like dataset
            sheets.append({**meta, "ext": ".csv", "as": "csv"})
        else:
            unsupported.append(meta)
    return {
        "ok": True,
        "root": str(root),
        "candidates": [str(p) for p in candidate_roots()],
        "files": books + sheets,
        "books": books,
        "spreadsheets": sheets,
        "unsupported": unsupported[:50],
        "counts": {
            "books": len(books),
            "spreadsheets": len(sheets),
            "unsupported": len(unsupported),
            "total_supported": len(books) + len(sheets),
        },
    }
