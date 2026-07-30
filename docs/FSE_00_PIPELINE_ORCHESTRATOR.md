# FSE-00 — Pipeline Orchestrator (Phase 0)

## Architecture & Engineering Specification

### Version 1.0.0

| Field | Value |
| --- | --- |
| **Status** | Production — additive coordination layer |
| **Workstream** | FSE-00 / Phase 0 |
| **Package** | `intelligence-engine/financial_statements_engine/orchestrator/` |
| **Reuses** | FSE Event Bus (`collection/event_bus.py`) · FSE store · engine production façades |
| **Does not** | Parse · validate · warehouse · calculate · migrate HD · change collectors |

> **Intent:** Coordinate existing FSE engines as a deterministic workflow. Business logic stays inside each engine. The orchestrator only schedules, tracks state, retries, replays, and observes.

---

## Workflow

```text
RAW_EVIDENCE_STORED → PARSE → VALIDATE → WAREHOUSE_PUBLISH → DERIVED_METRICS
```

## Workflow identity

`company_id` + `period` + `filing_type` + `document_hash` → unique `workflow_id`  
Duplicates do not execute twice.

## State machine

`RECEIVED` · `QUEUED` · `RUNNING` · `COMPLETED` · `FAILED` · `RETRYING` · `CANCELLED`

## Surfaces

| Surface | Path |
| --- | --- |
| Health / Dashboard | `--orch-health` · `--orch-dashboard` · `GET …/orchestrator/health|dashboard` |
| Queue / History | `--orch-queue` · `--orch-history` · `GET …/orchestrator/workflows` |
| Retry / Replay | `--orch-retry ID` · `--orch-replay ID` · `POST …/orchestrator/retry|replay/{id}` |

## Foundation choice

Built **on top of** the existing FSE Event Bus + disk store (JSONL events, JSON workflow records). No second Celery/RQ scheduler introduced. CGL remains the gather loop; this orchestrator owns FSE stage sequencing only.
