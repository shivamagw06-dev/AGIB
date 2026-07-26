# External API Audit (`.env` keys)

**Scope:** keys documented in `.env.example`, `intelligence-engine/.env.example`, and `server/.env`  
**Ask AGI path:** `POST /api/ui/search` → IE `/v1/ui/search` → `UiService.search` → CAE / IRP  
**HDFC probe:** `Should I buy HDFC Bank?` via `UiService.search` with HTTP instrumentation (urllib / httpx / requests)  
**HDFC result:** **0 outbound HTTP hosts**. Reasoning used in-process SIF (`sector_id=banks`) + Finance Academy (FAPI). Recommendation gated: insufficient company evidence.  
**Runtime secrets in this environment:** all vendor keys **unset** (only empty Groww placeholders appear in `server/.env`). Status below is from **code wiring**, plus the HDFC replay.

**Status legend (primary):**
| Status | Meaning |
|---|---|
| Unused | Documented in `.env*` but never read in code |
| Configured | Read in code / adapter exists; no production vendor HTTP caller (or metadata-only) |
| Called | Production route can invoke vendor HTTP (when key is set) |
| Used in reasoning | Vendor response is fed into sync Ask AGI / CAE / IRP recommendation reasoning |

---

## Summary table

| API key | Loaded | Primary importers | Endpoints / HTTP | Production routes | Ask AGI / CAE / IRP use data? | Called on last HDFC Ask AGI? | Status |
|---|---|---|---|---|---|---|---|
| `GROWW_ACCESS_TOKEN` | `server/providers/groww.js`, `growwHealth.js`, nifty500 worker | market / intelligence / health services | Groww `api.groww.in` LTP / hist / token | `/api/market/*`, `/api/ui/home` | No (sync path) | **No** | Called |
| `GROWW_API_KEY` | same as Groww | groww auth alt | Groww token exchange | same Groww routes | No | **No** | Called |
| `GROWW_API_SECRET` | same as Groww | groww auth alt | Groww token exchange | same Groww routes | No | **No** | Called |
| `NEWSAPI_KEY` | `server/services/newsHeadlinesService.js` | news headlines | `newsapi.org/v2/top-headlines` | `/api/news/headlines` | No | **No** | Called |
| `OPENAI_API_KEY` | Node briefings; IE `Settings` → CIO synthesizer | market/macro/pre-market briefings; CIO | `api.openai.com/v1/chat/completions` | `/api/market/*-briefing`; `/api/intelligence/research/runs` | No direct; optional later via CIO→KIP ingest | **No** | Called |
| `ALPHAVANTAGE_API_KEY` | `macroContextService.js` | macro context | Alpha Vantage commodities | `/api/market/macro-briefing` | No | **No** | Called |
| `FRED_API_KEY` | `macroContextService.js` | macro context | FRED series | `/api/market/macro-briefing` | No | **No** | Called |
| `FINNHUB_API_KEY` | Node `preMarketContextService.js`; IE `MarketDataClient` | pre-market; IE adapter | Finnhub quote/calendar | `/api/market/pre-market-briefing`, `/api/ui/home` | No | **No** | Called |
| `TWELVE_DATA_API_KEY` | `preMarketContextService.js` | pre-market fallback | Twelve Data quote | pre-market / home enrichment | No | **No** | Called |
| `POLYGON_API_KEY` | `macroContextService.js` (`missingSources` only) | macro status metadata | **none** | none | No | **No** | Configured |
| `FMP_API_KEY` | Node missingSources; IE `FmpProvider` | IE market_data adapter | adapter only; no prod `get_*` caller | IE `/v1/market-data/health` only | No | **No** | Configured |
| `RBI_DATA_API_KEY` | `macroContextService.js` (`missingSources` only) | macro status metadata | **none** (AOI RBI uses public/offline path) | none | No | **No** | Configured |
| `EXCHANGERATE_API_KEY` | **nowhere** | — | — | — | No | **No** | Unused |
| `INDIANAPI_KEY` / `VITE_INDIANAPI_KEY` | `server/index.js`, `ui.js`, market/ipo/research services; some Vite | IndianAPI proxies & briefings | `stock.indianapi.in` | `/api/stock`, `/api/news`, `/api/ipo*`, market context, home ticker | No (sync Ask AGI) | **No** | Called |
| `INDIAN_API_KEY` (IE) | IE `Settings` → `IndianApiProvider` | market_data | adapter; no prod `get_*` | health only | No | **No** | Configured |
| `PERPLEXITY_KEY` / `PERPLEXITY_API_KEY` | `server/index.js`, `research.js` | deals / research summary | `api.perplexity.ai` | `/api/perplexity/deals`, `/research/summary` | No | **No** | Called |
| `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` | auth, newsletter, nifty500, macro repo, IE memory | backend persistence / admin | Supabase REST | `/api/auth/*`, `/api/newsletter/*`, nifty500 research | No (Ask AGI uses in-process stores) | **No** | Called |
| `VITE_SUPABASE_URL` + `VITE_SUPABASE_ANON_KEY` | `src/lib/supabaseClient.js` | frontend auth | Supabase Auth/API (browser) | Vite `/login` etc. | No | **No** | Called |
| `INTELLIGENCE_ENGINE_TOKEN` | Node `ui.js` / `intelligence.js` / CIO scheduler; IE Settings | BFF→IE auth | internal bearer (not a market vendor) | `/api/ui/*`, `/api/intelligence/*` | Auth only for Ask AGI BFF | Internal auth only (no vendor) | Called |
| `RESEND_API_KEY` | `auth.js`, `newsletter.js`, edge functions | email | Resend API | auth verification, newsletter | No | **No** | Called |
| `SENDGRID_API_KEY` | `auth.js` (fallback) | email | SendGrid | `/api/auth/send-verification` | No | **No** | Called |
| `VITE_TRADEWATCH_API_KEY` | `vite.config.js` only | Vite dev proxy header | `api.tradewatch.io` (dev proxy) | none in prod `src/` | No | **No** | Configured |
| `AGIB_SERVICE_TOKEN` | IE `Settings` → `AgibClient` | CIO desk → Node market APIs | Node `/api/market/*` (internal) | IE research runs / CIO | No (CIO path) | **No** | Configured |

---

## Ask AGI / CAE / IRP vs vendors

| Question | Finding |
|---|---|
| Do sync Ask AGI / CAE / IRP call market vendor APIs? | **No.** All reasoning engines run in-process. |
| Do they use vendor-returned payloads? | **No** on the sync path. Indirect only if a prior CIO/briefing ingest landed text into KIP. |
| What powered the last HDFC answer? | **SIF** (banks framework: NIM, CASA, credit cost, GNPA/NNPA, CET1, ROE, P/B) + **Finance Academy (FAPI)** + empty company evidence → recommendation **blocked**. |
| Any vendor key reached “Used in reasoning”? | **None.** |

---

## Load map (by surface)

### Node (`server/`)
- Groww → `providers/groww.js` → market intelligence / dashboard / pulse / briefing / home snapshot
- NewsAPI → `newsHeadlinesService.js` → `/api/news/headlines`
- OpenAI → `*BriefingService.js` (cached narrative layer)
- Macro vendors → `macroContextService.js` → macro-briefing
- Pre-market vendors → `preMarketContextService.js` → pre-market-briefing / home
- IndianAPI / Perplexity → `index.js`, `research.js`, market/ipo services
- Supabase / Resend / SendGrid → auth + newsletter + research publish

### Intelligence Engine (`intelligence-engine/`)
- `INTELLIGENCE_ENGINE_TOKEN`, optional `OPENAI_API_KEY`, `SUPABASE_*`, `AGIB_SERVICE_TOKEN`
- Market adapters (`INDIAN_API_KEY`, `FINNHUB_API_KEY`, `FMP_API_KEY`) wired in `app/market_data/` but **not called** by `UiService.search` / CAE / IRP

### Vite (`VITE_*`)
- Supabase anon client for login
- Optional IndianAPI / Tradewatch (Tradewatch: proxy-only)

---

## HDFC Bank request evidence

```
UiService.search("Should I buy HDFC Bank?")
→ outbound unique hosts: NONE
→ sector_id: banks
→ recommendation_gate.blocked: true
→ finance_academy.enabled: true
```

**Conclusion:** Every market/data vendor key is at best **Called** on other production surfaces (market briefings, research workers, auth/email). On Ask AGI/CAE/IRP — and specifically the last HDFC Bank request — vendor APIs were **not called** and their data was **not used in reasoning**.
