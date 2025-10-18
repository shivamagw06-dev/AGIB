// server/index.js
/**
 * Unified Express proxy for IndianAPI
 *
 * - Prefers server-only INDIANAPI_KEY (falls back to VITE_INDIANAPI_KEY)
 * - Sets trust proxy for hosted environments (Render)
 * - Handles upstream errors gracefully with caching & retry
 * - Adds a small 30s cache for /api/trending
 * - Maps upstream {"error": "..."} -> 502 for clarity
 */

import express from 'express';
import rateLimit from 'express-rate-limit';
import dotenv from 'dotenv';
import cors from 'cors';

dotenv.config();

const app = express();
app.use(express.json());

// --- CONFIG ---
const PORT = process.env.PORT || 3000;
const INDIANAPI_KEY = process.env.INDIANAPI_KEY || process.env.VITE_INDIANAPI_KEY || '';
const INDIANAPI_BASE = 'https://stock.indianapi.in';

if (!INDIANAPI_KEY) {
  console.warn('⚠️  INDIANAPI_KEY is not set. Requests requiring the API key will fail until you set it in environment variables.');
}

// --- MIDDLEWARE ---
app.use(cors({ origin: process.env.FRONTEND_ORIGIN || '*', methods: ['GET', 'OPTIONS'] }));
app.set('trust proxy', 1);
const apiLimiter = rateLimit({ windowMs: 60 * 1000, max: 100 });
app.use('/api', apiLimiter);

// --- HELPERS ---
function forwardHeaders() {
  const headers = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
    'User-Agent': 'AGIB-Proxy/1.0'
  };
  if (INDIANAPI_KEY) headers['x-api-key'] = INDIANAPI_KEY;
  return headers;
}

async function proxyFetch(res, url) {
  try {
    const r = await globalThis.fetch(url, { headers: forwardHeaders() });
    const text = await r.text();

    console.log(`[proxy] ${url} -> ${r.status}`);
    console.log('[proxy] first 200 chars:', text.slice(0, 200).replace(/\n/g, ' '));

    if (!text) return res.status(r.status).end();

    try {
      const json = JSON.parse(text);
      if (json && json.error) {
        console.log('[proxy] upstream error:', json.error);
        return res.status(502).json({ upstream_error: json.error, upstream_body: json });
      }
      return res.status(r.status).json(json);
    } catch {
      res.set('Content-Type', r.headers.get('content-type') || 'text/plain');
      return res.status(r.status).send(text);
    }
  } catch (err) {
    console.error('🔥 Proxy fetch failed:', err);
    return res.status(500).json({ error: 'Proxy fetch failed', detail: err?.message });
  }
}

// --- SIMPLE CACHE for trending (30s) ---
let trendingCache = null;
let trendingCacheExpiry = 0;

// --- ROUTES ---

// Health and root
app.get('/', (req, res) => res.json({ service: 'finance-news-backend', status: 'running' }));
app.get('/api/health', (req, res) => res.json({ ok: true }));

// Debug (safe)
app.get('/_debug_env', (req, res) => {
  res.json({
    INDIANAPI_KEY_exists: !!process.env.INDIANAPI_KEY,
    VITE_INDIANAPI_KEY_exists: !!process.env.VITE_INDIANAPI_KEY,
    FRONTEND_ORIGIN: process.env.FRONTEND_ORIGIN || null,
    PORT: process.env.PORT || null
  });
});

// ✅ Trending with retry, cache, fallback
app.get('/api/trending', async (req, res) => {
  const now = Date.now();
  if (trendingCache && now < trendingCacheExpiry) {
    console.log('[cache] returning cached trending');
    return res.json(trendingCache);
  }

  async function fetchOnce() {
    const r = await globalThis.fetch(`${INDIANAPI_BASE}/trending`, { headers: forwardHeaders() });
    const text = await r.text();
    let body;
    try { body = JSON.parse(text); } catch { body = text; }
    return { status: r.status, body, raw: text };
  }

  let last = null;
  for (let i = 0; i < 2; i++) {
    try {
      const result = await fetchOnce();
      if (result.body && result.body.error) {
        console.log(`[trending] upstream error attempt ${i + 1}:`, result.body.error);
        last = result;
        await new Promise(r => setTimeout(r, 500));
        continue;
      }
      trendingCache = result.body;
      trendingCacheExpiry = Date.now() + 30 * 1000;
      return res.status(result.status).json(result.body);
    } catch (err) {
      console.error(`[trending] fetch failed attempt ${i + 1}:`, err.message);
      await new Promise(r => setTimeout(r, 500));
    }
  }

  if (trendingCache) {
    console.log('[trending] returning cached fallback');
    return res.json({ data: trendingCache, upstream_issue: true });
  }

  return res.status(502).json({
    data: [],
    upstream_issue: true,
    upstream_last: last && last.body ? last.body : { error: 'unknown' }
  });
});

// Other endpoints
app.get('/api/stock', (req, res) => {
  const symbol = req.query.symbol || req.query.name;
  if (!symbol) return res.status(400).json({ error: 'Missing ?symbol or ?name' });
  return proxyFetch(res, `${INDIANAPI_BASE}/stock?name=${encodeURIComponent(symbol)}`);
});

app.get('/api/industry_search', (req, res) => {
  const q = req.query.query;
  if (!q) return res.status(400).json({ error: 'Missing ?query' });
  return proxyFetch(res, `${INDIANAPI_BASE}/industry_search?query=${encodeURIComponent(q)}`);
});

app.get('/api/mutual_fund_search', (req, res) => {
  const q = req.query.query;
  if (!q) return res.status(400).json({ error: 'Missing ?query' });
  return proxyFetch(res, `${INDIANAPI_BASE}/mutual_fund_search?query=${encodeURIComponent(q)}`);
});

app.get('/api/fetch_52_week_high_low_data', (req, res) =>
  proxyFetch(res, `${INDIANAPI_BASE}/fetch_52_week_high_low_data`)
);

app.get('/api/NSE_most_active', (req, res) =>
  proxyFetch(res, `${INDIANAPI_BASE}/NSE_most_active`)
);

app.get('/api/BSE_most_active', (req, res) =>
  proxyFetch(res, `${INDIANAPI_BASE}/BSE_most_active`)
);

app.get('/api/mutual_funds', (req, res) =>
  proxyFetch(res, `${INDIANAPI_BASE}/mutual_funds`)
);

app.get('/api/price_shockers', (req, res) =>
  proxyFetch(res, `${INDIANAPI_BASE}/price_shockers`)
);

app.get('/api/commodities', (req, res) =>
  proxyFetch(res, `${INDIANAPI_BASE}/commodities`)
);

app.get('/api/stock_target_price', (req, res) => {
  const id = req.query.stock_id;
  if (!id) return res.status(400).json({ error: 'Missing ?stock_id' });
  return proxyFetch(res, `${INDIANAPI_BASE}/stock_target_price?stock_id=${encodeURIComponent(id)}`);
});

app.get('/api/stock_forecasts', (req, res) => {
  const params = new URLSearchParams(req.query);
  return proxyFetch(res, `${INDIANAPI_BASE}/stock_forecasts?${params}`);
});

app.get('/api/historical_data', (req, res) => {
  const params = new URLSearchParams(req.query);
  return proxyFetch(res, `${INDIANAPI_BASE}/historical_data?${params}`);
});

app.get('/api/historical_stats', (req, res) => {
  const params = new URLSearchParams(req.query);
  return proxyFetch(res, `${INDIANAPI_BASE}/historical_stats?${params}`);
});

// Default 404
app.use((req, res) => res.status(404).json({ error: 'Not found' }));

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Proxy running on port ${PORT} — IndianAPI base: ${INDIANAPI_BASE}`);
});
