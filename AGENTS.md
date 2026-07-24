# AGENTS.md

## Cursor Cloud specific instructions

This repo is a monorepo for **AGI / Agarwal Global Investments**, an Indian equity-research & market-intelligence platform. It has three services plus a Supabase backend. The startup update script already installs all dependencies (root npm, `server` npm via `npm ci`, and the `intelligence-engine` Python venv).

### Services and how to run them

| Service | Path | Dev command | Port | Notes |
|---|---|---|---|---|
| Frontend (React + Vite) | repo root | `npm run dev` | 3000 | Public site + admin CMS. Vite proxies `/api` → `http://localhost:3001`. |
| Node API gateway (`agib-api`) | `server/` | `npm run dev` | **3001** | Express proxy/cache for market data + `/api/intelligence/*`. See `server/package.json`. |
| Intelligence Engine (FastAPI) | `intelligence-engine/` | `intelligence-engine/.venv/bin/uvicorn app.main:app --port 8100 --reload` | 8100 | **Optional.** See `intelligence-engine/README.md`. |

### Non-obvious caveats

- **Node gateway must run on `PORT=3001`.** `server/index.js` defaults to `PORT=3000`, which collides with Vite. Local dev requires `PORT=3001` so the Vite `/api` proxy resolves. This is set in `server/.env` (gitignored — recreate it with at least `PORT=3001` if it is missing).
- **`server/node_modules` used to be committed and was broken** (incomplete `debug` package). It is now untracked/gitignored, and the update script installs it with `npm ci --prefix server`. If you ever see `Cannot find module './common'` from `debug`, run `npm ci` inside `server/`.
- **Graceful degradation is expected.** Without external API keys (IndianAPI, Groww, Perplexity, OpenAI, FRED, etc.) and without Supabase env vars, the app still boots. Market/news/IPO endpoints return empty/fallback data and CMS/auth/search show empty states. These empty states are **not bugs**; they only mean no secrets are configured. Provider keys live in root `.env` (see `.env.example`); frontend Supabase uses `VITE_SUPABASE_URL` / `VITE_SUPABASE_ANON_KEY`.
- **Intelligence Engine is currently broken by a pre-existing syntax error** in `intelligence-engine/app/tools/agib_client.py` (`settings = get_settings()` on line 17 is not indented inside `__init__`). This makes `uvicorn app.main:app` fail to import and makes `pytest` fail at collection. The dependencies still install fine; fix the indentation to run the engine or its tests.

### Lint / test / build

- **No frontend/server lint or test suites are configured** (root `package.json` has only `dev`/`build`/`preview`; no ESLint config file despite `eslint` being installed; `server` `test` is a no-op).
- **Build:** `npm run build` (frontend → `dist/`).
- **Tests:** only `intelligence-engine` has `pytest` (`intelligence-engine/.venv/bin/python -m pytest`), but they currently fail to collect due to the syntax error noted above.
- **Node version:** `.nvmrc` pins `20.19.1`; the app runs fine on the Node 22 present in the image.
