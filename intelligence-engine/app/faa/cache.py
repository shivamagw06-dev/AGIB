"""Document cache — never download the same URL/content twice unless changed."""

from __future__ import annotations

from typing import Any

from app.faa.models import sha256_text, utc_now


class DocumentCache:
    """In-memory URL → checksum cache (PostgreSQL-ready shape)."""

    def __init__(self) -> None:
        self.by_url: dict[str, dict[str, Any]] = {}
        self.by_checksum: dict[str, str] = {}  # checksum → url

    def lookup(self, url: str) -> dict[str, Any] | None:
        return self.by_url.get((url or "").strip())

    def has_checksum(self, checksum: str) -> bool:
        return bool(checksum) and checksum in self.by_checksum

    def should_skip(self, url: str, *, content_checksum: str | None = None) -> tuple[bool, str | None]:
        row = self.lookup(url)
        if row and content_checksum and row.get("checksum") == content_checksum:
            return True, "unchanged_checksum"
        if row and content_checksum is None:
            # URL seen before — skip unless caller proves change
            return True, "url_cached"
        if content_checksum and self.has_checksum(content_checksum):
            return True, "checksum_exists"
        return False, None

    def put(
        self,
        *,
        url: str,
        checksum: str,
        title: str = "",
        document_type: str = "",
        connector_id: str = "",
        live_fetch: bool = False,
        fre_document_id: str | None = None,
    ) -> dict[str, Any]:
        row = {
            "url": url,
            "checksum": checksum,
            "title": title,
            "document_type": document_type,
            "connector_id": connector_id,
            "live_fetch": live_fetch,
            "fre_document_id": fre_document_id,
            "stored_at": utc_now().isoformat(),
            "content_fingerprint": sha256_text(f"{url}|{checksum}"),
        }
        prev = self.by_url.get(url)
        if prev and prev.get("checksum") != checksum:
            row["previous_checksum"] = prev.get("checksum")
            row["versioned"] = True
        self.by_url[url] = row
        if checksum:
            self.by_checksum[checksum] = url
        return row

    def snapshot(self) -> dict[str, Any]:
        return {"urls": len(self.by_url), "checksums": len(self.by_checksum)}
