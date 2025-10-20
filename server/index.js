// server/index.js
// IndianAPI proxy + research router
// - mounts ./research.js at /research
// - provides /api/* proxy endpoints to IndianAPI
// - robust headers / JSON parsing / error handling
// - small caching for /api/trending

import express from "express";
import researchRouter from "./research.js";
import rateLimit from "express-rate-limit";
import cors from "cors";
import dotenv from "dotenv";

dotenv.config();

const app = express();
app.use(express.json({ limit: "200kb" }));
app.set("trust proxy", 1);

const PORT = process.env.PORT ? Number(process.env.PORT) : 3000;
const BASE_URL = process.env.INDIANAPI_BASE || "https://stock.indianapi.in";

const API_KEY = (process.env.INDIANAPI_KEY || process.env.VITE_INDIANAPI_KEY || "").toString().trim();
const PERPLEXITY_KEY = (process.env.PERPLEXITY_KEY || process.env.PERPLEXITY_API_KEY || process.env.VITE_PERPLEXITY_KEY || "").toString().trim();
const PERPLEXITY_URL = process.env.PERPLEXITY_URL || "https://api.perplexity.ai/chat/completions";
const PERPLEXITY_MODEL_ENV = (process.env.PERPLEXITY_MODEL || "").trim();
const DEBUG_API = (process.env.DEBUG_API || "").toLowerCase() === "true";

if (!API_KEY) console.warn("⚠️ Missing INDIANAPI_KEY — some endpoints may return limited data.");
if (!PERPLEXITY_KEY) console.warn("⚠️ Missing PERPLEXITY_KEY — Perplexity-backed endpoints disabled.");

// CORS: prefer explicit FRONTEND_ORIGIN entries; don't use '*' when credentials true
const rawAllowed = (process.env.FRONTEND_ORIGIN || "").split(",").map(s => s.trim()).filter(Boolean);
const allowedOrigins = rawAllowed.length ? rawAllowed : [
  "https://agarwalglobalinvestments.com",
  "https://www.agarwalglobalinvestments.com"
];

app.use(cors({
  origin: (origin, cb) => {
    if (!origin) return cb(null, true); // server-to-server or curl
    if (allowedOrigins.includes(origin)) return cb(null, true);
    return cb(new Error("CORS origin not allowed"));
  },
  methods: ["GET", "POST", "OPTIONS"],
  optionsSuccessStatus: 200,
  credentials: true,
}));

// Rate limiting
const apiLimiter = rateLimit({ windowMs: 60_000, max: 120, standardHeaders: true, legacyHeaders: false });
const researchLimiter = rateLimit({ windowMs: 60_000, max: 30, standardHeaders: true, legacyHeaders: false });
app.use('/api', apiLimiter);
app.use('/research', researchLimiter);

// dynamic fetch implementation
let _fetchImpl = undefined;
async function ensureFetch() {
  if (typeof _fetchImpl === 'function') return _fetchImpl;
  if (typeof globalThis.fetch === 'function') {
    _fetchImpl = globalThis.fetch.bind(globalThis);
    return _fetchImpl;
  }
  try {
    const mod = await import('node-fetch');
    _fetchImpl = mod.default;
    return _fetchImpl;
  } catch (e) {
    console.error('Failed to load node-fetch dynamically:', e?.message || e);
    throw e;
  }
}

// fetch with timeout and timeout flag
async function fetchWithTimeout(url, opts = {}, timeoutMs = 15_000) {
  const fetchFn = await ensureFetch();
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const merged = { ...opts, signal: controller.signal };
    const resp = await fetchFn(url, merged);
    clearTimeout(id);
    return resp;
  } catch (err) {
    clearTimeout(id);
    if (err && (err.name === 'AbortError' || /aborted/i.test(String(err.message || '')))) {
      const e = new Error('Upstream request timed out');
      e.isTimeout = true;
      throw e;
    }
    throw err;
  }
}

function makeHeaders() {
  const h = { Accept: 'application/json', 'Content-Type': 'application/json', 'User-Agent': 'AGIB-Proxy/1.0' };
  if (API_KEY) h['x-api-key'] = API_KEY;
  return h;
}

async function proxyFetch(res, url, opts = {}) {
  try {
    console.log(`[proxy] -> ${url}`);
    const r = await fetchWithTimeout(url, { method: opts.method || 'GET', headers: opts.headers || makeHeaders(), body: opts.body }, opts.timeout || 15_000);
    const ct = (r.headers.get('content-type') || '').toLowerCase();
    const text = await r.text().catch(() => '');

    console.log(`[proxy] ${url} returned ${r.status} content-type:${ct} length:${String(text?.length || 0)}`);

    if (!text) return res.status(r.status).end();

    if ([401, 402, 403].includes(r.status)) {
      console.error(`[proxy][upstream ${r.status}] ${text.slice(0, 200)}`);
      res.set('Content-Type', ct || 'text/plain');
      return res.status(r.status).send(text);
    }

    if (ct.includes('application/json') || ct.includes('+json')) {
      try {
        const json = JSON.parse(text);
        if (json && (json.error || json.upstream_error)) {
          console.error('[proxy][upstream error]', json.error || json.upstream_error);
          return res.status(502).json({ upstream_error: json.error || json.upstream_error, upstream_body: json });
        }
        return res.status(r.status).json(json);
      } catch (parseErr) {
        console.error('[proxy] failed to parse JSON from upstream', parseErr?.message || parseErr);
        res.set('Content-Type', ct || 'application/json');
        return res.status(502).send(text);
      }
    }

    res.set('Content-Type', ct || 'text/plain');
    return res.status(r.status).send(text);
  } catch (err) {
    console.error('🔥 proxyFetch failed:', err?.message || err);
    if (err?.isTimeout) return res.status(504).json({ error: 'Upstream request timed out' });
    return res.status(500).json({ error: 'Proxy fetch failed', detail: err?.message || String(err) });
  }
}

// small in-memory trending cache (30s)
let trendingCache = null;
let trendingExpiry = 0;

function reg(path, handler) {
  app.get(path, handler);
  console.log('[route registered]', path);
}

// --- Health + debug endpoints
reg('/', (req, res) => res.json({ service: 'finance-news-backend', status: 'running' }));
reg('/api/health', (req, res) => res.json({ ok: true }));
reg('/_debug_env', (req, res) => res.json({ API_KEY_exists: !!API_KEY, PERPLEXITY_key_present: !!PERPLEXITY_KEY, FRONTEND_ORIGIN: process.env.FRONTEND_ORIGIN || null, PORT: process.env.PORT || null }));
reg('/_debug_key', (req, res) => { if (!API_KEY) return res.json({ key_present: false }); return res.json({ key_present: true, masked: `${API_KEY.slice(0,6)}... (length ${API_KEY.length})` }); });

// mount research router
app.use('/research', researchRouter);

/* ---------- /api/perplexity/deals ----------
   Ask Perplexity for a strict JSON array of deals with these fields:
   - acquirer, target, value (string), value_number (number, optional), sector, type, date (ISO), source (URL), image (URL), summary (string)
   The endpoint WILL try multiple models (env override -> defaults) and parse choices[0].message.content robustly.
*/
reg('/api/perplexity/deals', async (req, res) => {
  try {
    const region = req.query.region || 'global';
    const limit = Math.min(50, Number(req.query.limit || 8));

    if (!PERPLEXITY_KEY) {
      console.warn('[perplexity] PERPLEXITY_KEY missing — returning empty array');
      return res.json([]);
    }

    // Strong prompt to force structured JSON output
    const structuredPrompt = `
Return a JSON array (max ${limit}) of recent M&A / PE deals for region: ${region}.
Each array item MUST be an object with the following keys:
- acquirer (string)
- target (string)
- value (string|null) e.g. "1.5 billion USD" or null
- value_number (number|null) USD amount if determinable (e.g. 1500000000)
- sector (string|null)
- type (string) one of "M&A", "PE", "Debt", "JV", etc.
- date (string|null) ISO 8601 date if available
- source (string|null) direct URL to the news/article
- image (string|null) an image URL or og:image if available
- summary (string|null) 1-2 sentence investor-facing summary

Return ONLY valid JSON (a single top-level JSON array). Do not include any explanation text or markdown.
`.trim();

    // models to try (env override first)
    const candidateModels = PERPLEXITY_MODEL_ENV ? [PERPLEXITY_MODEL_ENV, 'sonar', 'sonar-pro'] : ['sonar', 'sonar-pro'];

    let pRes = null, pText = "", usedModel = null;

    for (const mdl of candidateModels) {
      const body = {
        model: mdl,
        messages: [
          { role: 'system', content: 'You are a factual research assistant. Respond only with JSON when asked.' },
          { role: 'user', content: structuredPrompt },
        ],
        temperature: 0.1,
        max_tokens: 1200,
      };

      try {
        console.log(`[perplexity] trying model=${mdl}`);
        pRes = await fetchWithTimeout(PERPLEXITY_URL, {
          method: 'POST',
          headers: { Authorization: `Bearer ${PERPLEXITY_KEY}`, 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        }, 30_000);

        pText = await pRes.text().catch(() => "");

        if (pRes.ok) { usedModel = mdl; break; }

        // if model invalid, try next
        if (pRes.status === 400 && /invalid_model/i.test(pText)) {
          console.warn(`[perplexity] model "${mdl}" invalid — trying next candidate`);
          pRes = null; pText = "";
          continue;
        }

        // other error: break and fallback
        console.error(`[perplexity] model ${mdl} returned ${pRes.status}:`, String(pText).slice(0,300));
        break;
      } catch (err) {
        console.error(`[perplexity] request failed for model=${mdl}:`, err?.message || err);
        pRes = null; pText = "";
        continue;
      }
    }

    if (!pRes || !pRes.ok) {
      console.error('[perplexity] no successful model response; returning empty array');
      return res.json([]);
    }

    const rawText = pText;
    if (DEBUG_API) console.warn(`[perplexity] RAW RESPONSE (model=${usedModel}) (truncated):`, String(rawText).slice(0, 2000));

    // parsing: prefer choices[0].message.content, then fallbacks
    let parsed = null;
    try {
      const respObj = JSON.parse(rawText);
      const reply = respObj?.choices?.[0]?.message?.content ?? respObj?.choices?.[0]?.text ?? null;

      if (typeof reply === 'string' && reply.trim()) {
        try {
          parsed = JSON.parse(reply);
        } catch (innerErr) {
          // try to extract array substring inside reply
          const arrMatch = String(reply).match(/\[\s*(?:\{[\s\S]*?\}\s*,?\s*)+\s*\]/m);
          if (arrMatch) {
            try { parsed = JSON.parse(arrMatch[0]); } catch (ee) { parsed = null; }
          }
        }
      }

      // final fallback: try array substring from the full rawText
      if (!Array.isArray(parsed)) {
        const anyArr = String(rawText).match(/\[\s*(?:\{[\s\S]*?\}\s*,?\s*)+\s*\]/m);
        if (anyArr) {
          try { parsed = JSON.parse(anyArr[0]); } catch (ee) { parsed = null; }
        }
      }
    } catch (e) {
      const fallback = String(rawText).match(/\[\s*(?:\{[\s\S]*?\}\s*,?\s*)+\s*\]/m);
      if (fallback) {
        try { parsed = JSON.parse(fallback[0]); } catch (ee) { parsed = null; }
      } else parsed = null;
    }

    if (!Array.isArray(parsed)) {
      if (DEBUG_API) console.warn('[perplexity] unexpected shape from API, returning empty array; raw (truncated):', String(rawText).slice(0,2000));
      return res.json([]);
    }

    // Normalize items: keep required fields consistent
    const normalized = parsed.slice(0, limit).map(it => ({
      acquirer: it?.acquirer ?? it?.buyer ?? null,
      target: it?.target ?? it?.company ?? null,
      value: it?.value ?? null,
      value_number: typeof it?.value_number === 'number' ? it.value_number : (it?.value_number ? Number(it.value_number) : null),
      sector: it?.sector ?? null,
      region: it?.region ?? region,
      date: it?.date ?? null,
      source: it?.source ?? null,
      image: it?.image ?? null,
      summary: it?.summary ?? null,
      type: it?.type ?? 'M&A'
    }));

    return res.json(normalized);
  } catch (err) {
    console.error('Perplexity proxy failed:', err);
    if (err?.isTimeout) return res.status(504).json({ error: 'Perplexity request timed out' });
    return res.json([]);
  }
});

/* --- /api/quote (tries multiple upstream endpoints) --- */
reg('/api/quote', async (req, res) => {
  try {
    const symbol = req.query.symbol || req.query.name;
    if (!symbol) return res.status(400).json({ error: 'Missing ?symbol or ?name' });

    const candidates = [
      `${BASE_URL}/stock?name=${encodeURIComponent(symbol)}`,
      `${BASE_URL}/stock?symbol=${encodeURIComponent(symbol)}`,
      `${BASE_URL}/quote?symbol=${encodeURIComponent(symbol)}`
    ];

    let lastErr = null;
    for (const url of candidates) {
      try {
        const r = await fetchWithTimeout(url, { method: 'GET', headers: makeHeaders() }, 15_000);
        const ct = (r.headers.get('content-type') || '').toLowerCase();
        const text = await r.text().catch(() => '');
        if (!text) { lastErr = new Error(`empty upstream response ${r.status} from ${url}`); continue; }
        if (!r.ok) { lastErr = new Error(`${r.status} : ${text}`); if (r.status >= 500) { res.set('Content-Type', ct || 'text/plain'); return res.status(r.status).send(text); } continue; }
        if (ct.includes('json') || ct.includes('+json')) {
          try {
            const json = JSON.parse(text);
            const cp = json.currentPrice ?? json.current_price ?? json.price ?? json.last_price ?? json.lastTradedPrice ?? null;
            const percent = json.percentChange ?? json.changePercent ?? json.percent_change ?? json.percent ?? json.change ?? null;
            const volume = json.volume ?? json.totalVolume ?? json.v ?? null;
            const prevClose = json.prevClose ?? json.previous_close ?? json.prev_close ?? null;
            const openPrice = json.openPrice ?? json.open ?? null;
            const dayRange = json.dayRange ?? (json.low && json.high ? { low: json.low, high: json.high } : null);
            return res.json({ currentPrice: cp, percentChange: percent, volume, prevClose, openPrice, dayRange, raw: json });
          } catch (e) {
            res.set('Content-Type', ct || 'text/plain');
            return res.status(200).send(text);
          }
        }
        res.set('Content-Type', ct || 'text/plain');
        return res.status(200).send(text);
      } catch (err) { lastErr = err; continue; }
    }
    return res.status(502).json({ error: 'Upstream quote fetch failed', detail: String(lastErr?.message || lastErr) });
  } catch (err) {
    console.error('/api/quote failed:', err);
    return res.status(500).json({ error: 'Internal server error', detail: String(err?.message || err) });
  }
});

// --- many proxy endpoints (unchanged) ---
reg('/api/stock', (req, res) => { const q = req.query.name || req.query.symbol; if (!q) return res.status(400).json({ error: 'Missing ?name or ?symbol' }); return proxyFetch(res, `${BASE_URL}/stock?name=${encodeURIComponent(q)}`); });
reg('/api/industry_search', (req, res) => { const q = req.query.query; if (!q) return res.status(400).json({ error: 'Missing ?query' }); return proxyFetch(res, `${BASE_URL}/industry_search?query=${encodeURIComponent(q)}`); });
reg('/api/mutual_fund_search', (req, res) => { const q = req.query.query; if (!q) return res.status(400).json({ error: 'Missing ?query' }); return proxyFetch(res, `${BASE_URL}/mutual_fund_search?query=${encodeURIComponent(q)}`); });

reg('/api/trending', async (req, res) => {
  const now = Date.now();
  if (trendingCache && now < trendingExpiry) { console.log('[trending] returning cache'); return res.json(trendingCache); }
  try {
    const r = await fetchWithTimeout(`${BASE_URL}/trending`, { headers: makeHeaders(), method: 'GET' }, 15_000);
    const ct = (r.headers.get('content-type') || '').toLowerCase();
    const text = await r.text().catch(() => '');
    if (!text) return res.status(r.status).end();
    if (ct.includes('application/json') || ct.includes('+json')) {
      try {
        const json = JSON.parse(text);
        trendingCache = json;
        trendingExpiry = Date.now() + 30_000;
        return res.status(r.status).json(json);
      } catch (parseErr) {
        console.error('[trending] parse error:', parseErr?.message || parseErr);
        return res.status(502).json({ error: 'Invalid trending JSON' });
      }
    } else {
      return res.status(r.status).send(text);
    }
  } catch (err) {
    console.error('trending fetch failed:', err?.message || err);
    if (trendingCache) return res.json({ data: trendingCache, upstream_issue: true });
    return res.status(502).json({ error: 'Upstream trending error', detail: err?.message || String(err) });
  }
});

reg('/api/fetch_52_week_high_low_data', (req, res) => proxyFetch(res, `${BASE_URL}/fetch_52_week_high_low_data`));
reg('/api/NSE_most_active', (req, res) => proxyFetch(res, `${BASE_URL}/NSE_most_active`));
reg('/api/BSE_most_active', (req, res) => proxyFetch(res, `${BASE_URL}/BSE_most_active`));
reg('/api/mutual_funds', (req, res) => proxyFetch(res, `${BASE_URL}/mutual_funds`));
reg('/api/price_shockers', (req, res) => proxyFetch(res, `${BASE_URL}/price_shockers`));
reg('/api/commodities', (req, res) => proxyFetch(res, `${BASE_URL}/commodities`));
reg('/api/stock_target_price', (req, res) => { const id = req.query.stock_id; if (!id) return res.status(400).json({ error: 'Missing ?stock_id' }); return proxyFetch(res, `${BASE_URL}/stock_target_price?stock_id=${encodeURIComponent(id)}`); });
reg('/api/stock_forecasts', (req, res) => { const params = new URLSearchParams(req.query); if (!params.has('stock_id')) return res.status(400).json({ error: 'Missing required ?stock_id' }); return proxyFetch(res, `${BASE_URL}/stock_forecasts?${params.toString()}`); });

reg('/api/historical_data', async (req, res) => {
  try {
    const symbol = req.query.symbol || req.query.stock_id || req.query.name;
    if (!symbol) return res.status(400).json({ error: 'Missing required ?symbol or ?stock_id or ?name' });
    const qs = new URLSearchParams(req.query).toString();
    const upstream = `${BASE_URL}/historical_data?${qs}`;
    const r = await fetchWithTimeout(upstream, { method: 'GET', headers: makeHeaders() }, 20_000);
    const ct = (r.headers.get('content-type') || '').toLowerCase();
    const text = await r.text().catch(() => '');
    if (!r.ok) { res.set('Content-Type', ct || 'text/plain'); return res.status(r.status).send(text); }
    if (ct.includes('application/json') || ct.includes('+json')) { try { const json = JSON.parse(text); return res.status(200).json(json); } catch (e) { res.set('Content-Type', ct || 'text/plain'); return res.status(200).send(text); } }
    res.set('Content-Type', ct || 'text/plain'); return res.status(200).send(text);
  } catch (err) { console.error('/api/historical_data failed:', err); return res.status(500).json({ error: 'Internal server error', detail: String(err?.message || err) }); }
});

reg('/api/historical_stats', (req, res) => proxyFetch(res, `${BASE_URL}/historical_stats?${new URLSearchParams(req.query).toString()}`));
reg('/api/news', (req, res) => proxyFetch(res, `${BASE_URL}/news`));
reg('/api/ipo', (req, res) => proxyFetch(res, `${BASE_URL}/ipo`));
reg('/api/recent_announcements', (req, res) => proxyFetch(res, `${BASE_URL}/recent_announcements`));
reg('/api/corporate_actions', (req, res) => proxyFetch(res, `${BASE_URL}/corporate_actions`));
reg('/api/statement', (req, res) => proxyFetch(res, `${BASE_URL}/statement`));

// wildcard fallback
reg('/api/:path(*)', (req, res) => {
  const path = req.params.path || '';
  const qs = new URLSearchParams(req.query).toString();
  const upstream = `${BASE_URL}/${path}${qs ? `?${qs}` : ''}`;
  console.log(`[wildcard proxy] /api/${path} -> ${upstream}`);
  return proxyFetch(res, upstream);
});

reg('/__routes', (req, res) => {
  const routes = [];
  (app._router.stack || []).forEach(layer => { if (layer.route && layer.route.path) routes.push({ path: layer.route.path, methods: Object.keys(layer.route.methods).join(',') }); });
  res.json(routes);
});

app.use((req, res) => res.status(404).json({ error: 'Not found', path: req.path }));

// start server
const server = app.listen(PORT, () => {
  console.log(`🚀 IndianAPI Proxy running on port ${PORT} — Base: ${BASE_URL}`);
});

process.on('SIGTERM', () => {
  console.info('SIGTERM received — closing HTTP server');
  server.close(() => {
    console.info('HTTP server closed');
    process.exit(0);
  });
});

export default app;
