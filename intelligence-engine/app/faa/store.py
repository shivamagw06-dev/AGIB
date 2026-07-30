"""FAA immutable document version store — never overwrite."""

from __future__ import annotations

from typing import Any

from app.faa.models import DocumentVersion, utc_now


class FaaStore:
    def __init__(self) -> None:
        self.versions: dict[str, DocumentVersion] = {}  # document_id -> version record
        self.by_url: dict[str, list[str]] = {}  # url -> [document_ids] chronological

    def put_version(self, version: DocumentVersion) -> DocumentVersion:
        url = version.url
        prior_ids = self.by_url.get(url) or []
        if prior_ids:
            latest_id = prior_ids[-1]
            latest = self.versions.get(latest_id)
            if latest and latest.checksum == version.checksum and latest.status == "active":
                return latest
            if latest and latest.status == "active":
                latest.status = "superseded"
                latest.superseded_by = version.document_id
                version.version = int(latest.version) + 1
        self.versions[version.document_id] = version
        self.by_url.setdefault(url, []).append(version.document_id)
        return version

    def active_for_url(self, url: str) -> DocumentVersion | None:
        ids = self.by_url.get(url) or []
        for doc_id in reversed(ids):
            v = self.versions.get(doc_id)
            if v and v.status == "active":
                return v
        return None

    def snapshot(self) -> dict[str, Any]:
        active = sum(1 for v in self.versions.values() if v.status == "active")
        superseded = sum(1 for v in self.versions.values() if v.status == "superseded")
        return {
            "versions": len(self.versions),
            "active": active,
            "superseded": superseded,
            "urls": len(self.by_url),
            "latest": [
                self.versions[ids[-1]].to_dict()
                for ids in list(self.by_url.values())[-20:]
                if ids and ids[-1] in self.versions
            ],
        }

    def mark_fre_link(self, document_id: str, fre_document_id: str) -> None:
        v = self.versions.get(document_id)
        if v:
            v.fre_document_id = fre_document_id
            v.retrieved_at = v.retrieved_at or utc_now()
