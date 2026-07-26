# CMS article learning (daily knowledge updates)

Soft-wire path so AGI **reads uploaded CMS articles** into KIP → KF/KC and **remembers learning dates** (Asia/Kolkata) for everyday knowledge updates.

Architecture **v1.0.1 LOCKED** — additive only.

## 1. Run the Supabase migration

Open the project SQL editor and run:

`supabase/migrations/20260726120000_cms_article_learning_dates.sql`

This adds on `articles`:

- `last_learned_at`
- `learn_status`
- `last_learn_error`
- `learn_count`

And creates `cms_article_learn_events` with `learning_date` for the daily calendar.

## 2. API (Render Node)

Requires `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` on the API.

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/intelligence/cms/learn-articles` | Read CMS articles into KIP; stamp dates; optional KC populate |
| `GET` | `/api/intelligence/cms/learning-status` | Pending articles + learning calendar |

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
