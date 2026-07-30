# AGI — Institutional Knowledge Operations Center (KOC-01)

## Mission

Admin-only control room for the Institutional Evidence Platform / Knowledge OS.

**Not a developer dashboard.** Operators monitor, validate, repair, and improve institutional knowledge.

## Access

| Rule | Behavior |
|------|----------|
| `isAdmin(user)` | Render **Knowledge Operations** in top nav (next to auth controls) and CMS sidebar |
| Non-admin signed-in | Menu item hidden; direct URL → **403 Forbidden** |
| Guest | Redirect to login |

Route: `/admin/knowledge-operations` (alias `/knowledge-operations`)

## Primary workflow — Missing Knowledge Inbox

> **Today's Highest-Impact Missing Knowledge**

Prioritized gaps (Critical → Low) with one-click **Upload** / **Repair**. Clears the job of searching for missing evidence.

## Page sections

1. Today's Knowledge Ingestion (timeline)
2. Daily Knowledge Summary
3. Institutional Coverage Table (search / view / refresh / upload)
4. Company Detail (green / yellow / red progress)
5. Manual Knowledge Upload (append-only pipeline)
6. Knowledge Queue
7. Collector Health
8. Evidence Explorer (via coverage + registry drill-down)
9. Knowledge Graph (rebuild action + IEP graph API)
10. Knowledge Versions
11. Coverage Heatmap (Top 20 / Nifty bands)
12. Operational Actions (CGL / KIL / ICF / repair / readiness)

## Upload pipeline

```text
Store document → checksum / hash → parse → extract → normalize
→ Evidence Objects → link company → Company Memory
→ Knowledge Graph → Research Readiness → Claim Safety
```

Evidence is **never overwritten**. Every action is audit-logged (who, when, hash, company, version, evidence IDs).

## Package

`intelligence-engine/knowledge_operations/`

| Module | Role |
|--------|------|
| `desk.py` | Control-room aggregate |
| `missing_inbox.py` | Prioritized gap inbox |
| `upload.py` | Manual upload + queue |
| `audit.py` | Immutable audit log |
| `actions.py` | Audited ops actions |
| `production.py` | API façades |

## APIs

| Method | Path |
|--------|------|
| GET | `/v1/koc/health` · `/koc/status` |
| GET | `/v1/koc/desk` |
| GET | `/v1/koc/missing-inbox` |
| GET | `/v1/koc/company/{ticker}` |
| POST | `/v1/koc/upload` |
| GET | `/v1/koc/queue` · `/koc/audit` |
| POST | `/v1/koc/action` |

BFF: `/api/intelligence/koc/*`

## UI

Light institutional surface — white background, IBM Plex, green/yellow/red status only. Bloomberg-terminal precision, not a colorful admin theme.
