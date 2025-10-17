// server/index.js
/**
 * Unified Express proxy for IndianAPI
 *
 * Note: this file uses ESM `import`. Ensure your server/package.json
 * has "type": "module" (or convert imports to require() for CommonJS).
 */

import express from 'express';
import rateLimit from 'express-rate-limit';
import dotenv from 'dotenv';
import cors from 'cors';

// Load .env for local development (Render will provide env vars)
dotenv.config();

const app = express();
app.use(express.json());

// --- CONFIG ---
const PORT = process.env.PORT || 3000;
const INDIANAPI_KEY = process.env.VITE_INDIANAPI_KEY || process.env.INDIANAPI_KEY || '';
const INDIANAPI_BASE = 'https://stock.indianapi.in';

if (!INDIANAPI_KEY) {
  console.warn(
    '⚠️  INDIANAPI_KEY is not set. Requests requiring the API key will fail with 500 until you set it in environment variables.'
  );
}

// --- MIDDLEWARE ---
// Allow all origins for testing; restrict in production via FRONTEND_ORIGIN
app.use(cors({ origin: process.env.FRONTEND_ORIGIN || '*', methods: ['GET', 'OPTIONS'] }));

// Apply rate limit only to /api routes so health and root are unaffected
const apiLimiter = rateLimit({ windowMs: 60 * 1000, max: 100 });
app.use('/api', apiLimiter);

/** forwardHeaders
 *  ensures we always send the API key + expected headers to IndianAPI
 */
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
 * - Uses global fetch (Node 18+). If response body is JSON returns res.json(),
 *   otherwise forwards raw text with original status and content-type.
 */
async function proxyFetch(res, url) {
  if (!INDIANAPI_KEY) {
    // For security we return explicit error rather than forwarding a call that will likely fail.
    return res.status(500).json({ error: 'Server missing INDIANAPI_KEY environment variable' });
  }

  if (typeof globalThis.fetch !== 'function') {
    console.error('❌ global fetch is not available in this Node runtime.');
    return res.status(500).json({ error: 'Server runtime missing global fetch' });
  }

  try {
    const r = await globalThis.fetch(url, { headers: forwardHeaders() });

    // read raw text (some endpoints might return plain text or HTML on error)
    const text = await r.text();

    // If no body, forward status with empty body
    if (!text) {
      res.status(r.status).end();
      console.log(`[proxy] ${url} -> ${r.status} (empty body)`);
      return;
    }

    // Try parse JSON
    try {
      const json = JSON.parse(text);
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

// --- ROUTES ---

// Root route — useful when you open service root on browser (no 404 JSON at root)
app.get('/', (req, res) => {
  res.json({ service: 'finance-news-backend', status: 'running', endpoints: ['/api/health', '/api/trending', '/api/...'] });
});

// Health for Render / monitoring
app.get('/api/health', (req, res) => res.json({ ok: true }));

// 1️⃣ Company data
app.get('/api/stock', (req, res) => {
  const symbolOrName = req.query.symbol || req.query.name;
  if (!symbolOrName) return res.status(400).json({ error: 'Missing ?symbol or ?name parameter' });
  return proxyFetch(res, `${INDIANAPI_BASE}/stock?name=${encodeURIComponent(symbolOrName)}`);
});

// 2️⃣ Industry search
app.get('/api/industry_search', (req, res) => {
  const q = req.query.query;
  if (!q) return res.status(400).json({ error: 'Missing ?query' });
  return proxyFetch(res, `${INDIANAPI_BASE}/industry_search?query=${encodeURIComponent(q)}`);
});

// 3️⃣ Mutual fund search
app.get('/api/mutual_fund_search', (req, res) => {
  const q = req.query.query;
  if (!q) return res.status(400).json({ error: 'Missing ?query' });
  return proxyFetch(res, `${INDIANAPI_BASE}/mutual_fund_search?query=${encodeURIComponent(q)}`);
});

// 4️⃣ Trending
app.get('/api/trending', (req, res) => proxyFetch(res, `${INDIANAPI_BASE}/trending`));

// 5️⃣ 52-week data
app.get('/api/fetch_52_week_high_low_data', (req, res) => proxyFetch(res, `${INDIANAPI_BASE}/fetch_52_week_high_low_data`));

// 6️⃣ NSE / BSE most active
app.get('/api/NSE_most_active', (req, res) => proxyFetch(res, `${INDIANAPI_BASE}/NSE_most_active`));
app.get('/api/BSE_most_active', (req, res) => proxyFetch(res, `${INDIANAPI_BASE}/BSE_most_active`));

// 7️⃣ Mutual funds
app.get('/api/mutual_funds', (req, res) => proxyFetch(res, `${INDIANAPI_BASE}/mutual_funds`));

// 8️⃣ Price shockers
app.get('/api/price_shockers', (req, res) => proxyFetch(res, `${INDIANAPI_BASE}/price_shockers`));

// 9️⃣ Commodities
app.get('/api/commodities', (req, res) => proxyFetch(res, `${INDIANAPI_BASE}/commodities`));

// 🔟 Analyst recommendations
app.get('/api/stock_target_price', (req, res) => {
  const id = req.query.stock_id;
  if (!id) return res.status(400).json({ error: 'Missing ?stock_id' });
  return proxyFetch(res, `${INDIANAPI_BASE}/stock_target_price?stock_id=${encodeURIComponent(id)}`);
});

// 11️⃣ Stock forecasts
app.get('/api/stock_forecasts', (req, res) => {
  const params = new URLSearchParams(req.query);
  return proxyFetch(res, `${INDIANAPI_BASE}/stock_forecasts?${params.toString()}`);
});

// 12️⃣ Historical data
app.get('/api/historical_data', (req, res) => {
  const params = new URLSearchParams(req.query);
  return proxyFetch(res, `${INDIANAPI_BASE}/historical_data?${params.toString()}`);
});

// 13️⃣ Historical stats
app.get('/api/historical_stats', (req, res) => {
  const params = new URLSearchParams(req.query);
  return proxyFetch(res, `${INDIANAPI_BASE}/historical_stats?${params.toString()}`);
});

// Default 404 JSON for everything else
app.use((req, res) => res.status(404).json({ error: 'Not found' }));

// --- START SERVER ---
app.listen(PORT, () => {
  console.log(`🚀 Proxy running on port ${PORT} — IndianAPI base: ${INDIANAPI_BASE}`);
});
