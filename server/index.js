// server/index.js
/**
 * Unified Express proxy for IndianAPI
 *
 * - Prefers server-only INDIANAPI_KEY (falls back to VITE_INDIANAPI_KEY)
 * - Sets trust proxy for hosted environments (Render)
 * - Upstream logging (no secrets)
 * - Maps upstream {"error": "..."} -> 502 for clarity
 * - Adds a small 30s cache for /api/trending
 *
 * Note: ESM import style — package.json should have "type": "module"
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
  console.warn(
    '⚠️  INDIANAPI_KEY is not set. Requests requiring the API key will fail until you set it in environment variables.'
  );
}

// --- MIDDLEWARE ---
// CORS - allow specific frontend or all for testing
app.use(cors({ origin: process.env.FRONTEND_ORIGIN || '*', methods: ['GET', 'OPTIONS'] }));

// Trust proxy headers so express-rate-limit can read client IPs on Render / proxies
app.set('trust proxy', 1);

// Apply rate limit to /api routes
const apiLimiter = rateLimit({ windowMs: 60 * 1000, max: 100 });
app.use('/api', apiLimiter);

// --- HELPERS ---
function forwardHeaders() {
  const headers = {
    'Content-Type': 'application/json',
    Accept: 'application/json'
  };
  if (INDIANAPI_KEY) headers['x-api-key'] = INDIANAPI_KEY;
  return headers;
}

/**
 * proxyFetch
 * - fetches url with forward headers
 * - logs upstream status/content-type + small body snippet (no secrets)
 * - if upstream returns JSON with an "error" field, we map to 502
 */
async function proxyFetch(res, url) {
  if (!INDIANAPI_KEY) {
    return res.status(500).json({ error: 'Server missing INDIANAPI_KEY environment variable' });
  }

  if (typeof globalThis.fetch !== 'function') {
    console.error('❌ global fetch is not available in this Node runtime.');
    return res.status(500).json({ error: 'Server runtime missing global fetch' });
  }

  try {
    const r = await globalThis.fetch(url, { headers: forwardHeaders() });
    const text = await r.text();

    // lightweight logging for debugging (no keys)
    console.log(`[proxy] upstream ${url} -> status ${r.status}`);
    console.log(`[proxy] upstream content-type: ${r.headers.get('content-type')}`);
    console.log('[proxy] upstream body (first 300 chars):', String(text).slice(0, 300).replace(/\n/g, ' '));

    if (!text) {
      res.status(r.status).end();
      console.log(`[proxy] ${url} -> ${r.status} (empty body)`);
      return;
    }

    try {
      const json = JSON.parse(text);

      // If upstream returned an error field, surface as 502 so clients know upstream failed
      if (json && json.error) {
        console.log('[proxy] upstream reported error:', json.error);
        return res.status(502).json({ upstream_error: json.error, upstream_body: json });
      }

      res.status(r.status).json(json);
      console.log(`[proxy] ${url} -> ${r.status} (json)`);
      return;
    } catch (parseErr) {
      // Not JSON — forward as text and preserve content-type where possible
      const contentType = r.headers.get('content-type') || 'text/plain; charset=utf-8';
      res.set('Content-Type', contentType);
      res.status(r.status).send(text);
      console.log(`[proxy] ${url} -> ${r.status} (text: ${contentType})`);
      return;
    }
  } catch (err) {
    console.error('🔥 Proxy fetch error for', url, err);
    return res.status(500).json({ error: 'Proxy fetch failed', detail: err?.message || String(err) });
  }
}

// --- SIMPLE CACHE for trending (30s) ---
let trendingCache = null;
let trendingCacheExpiry = 0;

// --- ROUTES ---
app.get('/', (req, res) => {
  res.json({
    service: 'finance-news-backend',
    status: 'running',
    endpoints: ['/api/health', '/api/trending', '/api/...']
  });
});

// Safe debug endpoint (does not expose secret values)
app.get('/_debug_env', (req, res) => {
  res.json({
    INDIANAPI_KEY_exists: !!process.env.INDIANAPI_KEY,
    VITE_INDIANAPI_KEY_exists: !!process.env.VITE_INDIANAPI_KEY,
    PORT: process.env.PORT || null,
    FRONTEND_ORIGIN: process.env.FRONTEND_ORIGIN || null
  });
});

// Health
app.get('/api/health', (req, res) => res.json({ ok: true }));

// Company data
app.get('/api/stock', (req, res) => {
  const symbolOrName = req.query.symbol || req.query.name;
  if (!symbolOrName) return res.status(400).json({ error: 'Missing ?symbol or ?name parameter' });
  return proxyFetch(res, `${INDIANAPI_BASE}/stock?name=${encodeURIComponent(symbolOrName)}`);
});

// Industry search
app.get('/api/industry_search', (req, res) => {
  const q = req.query.query;
  if (!q) return res.status(400).json({ error: 'Missing ?query' });
  return proxyFetch(res, `${INDIANAPI_BASE}/industry_search?query=${encodeURIComponent(q)}`);
});

// Mutual fund search
app.get('/api/mutual_fund_search', (req, res) => {
  const q = req.query.query;
  if (!q) return res.status(400).json({ error: 'Missing ?query' });
  return proxyFetch(res, `${INDIANAPI_BASE}/mutual_fund_search?query=${encodeURIComponent(q)}`);
});

// Trending with caching
app.get('/api/trending', async (req, res) => {
  const now = Date.now();
  if (trendingCache && now < trendingCacheExpiry) {
    console.log('[cache] returning cached trending');
    return res.json(trendingCache);
  }

  try {
    const r = await globalThis.fetch(`${INDIANAPI_BASE}/trending`, { headers: forwardHeaders() });
    const text = await r.text();
    let body;
    try { body = JSON.parse(text); } catch { body = text; }

    // If upstream reports an error, forward as 502
    if (body && body.error) {
      console.log('[proxy] upstream trending error:', body.error);
      return res.status(502).json({ upstream_error: body.error, upstream_body: body });
    }

    trendingCache = body;
    trendingCacheExpiry = Date.now() + 30 * 1000; // 30s cache
    return res.status(r.status).json(body);
  } catch (err) {
    console.error('🔥 Trending proxy failed', err);
    return res.status(502).json({ error: 'Upstream fetch failed', detail: err?.message || String(err) });
  }
});

// 52-week data
app.get('/api/fetch_52_week_high_low_data', (req, res) => proxyFetch(res, `${INDIANAPI_BASE}/fetch_52_week_high_low_data`));

// NSE / BSE most active
app.get('/api/NSE_most_active', (req, res) => proxyFetch(res, `${INDIANAPI_BASE}/NSE_most_active`));
app.get('/api/BSE_most_active', (req, res) => proxyFetch(res, `${INDIANAPI_BASE}/BSE_most_active`));

// Mutual funds
app.get('/api/mutual_funds', (req, res) => proxyFetch(res, `${INDIANAPI_BASE}/mutual_funds`));

// Price shockers
app.get('/api/price_shockers', (req, res) => proxyFetch(res, `${INDIANAPI_BASE}/price_shockers`));

// Commodities
app.get('/api/commodities', (req, res) => proxyFetch(res, `${INDIANAPI_BASE}/commodities`));

// Analyst recommendations (target price)
app.get('/api/stock_target_price', (req, res) => {
  const id = req.query.stock_id;
  if (!id) return res.status(400).json({ error: 'Missing ?stock_id' });
  return proxyFetch(res, `${INDIANAPI_BASE}/stock_target_price?stock_id=${encodeURIComponent(id)}`);
});

// Stock forecasts (pass-through params)
app.get('/api/stock_forecasts', (req, res) => {
  const params = new URLSearchParams(req.query);
  return proxyFetch(res, `${INDIANAPI_BASE}/stock_forecasts?${params.toString()}`);
});

// Historical data
app.get('/api/historical_data', (req, res) => {
  const params = new URLSearchParams(req.query);
  return proxyFetch(res, `${INDIANAPI_BASE}/historical_data?${params.toString()}`);
});

// Historical stats
app.get('/api/historical_stats', (req, res) => {
  const params = new URLSearchParams(req.query);
  return proxyFetch(res, `${INDIANAPI_BASE}/historical_stats?${params.toString()}`);
});

// Default 404
app.use((req, res) => res.status(404).json({ error: 'Not found' }));

// --- START SERVER ---
app.listen(PORT, () => {
  console.log(`🚀 Proxy running on port ${PORT} — IndianAPI base: ${INDIANAPI_BASE}`);
});
