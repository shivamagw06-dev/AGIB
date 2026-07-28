"""SQLite storage for KAIP Sprint 6.1 — append-only raw events + KO tables."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.contracts.models import (
    EntityRefs,
    KnowledgeObject,
    KnowledgeObjectType,
    LearningEvent,
    RawEvent,
    ValidationStatus,
)

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


class KaipStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        sql = SCHEMA_PATH.read_text(encoding="utf-8")
        self._conn.executescript(sql)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    # ----- raw events -----

    def insert_raw_event(self, event: RawEvent) -> None:
        now = _iso(datetime.now(timezone.utc))
        self._conn.execute(
            """
            INSERT INTO raw_events (
                event_id, source, collector_id, endpoint, company_symbol,
                payload_json, timestamp, checksum, validation_status,
                validation_errors_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.event_id,
                event.source.value,
                event.collector_id,
                event.endpoint,
                event.company_symbol,
                json.dumps(event.payload, default=str),
                _iso(event.timestamp),
                event.checksum,
                event.validation_status.value if event.validation_status else None,
                json.dumps(event.validation_errors),
                now,
            ),
        )
        self._conn.commit()

    def update_raw_validation(self, event: RawEvent) -> None:
        self._conn.execute(
            """
            UPDATE raw_events
            SET validation_status = ?, validation_errors_json = ?
            WHERE event_id = ?
            """,
            (
                event.validation_status.value if event.validation_status else None,
                json.dumps(event.validation_errors),
                event.event_id,
            ),
        )
        self._conn.commit()

    def find_duplicate(
        self,
        *,
        source: str,
        company_symbol: str | None,
        checksum: str,
        window_seconds: int,
        now: datetime | None = None,
    ) -> bool:
        now = now or datetime.now(timezone.utc)
        # Compare in Python for timezone-safe windowing
        rows = self._conn.execute(
            """
            SELECT timestamp FROM raw_events
            WHERE source = ? AND checksum = ?
              AND IFNULL(company_symbol, '') = IFNULL(?, '')
              AND validation_status IN ('accepted', 'duplicate')
            ORDER BY timestamp DESC
            LIMIT 20
            """,
            (source, checksum, company_symbol),
        ).fetchall()
        for row in rows:
            ts = _parse_dt(row["timestamp"])
            if ts is None:
                continue
            if abs((now - ts).total_seconds()) <= window_seconds:
                return True
        return False

    # ----- entity registry -----

    def upsert_entity(
        self,
        *,
        company_symbol: str,
        company_id: str,
        company_name: str,
        sector: str | None,
        industry: str | None,
        indexes: list[str],
        peers: list[str],
        aliases: list[str] | None = None,
    ) -> EntityRefs:
        now = _iso(datetime.now(timezone.utc))
        self._conn.execute(
            """
            INSERT INTO entity_registry (
                company_symbol, company_id, company_name, sector, industry,
                indexes_json, peers_json, aliases_json, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(company_symbol) DO UPDATE SET
                company_id = excluded.company_id,
                company_name = excluded.company_name,
                sector = excluded.sector,
                industry = excluded.industry,
                indexes_json = excluded.indexes_json,
                peers_json = excluded.peers_json,
                aliases_json = excluded.aliases_json,
                updated_at = excluded.updated_at
            """,
            (
                company_symbol.upper(),
                company_id,
                company_name,
                sector,
                industry,
                json.dumps(indexes),
                json.dumps(peers),
                json.dumps(aliases or []),
                now,
            ),
        )
        self._conn.commit()
        return EntityRefs(
            company_id=company_id,
            company_name=company_name,
            company_symbol=company_symbol.upper(),
            sector=sector,
            industry=industry,
            indexes=indexes,
            peers=peers,
        )

    def get_entity(self, company_symbol: str) -> EntityRefs | None:
        row = self._conn.execute(
            "SELECT * FROM entity_registry WHERE company_symbol = ?",
            (company_symbol.upper(),),
        ).fetchone()
        if not row:
            return None
        return EntityRefs(
            company_id=row["company_id"],
            company_name=row["company_name"],
            company_symbol=row["company_symbol"],
            sector=row["sector"],
            industry=row["industry"],
            indexes=json.loads(row["indexes_json"] or "[]"),
            peers=json.loads(row["peers_json"] or "[]"),
        )

    def update_entity_relationships(
        self,
        company_symbol: str,
        *,
        sector: str | None = None,
        industry: str | None = None,
        indexes: list[str] | None = None,
        peers: list[str] | None = None,
    ) -> EntityRefs | None:
        current = self.get_entity(company_symbol)
        if not current:
            return None
        return self.upsert_entity(
            company_symbol=current.company_symbol,
            company_id=current.company_id,
            company_name=current.company_name,
            sector=sector if sector is not None else current.sector,
            industry=industry if industry is not None else current.industry,
            indexes=indexes if indexes is not None else current.indexes,
            peers=peers if peers is not None else current.peers,
        )

    # ----- knowledge objects -----

    def latest_ko(self, object_type: KnowledgeObjectType, symbol: str) -> KnowledgeObject | None:
        row = self._conn.execute(
            """
            SELECT * FROM knowledge_objects
            WHERE object_type = ? AND company_symbol = ?
            ORDER BY version DESC
            LIMIT 1
            """,
            (object_type.value, symbol.upper()),
        ).fetchone()
        if not row:
            return None
        return self._row_to_ko(row)

    def insert_knowledge_object(self, ko: KnowledgeObject) -> None:
        self._conn.execute(
            """
            INSERT INTO knowledge_objects (
                object_id, object_type, company_symbol, version, payload_json,
                entity_refs_json, source_event_ids_json, published_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ko.object_id,
                ko.object_type.value,
                ko.company_symbol.upper(),
                ko.version,
                json.dumps(ko.payload, default=str),
                ko.entity_refs.model_dump_json(),
                json.dumps(ko.source_event_ids),
                _iso(ko.published_at),
                _iso(ko.created_at),
                _iso(ko.updated_at),
            ),
        )
        self._mirror_typed(ko)
        self._conn.commit()

    def mark_published(self, object_id: str, published_at: datetime) -> None:
        self._conn.execute(
            "UPDATE knowledge_objects SET published_at = ?, updated_at = ? WHERE object_id = ?",
            (_iso(published_at), _iso(published_at), object_id),
        )
        self._conn.commit()

    def _mirror_typed(self, ko: KnowledgeObject) -> None:
        payload = json.dumps(ko.payload, default=str)
        refs = ko.entity_refs.model_dump_json()
        now = _iso(ko.updated_at)
        symbol = ko.company_symbol.upper()
        if ko.object_type == KnowledgeObjectType.COMPANY_PROFILE:
            self._conn.execute(
                """
                INSERT INTO company_profiles (
                    company_symbol, object_id, payload_json, entity_refs_json, version, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(company_symbol) DO UPDATE SET
                    object_id = excluded.object_id,
                    payload_json = excluded.payload_json,
                    entity_refs_json = excluded.entity_refs_json,
                    version = excluded.version,
                    updated_at = excluded.updated_at
                """,
                (symbol, ko.object_id, payload, refs, ko.version, now),
            )
        elif ko.object_type == KnowledgeObjectType.MARKET_SNAPSHOT:
            self._conn.execute(
                """
                INSERT INTO market_snapshots (
                    snapshot_id, company_symbol, object_id, payload_json, as_of, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    ko.object_id,
                    symbol,
                    ko.object_id,
                    payload,
                    ko.payload.get("as_of") or now,
                    now,
                ),
            )
        elif ko.object_type == KnowledgeObjectType.CORPORATE_EVENT:
            self._conn.execute(
                """
                INSERT INTO corporate_events (
                    event_object_id, company_symbol, object_id, payload_json, event_date, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    ko.object_id,
                    symbol,
                    ko.object_id,
                    payload,
                    ko.payload.get("event_date"),
                    now,
                ),
            )
        elif ko.object_type == KnowledgeObjectType.CORPORATE_ACTION:
            self._conn.execute(
                """
                INSERT INTO corporate_actions (
                    action_object_id, company_symbol, object_id, payload_json, ex_date, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    ko.object_id,
                    symbol,
                    ko.object_id,
                    payload,
                    ko.payload.get("ex_date"),
                    now,
                ),
            )
        elif ko.object_type == KnowledgeObjectType.FINANCIAL_STATEMENT:
            self._conn.execute(
                """
                INSERT INTO financial_statements (
                    statement_id, company_symbol, object_id, statement_type,
                    period_end, payload_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ko.object_id,
                    symbol,
                    ko.object_id,
                    ko.payload.get("statement_type") or "unknown",
                    ko.payload.get("period_end"),
                    payload,
                    now,
                ),
            )

    def _row_to_ko(self, row: sqlite3.Row) -> KnowledgeObject:
        return KnowledgeObject(
            object_id=row["object_id"],
            object_type=KnowledgeObjectType(row["object_type"]),
            company_symbol=row["company_symbol"],
            version=row["version"],
            payload=json.loads(row["payload_json"]),
            entity_refs=EntityRefs.model_validate_json(row["entity_refs_json"]),
            source_event_ids=json.loads(row["source_event_ids_json"] or "[]"),
            published_at=_parse_dt(row["published_at"]),
            created_at=_parse_dt(row["created_at"]) or datetime.now(timezone.utc),
            updated_at=_parse_dt(row["updated_at"]) or datetime.now(timezone.utc),
        )

    def get_company_profile(self, symbol: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT * FROM company_profiles WHERE company_symbol = ?",
            (symbol.upper(),),
        ).fetchone()
        if not row:
            return None
        return {
            "object_id": row["object_id"],
            "company_symbol": row["company_symbol"],
            "version": row["version"],
            "payload": json.loads(row["payload_json"]),
            "entity_refs": json.loads(row["entity_refs_json"]),
            "updated_at": row["updated_at"],
        }

    def get_latest_market(self, symbol: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            """
            SELECT * FROM market_snapshots
            WHERE company_symbol = ?
            ORDER BY as_of DESC
            LIMIT 1
            """,
            (symbol.upper(),),
        ).fetchone()
        if not row:
            return None
        return {
            "object_id": row["object_id"],
            "company_symbol": row["company_symbol"],
            "payload": json.loads(row["payload_json"]),
            "as_of": row["as_of"],
            "updated_at": row["updated_at"],
        }

    def list_events(self, symbol: str, limit: int = 50) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            """
            SELECT * FROM corporate_events
            WHERE company_symbol = ?
            ORDER BY IFNULL(event_date, updated_at) DESC
            LIMIT ?
            """,
            (symbol.upper(), limit),
        ).fetchall()
        return [
            {
                "object_id": r["object_id"],
                "company_symbol": r["company_symbol"],
                "payload": json.loads(r["payload_json"]),
                "event_date": r["event_date"],
                "updated_at": r["updated_at"],
            }
            for r in rows
        ]

    def list_financials(self, symbol: str, limit: int = 50) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            """
            SELECT * FROM financial_statements
            WHERE company_symbol = ?
            ORDER BY IFNULL(period_end, updated_at) DESC
            LIMIT ?
            """,
            (symbol.upper(), limit),
        ).fetchall()
        return [
            {
                "object_id": r["object_id"],
                "company_symbol": r["company_symbol"],
                "statement_type": r["statement_type"],
                "period_end": r["period_end"],
                "payload": json.loads(r["payload_json"]),
                "updated_at": r["updated_at"],
            }
            for r in rows
        ]

    def insert_learning_event(self, event: LearningEvent) -> None:
        self._conn.execute(
            """
            INSERT INTO learning_events (
                learning_id, company_symbol, field_name, previous_value_json,
                new_value_json, delta_json, materiality, reason, object_type,
                object_id, source_event_ids_json, created_at, published_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.learning_id,
                event.company_symbol.upper(),
                event.field_name,
                json.dumps(event.previous_value, default=str),
                json.dumps(event.new_value, default=str),
                json.dumps(event.delta, default=str),
                event.materiality,
                event.reason,
                event.object_type.value if event.object_type else None,
                event.object_id,
                json.dumps(event.source_event_ids),
                _iso(event.created_at),
                _iso(event.published_at),
            ),
        )
        self._conn.commit()

    def mark_learning_published(self, learning_id: str, published_at: datetime) -> None:
        self._conn.execute(
            "UPDATE learning_events SET published_at = ? WHERE learning_id = ?",
            (_iso(published_at), learning_id),
        )
        self._conn.commit()

    def list_learning(self, symbol: str, limit: int = 50) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            """
            SELECT * FROM learning_events
            WHERE company_symbol = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (symbol.upper(), limit),
        ).fetchall()
        return [
            {
                "learning_id": r["learning_id"],
                "company_symbol": r["company_symbol"],
                "field_name": r["field_name"],
                "previous_value": json.loads(r["previous_value_json"]) if r["previous_value_json"] else None,
                "new_value": json.loads(r["new_value_json"]) if r["new_value_json"] else None,
                "delta": json.loads(r["delta_json"]) if r["delta_json"] else None,
                "materiality": r["materiality"],
                "reason": r["reason"],
                "object_type": r["object_type"],
                "object_id": r["object_id"],
                "created_at": r["created_at"],
                "published_at": r["published_at"],
            }
            for r in rows
        ]

    def count_raw_events(self) -> int:
        return int(self._conn.execute("SELECT COUNT(*) AS c FROM raw_events").fetchone()["c"])

    def count_published_kos(self) -> int:
        return int(
            self._conn.execute(
                "SELECT COUNT(*) AS c FROM knowledge_objects WHERE published_at IS NOT NULL"
            ).fetchone()["c"]
        )
