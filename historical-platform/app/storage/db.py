"""Append-only Historical Knowledge Store — never overwrites history."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.contracts.models import (
    HistoricalKnowledgeObject,
    HistoricalObjectType,
    IngestionRun,
    RawHistoricalEvent,
    ValidationStatus,
)
from app.coverage.policy import COVERAGE_TARGETS, expected_for, score_completeness

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


class HipStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    # ----- raw archive -----

    def insert_raw(self, event: RawHistoricalEvent) -> bool:
        """Insert raw event. Returns False if checksum already archived (idempotent)."""
        try:
            self._conn.execute(
                """
                INSERT INTO historical_raw_archive (
                    event_id, source, collector_id, endpoint, company_symbol, category,
                    payload_json, retrieved_at, effective_start, effective_end, checksum,
                    validation_status, validation_errors_json, ingestion_run_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.source.value,
                    event.collector_id,
                    event.endpoint,
                    event.company_symbol.upper() if event.company_symbol else None,
                    event.category,
                    json.dumps(event.payload, default=str),
                    _iso(event.retrieved_at),
                    event.effective_start,
                    event.effective_end,
                    event.checksum,
                    event.validation_status.value if event.validation_status else None,
                    json.dumps(event.validation_errors),
                    event.ingestion_run_id,
                    _iso(event.created_at),
                ),
            )
            self._conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def update_raw_validation(self, event: RawHistoricalEvent) -> None:
        self._conn.execute(
            """
            UPDATE historical_raw_archive
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

    def checksum_exists(self, checksum: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM historical_raw_archive WHERE checksum = ?",
            (checksum,),
        ).fetchone()
        return row is not None

    def count_raw(self) -> int:
        return int(self._conn.execute("SELECT COUNT(*) AS c FROM historical_raw_archive").fetchone()["c"])

    # ----- ingestion runs -----

    def start_run(self, run: IngestionRun) -> None:
        self._conn.execute(
            """
            INSERT INTO historical_ingestion_runs (
                run_id, mode, collector_id, symbols_json, categories_json,
                started_at, ended_at, status, raw_accepted, raw_rejected,
                objects_written, detail_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run.run_id,
                run.mode,
                run.collector_id,
                json.dumps(run.symbols),
                json.dumps(run.categories),
                _iso(run.started_at),
                _iso(run.ended_at),
                run.status,
                run.raw_accepted,
                run.raw_rejected,
                run.objects_written,
                json.dumps(run.detail, default=str),
            ),
        )
        self._conn.commit()

    def finish_run(self, run: IngestionRun) -> None:
        self._conn.execute(
            """
            UPDATE historical_ingestion_runs
            SET ended_at = ?, status = ?, raw_accepted = ?, raw_rejected = ?,
                objects_written = ?, detail_json = ?
            WHERE run_id = ?
            """,
            (
                _iso(run.ended_at),
                run.status,
                run.raw_accepted,
                run.raw_rejected,
                run.objects_written,
                json.dumps(run.detail, default=str),
                run.run_id,
            ),
        )
        self._conn.commit()

    def list_runs(self, limit: int = 50) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT * FROM historical_ingestion_runs ORDER BY started_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["symbols"] = json.loads(d.pop("symbols_json") or "[]")
            d["categories"] = json.loads(d.pop("categories_json") or "[]")
            d["detail"] = json.loads(d.pop("detail_json") or "{}")
            out.append(d)
        return out

    # ----- entities -----

    def upsert_entity(
        self,
        *,
        company_symbol: str,
        company_name: str | None = None,
        sector: str | None = None,
        sector_key: str | None = None,
        industry: str | None = None,
        index_membership: list[str] | None = None,
    ) -> None:
        symbol = company_symbol.upper()
        self._conn.execute(
            """
            INSERT INTO historical_entities (
                company_symbol, company_name, sector, sector_key, industry,
                index_membership_json, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(company_symbol) DO UPDATE SET
                company_name = COALESCE(excluded.company_name, historical_entities.company_name),
                sector = COALESCE(excluded.sector, historical_entities.sector),
                sector_key = COALESCE(excluded.sector_key, historical_entities.sector_key),
                industry = COALESCE(excluded.industry, historical_entities.industry),
                index_membership_json = excluded.index_membership_json,
                updated_at = excluded.updated_at
            """,
            (
                symbol,
                company_name,
                sector,
                sector_key,
                industry,
                json.dumps(index_membership or []),
                _iso(datetime.now(timezone.utc)),
            ),
        )
        self._conn.commit()

    def get_entity(self, symbol: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT * FROM historical_entities WHERE company_symbol = ?",
            (symbol.upper(),),
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["index_membership"] = json.loads(d.pop("index_membership_json") or "[]")
        return d

    # ----- knowledge objects -----

    def latest_version(
        self, object_type: HistoricalObjectType, subject_key: str, effective_date: str
    ) -> int:
        row = self._conn.execute(
            """
            SELECT MAX(version) AS v FROM historical_knowledge_objects
            WHERE object_type = ? AND subject_key = ? AND effective_date = ?
            """,
            (object_type.value, subject_key, effective_date),
        ).fetchone()
        return int(row["v"] or 0)

    def insert_historical_object(self, ko: HistoricalKnowledgeObject) -> None:
        self._conn.execute(
            """
            INSERT INTO historical_knowledge_objects (
                object_id, object_type, subject_key, company_symbol, effective_date,
                period_kind, version, previous_object_id, knowledge_json,
                entity_refs_json, provenance_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ko.object_id,
                ko.object_type.value,
                ko.subject_key,
                ko.company_symbol.upper() if ko.company_symbol else None,
                ko.effective_date,
                ko.period_kind.value,
                ko.version,
                ko.previous_object_id,
                json.dumps(ko.knowledge, default=str),
                json.dumps(ko.entity_refs.model_dump(mode="json"), default=str),
                json.dumps(ko.provenance.model_dump(mode="json"), default=str),
                _iso(ko.created_at),
            ),
        )
        self._mirror(ko)
        self._conn.commit()

    def _mirror(self, ko: HistoricalKnowledgeObject) -> None:
        prov = json.dumps(ko.provenance.model_dump(mode="json"), default=str)
        knowledge = json.dumps(ko.knowledge, default=str)
        created = _iso(ko.created_at)
        symbol = ko.company_symbol.upper() if ko.company_symbol else ""
        if ko.object_type == HistoricalObjectType.PRICE_HISTORY:
            self._conn.execute(
                """
                INSERT INTO historical_prices (
                    object_id, company_symbol, effective_date, period_kind, version,
                    open, high, low, close, volume, knowledge_json, provenance_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ko.object_id,
                    symbol,
                    ko.effective_date,
                    ko.period_kind.value,
                    ko.version,
                    ko.knowledge.get("open"),
                    ko.knowledge.get("high"),
                    ko.knowledge.get("low"),
                    ko.knowledge.get("close"),
                    ko.knowledge.get("volume"),
                    knowledge,
                    prov,
                    created,
                ),
            )
        elif ko.object_type == HistoricalObjectType.FINANCIAL_STATEMENT:
            self._conn.execute(
                """
                INSERT INTO historical_financials (
                    object_id, company_symbol, effective_date, period_kind, statement_type,
                    version, revenue, net_income, knowledge_json, provenance_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ko.object_id,
                    symbol,
                    ko.effective_date,
                    ko.period_kind.value,
                    ko.knowledge.get("statement_type") or "income",
                    ko.version,
                    ko.knowledge.get("revenue"),
                    ko.knowledge.get("net_income"),
                    knowledge,
                    prov,
                    created,
                ),
            )
        elif ko.object_type == HistoricalObjectType.BALANCE_SHEET:
            self._conn.execute(
                """
                INSERT INTO historical_balance_sheets (
                    object_id, company_symbol, effective_date, period_kind, version,
                    knowledge_json, provenance_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (ko.object_id, symbol, ko.effective_date, ko.period_kind.value, ko.version, knowledge, prov, created),
            )
        elif ko.object_type == HistoricalObjectType.CASH_FLOW:
            self._conn.execute(
                """
                INSERT INTO historical_cashflows (
                    object_id, company_symbol, effective_date, period_kind, version,
                    knowledge_json, provenance_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (ko.object_id, symbol, ko.effective_date, ko.period_kind.value, ko.version, knowledge, prov, created),
            )
        elif ko.object_type == HistoricalObjectType.DIVIDEND_HISTORY:
            self._conn.execute(
                """
                INSERT INTO historical_dividends (
                    object_id, company_symbol, effective_date, version, amount,
                    knowledge_json, provenance_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ko.object_id,
                    symbol,
                    ko.effective_date,
                    ko.version,
                    ko.knowledge.get("amount"),
                    knowledge,
                    prov,
                    created,
                ),
            )
        elif ko.object_type == HistoricalObjectType.CORPORATE_ACTION:
            self._conn.execute(
                """
                INSERT INTO historical_actions (
                    object_id, company_symbol, effective_date, action_type, version,
                    knowledge_json, provenance_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ko.object_id,
                    symbol,
                    ko.effective_date,
                    ko.knowledge.get("action_type") or "unknown",
                    ko.version,
                    knowledge,
                    prov,
                    created,
                ),
            )
        elif ko.object_type == HistoricalObjectType.CORPORATE_EVENT:
            self._conn.execute(
                """
                INSERT INTO historical_events (
                    object_id, company_symbol, effective_date, event_type, version,
                    knowledge_json, provenance_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ko.object_id,
                    symbol,
                    ko.effective_date,
                    ko.knowledge.get("event_type") or "announcement",
                    ko.version,
                    knowledge,
                    prov,
                    created,
                ),
            )
            if ko.knowledge.get("report_type"):
                self._conn.execute(
                    """
                    INSERT INTO historical_reports (
                        object_id, company_symbol, effective_date, report_type, version, title,
                        knowledge_json, provenance_json, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        ko.object_id,
                        symbol,
                        ko.effective_date,
                        ko.knowledge.get("report_type"),
                        ko.version,
                        ko.knowledge.get("title"),
                        knowledge,
                        prov,
                        created,
                    ),
                )
        elif ko.object_type == HistoricalObjectType.COMPANY_PROFILE:
            self._conn.execute(
                """
                INSERT INTO historical_company_profiles (
                    object_id, company_symbol, effective_date, version,
                    knowledge_json, entity_refs_json, provenance_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ko.object_id,
                    symbol,
                    ko.effective_date,
                    ko.version,
                    knowledge,
                    json.dumps(ko.entity_refs.model_dump(mode="json"), default=str),
                    prov,
                    created,
                ),
            )
        elif ko.object_type == HistoricalObjectType.NEWS_EVENT:
            self._conn.execute(
                """
                INSERT INTO historical_news (
                    object_id, company_symbol, effective_date, version, title,
                    knowledge_json, provenance_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ko.object_id,
                    symbol,
                    ko.effective_date,
                    ko.version,
                    ko.knowledge.get("title"),
                    knowledge,
                    prov,
                    created,
                ),
            )
        elif ko.knowledge.get("report_type"):
            self._conn.execute(
                """
                INSERT INTO historical_reports (
                    object_id, company_symbol, effective_date, report_type, version, title,
                    knowledge_json, provenance_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ko.object_id,
                    symbol,
                    ko.effective_date,
                    ko.knowledge.get("report_type"),
                    ko.version,
                    ko.knowledge.get("title"),
                    knowledge,
                    prov,
                    created,
                ),
            )

    # ----- retrieval (no external calls) -----

    def list_prices(
        self, symbol: str, *, period_kind: str = "daily", limit: int = 5000
    ) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            """
            SELECT * FROM historical_prices
            WHERE company_symbol = ? AND period_kind = ?
            ORDER BY effective_date ASC, version DESC
            LIMIT ?
            """,
            (symbol.upper(), period_kind, limit),
        ).fetchall()
        return [self._row_knowledge(r) for r in rows]

    def list_financials(
        self, symbol: str, *, period_kind: str | None = None, limit: int = 200
    ) -> list[dict[str, Any]]:
        if period_kind:
            rows = self._conn.execute(
                """
                SELECT * FROM historical_financials
                WHERE company_symbol = ? AND period_kind = ?
                ORDER BY effective_date ASC, version DESC
                LIMIT ?
                """,
                (symbol.upper(), period_kind, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """
                SELECT * FROM historical_financials
                WHERE company_symbol = ?
                ORDER BY effective_date ASC, version DESC
                LIMIT ?
                """,
                (symbol.upper(), limit),
            ).fetchall()
        return [self._row_knowledge(r) for r in rows]

    def list_events(self, symbol: str, limit: int = 200) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            """
            SELECT * FROM historical_events
            WHERE company_symbol = ?
            ORDER BY effective_date DESC, version DESC
            LIMIT ?
            """,
            (symbol.upper(), limit),
        ).fetchall()
        return [self._row_knowledge(r) for r in rows]

    def list_actions(self, symbol: str, limit: int = 200) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            """
            SELECT * FROM historical_actions
            WHERE company_symbol = ?
            ORDER BY effective_date DESC, version DESC
            LIMIT ?
            """,
            (symbol.upper(), limit),
        ).fetchall()
        return [self._row_knowledge(r) for r in rows]

    def list_dividends(self, symbol: str, limit: int = 200) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            """
            SELECT * FROM historical_dividends
            WHERE company_symbol = ?
            ORDER BY effective_date ASC, version DESC
            LIMIT ?
            """,
            (symbol.upper(), limit),
        ).fetchall()
        return [self._row_knowledge(r) for r in rows]

    def list_reports(self, symbol: str, limit: int = 100) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            """
            SELECT * FROM historical_reports
            WHERE company_symbol = ?
            ORDER BY effective_date DESC, version DESC
            LIMIT ?
            """,
            (symbol.upper(), limit),
        ).fetchall()
        return [self._row_knowledge(r) for r in rows]

    def list_profiles(self, symbol: str, limit: int = 50) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            """
            SELECT * FROM historical_company_profiles
            WHERE company_symbol = ?
            ORDER BY effective_date DESC, version DESC
            LIMIT ?
            """,
            (symbol.upper(), limit),
        ).fetchall()
        return [self._row_knowledge(r) for r in rows]

    def list_news(self, symbol: str, limit: int = 100) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            """
            SELECT * FROM historical_news
            WHERE company_symbol = ?
            ORDER BY effective_date DESC, version DESC
            LIMIT ?
            """,
            (symbol.upper(), limit),
        ).fetchall()
        return [self._row_knowledge(r) for r in rows]

    def revenue_series(self, symbol: str, *, from_period: str, to_period: str) -> list[dict[str, Any]]:
        """FY/period revenue series for IE — store only, no external providers."""
        rows = self.list_financials(symbol, limit=500)
        out = []
        seen: set[str] = set()
        for row in rows:
            period = row.get("effective_date") or ""
            if period < from_period or period > to_period:
                continue
            if period in seen:
                continue
            seen.add(period)
            out.append(
                {
                    "period": period,
                    "period_kind": row.get("period_kind"),
                    "revenue": row.get("revenue") or (row.get("knowledge") or {}).get("revenue"),
                    "net_income": row.get("net_income") or (row.get("knowledge") or {}).get("net_income"),
                    "pe": (row.get("knowledge") or {}).get("pe"),
                    "valuation": (row.get("knowledge") or {}).get("valuation"),
                    "version": row.get("version"),
                    "provenance": row.get("provenance"),
                }
            )
        return out

    def coverage_report(self, symbol: str, settings: Any | None = None) -> dict[str, Any]:
        symbol = symbol.upper()
        counts = {
            "daily_ohlcv": self._count("historical_prices", symbol, "period_kind = 'daily'"),
            "quarterly_financials": self._count(
                "historical_financials", symbol, "period_kind = 'quarterly'"
            ),
            "annual_financials": self._count(
                "historical_financials", symbol, "period_kind = 'annual'"
            ),
            "balance_sheets": self._count("historical_balance_sheets", symbol),
            "cash_flows": self._count("historical_cashflows", symbol),
            "dividends": self._count("historical_dividends", symbol),
            "corporate_actions": self._count("historical_actions", symbol),
            "corporate_events": self._count("historical_events", symbol),
            "company_ir_reports": self._count("historical_reports", symbol),
            "company_profile_history": self._count("historical_company_profiles", symbol),
            "news_metadata": self._count("historical_news", symbol),
        }
        categories = {}
        for t in COVERAGE_TARGETS:
            categories[t.category] = {
                "description": t.description,
                **score_completeness(counts.get(t.category, 0), expected_for(t.category, settings)),
            }
        return {"company_symbol": symbol, "categories": categories, "counts": counts}

    def _count(self, table: str, symbol: str, extra: str | None = None) -> int:
        where = "company_symbol = ?"
        if extra:
            where += f" AND {extra}"
        # distinct effective dates for completeness
        sql = f"SELECT COUNT(DISTINCT effective_date) AS c FROM {table} WHERE {where}"
        return int(self._conn.execute(sql, (symbol.upper(),)).fetchone()["c"])

    def count_objects(self) -> int:
        return int(
            self._conn.execute("SELECT COUNT(*) AS c FROM historical_knowledge_objects").fetchone()["c"]
        )

    @staticmethod
    def _row_knowledge(row: sqlite3.Row) -> dict[str, Any]:
        d = dict(row)
        if "knowledge_json" in d:
            d["knowledge"] = json.loads(d.pop("knowledge_json") or "{}")
        if "provenance_json" in d:
            d["provenance"] = json.loads(d.pop("provenance_json") or "{}")
        if "entity_refs_json" in d:
            d["entity_refs"] = json.loads(d.pop("entity_refs_json") or "{}")
        return d
