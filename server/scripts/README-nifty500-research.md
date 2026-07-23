# Nifty 500 research worker

The research worker generates derived technical research for the current Nifty 500 constituent CSV and publishes a fully populated run to Supabase. It does not publish raw Groww market data, recommendations, targets, or order instructions.

## Required environment variables

```bash
GROWW_ACCESS_TOKEN=...
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=...
NIFTY500_CONSTITUENTS_PATH=/opt/render/project/src/Nifty500.csv
```

The service-role key is server-only. Never use it in a `VITE_` variable, browser code, or public client.

## Run once

```bash
cd server
pip install -r requirements.txt
python3 scripts/nifty500_research_engine.py --once
```

## Run as a Render background worker

Use this command for a worker service:

```bash
cd server && pip install -r requirements.txt && python3 scripts/nifty500_research_engine.py
```

The default schedule is `16:15` IST on weekdays. Configure optional runs with:

```bash
NIFTY500_SCHEDULE_TIMES_IST=08:30,12:30,16:15
```

Deploy the Supabase migration `supabase/migrations/20260723133739_nifty500_research.sql` before starting the worker. A run remains private until all stock records were written successfully; then it becomes the single public current run.
