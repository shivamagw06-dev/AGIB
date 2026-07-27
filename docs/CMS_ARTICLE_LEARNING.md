# CMS article learning (daily knowledge updates)

Soft-wire path so AGI **reads uploaded CMS articles** into KIP → KF/KC and **remembers learning dates** (Asia/Kolkata) for everyday knowledge updates.

Architecture **v1.0.1 LOCKED** — additive only.

## 1. Run the Supabase migrations

Open the project SQL editor and run:

1. `supabase/migrations/20260726120000_cms_article_learning_dates.sql`
2. `supabase/migrations/20260727180000_cms_intelligence_ingest_jobs.sql` (async Send-to-Intelligence job queue)

Learning migration adds on `articles`:

- `last_learned_at`
- `learn_status`
- `last_learn_error`
- `learn_count`

And creates `cms_article_learn_events` with `learning_date` for the daily calendar.

The ingest-jobs migration creates `cms_intelligence_ingest_jobs` so CMS never waits on Render wake inside the browser request.

Also run the harden + pipeline foundation migrations:

- `supabase/migrations/20260727190000_cms_ingest_jobs_harden.sql`
- `supabase/migrations/20260727200000_cms_ingest_pipeline_foundation.sql`

(adds `failed_permanent`, metrics, priority, stage_trace, leases, confidence/cost, approval, replay).

## 1b. Send to Intelligence (async job queue)

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/intelligence/kip/ingest/agi` | **Enqueue only** → always `202` + `job_id` |
| `GET` | `/api/intelligence/cms/ingest-jobs/:jobId` | Poll status + `pipeline_stage` / `stage_trace` / confidence / cost |
| `GET` | `/api/intelligence/cms/ingest-jobs-stuck` | Ops alert: stalled processing (>15m) or queued (>30m) |
| `POST` | `/api/intelligence/cms/ingest-jobs/tick` | Manual reclaim + process tick (post-deploy rescue) |
| `GET` | `/api/intelligence/cms/ingest-pipeline` | Soft stage blueprint (maps to existing KIP/KC — no new engines) |
| `POST` | `/api/intelligence/cms/ingest-jobs/:jobId/replay` | Replay terminal job payload (optional new `embedding_version`) |
| `POST` | `/api/intelligence/cms/ingest-jobs/:jobId/approve` | Release `require_approval` jobs to the worker |

Flow: CMS saves article → POST enqueue (idempotent on `article_id` + content hash) → Node worker wakes engine + retries with exponential backoff → browser polls short GETs until a **terminal** state (then stops). Duplicate clicks return the same active job. **Content change** (new hash) creates a **new version** job.

### Pipeline foundation (soft-wire)

Stages over **existing** AGIB layers only:

`queued → wake_engine → kip_ingest → knowledge_compound → [awaiting_approval] → completed`

- **Priority:** 1 market alert → 2 research → 3 default → 4 archive  
- **Exactly-once stages:** `stage_keys` skip already-completed stages on retry  
- **Lease tokens:** claim ownership + heartbeat while processing  
- **Backpressure:** 429 slows the worker (`backpressure_until`, adaptive concurrency)  
- **Replay:** re-run stored payload with a new embedding version without CMS re-upload  
- **Human approval:** `require_approval: true` holds the job until `/approve`

Longer-term graph/teach/forecast work stays inside existing soft layers (KIP/KC/FRE/IIE/FLE) — this queue is the entry gate, not a new engine.

### Worker modes

- `CMS_INGEST_WORKER_MODE=embedded` (default): API process runs the worker + startup reclaim + stall watchdog.
- `CMS_INGEST_WORKER_MODE=external` + Render worker `agib-cms-ingest-worker`: API enqueue-only; dedicated process owns processing (`node server/workers/cmsIngestWorker.js`).

### Failure policy

- Retry (transient): 502/503/timeouts/connection errors — up to `max_attempts` (default 6), then **dead-letter** `failed_permanent`.
- Do not retry (permanent): 400/401/403/404/422, validation, malformed payload → immediate `failed_permanent`.
- Stall reclaim: jobs in `waking`/`processing` older than 15 minutes return to `pending`.

## 2. API (Render Node)

Requires `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` on the API.

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/intelligence/cms/learn-articles` | Read CMS articles into KIP; stamp dates; optional KC populate |
| `GET` | `/api/intelligence/cms/learning-status` | Pending articles + learning calendar |
| `GET` | `/api/intelligence/cms/learning-summary?days=5` | Founder digest of what intelligence learned |
| Mission Control | `/api/intelligence/mission-control/dashboard` | Soft-enriched with `learning_last_5_days` |

Body options for learn:

```json
{
  "only_unlearned": true,
  "mode": "daily",
  "limit": 100,
  "compound": true
}
```

- `only_unlearned` — catch-up for articles never learned  
- `mode: "daily"` — skip articles already learned on today’s IST date  
- `compound` — after successful ingests, call `/v1/kc/populate`

## 3. Daily scheduler

Node starts a soft scheduler (`CMS_ARTICLE_LEARN_DAILY`, default `true`) that runs about hourly and executes **one daily learn per IST calendar day**.

Disable: `CMS_ARTICLE_LEARN_DAILY=false`

## 4. Admin UI

- **CMS Dashboard** → “Ask intelligence to learn articles”
- **Knowledge Foundation** → “Learn unlearned articles” / “Daily CMS learn” + calendar

## 5. Manual catch-up (after migration)

```bash
curl -X POST https://finance-news-backend-19i5.onrender.com/api/intelligence/cms/learn-articles \
  -H 'Content-Type: application/json' \
  -d '{"only_unlearned":true,"limit":200,"compound":true}'
```
