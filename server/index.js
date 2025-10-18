// server/index.js
/**
 * Unified Express proxy for IndianAPI
 * (Minimal changes: prefer INDIANAPI_KEY, add _debug_env and light upstream logs)
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
// prefer server-only var first
const INDIANAPI_KEY = process.env.INDIANAPI_KEY || process.env.VITE_INDIANAPI_KEY || '';
const INDIANAPI_BASE = 'https://stock.indianapi.in';

if (!INDIANAPI_KEY) {
  console.warn(
    '⚠️  INDIANAPI_KEY is not set. Requests requiring the API key will fail until you set it in environment variables.'
  );
}

// --- MIDDLEWARE ---
app.use(cors({ origin: process.env.FRONTEND_ORIGIN || '*', methods: ['GET', 'OPTIONS'] }));

const apiLimiter = rateLimit({ windowMs: 60 * 1000, max: 100 });
app.use('/api', apiLimiter);

function forwardHeaders() {
  const headers = { 'Content-Type': 'application/json', Accept: 'application/json' };
  if (INDIANAPI_KEY) headers['x-api-key'] = INDIANAPI_KEY;
  return headers;
}

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

    // lightweight upstream logging for debugging (no secrets)
    console.log(`[proxy] upstream ${url} -> status ${r.status}`);
    console.log(`[proxy] upstream content-type: ${r.headers.get('content-type')}`);
    console.log('[proxy] upstream body (first 300 chars):', text.slice(0, 300).replace(/\n/g, ' '));

    if (!text) {
      res.status(r.status).end();
      console.log(`[proxy] ${url} -> ${r.status} (empty body)`);
      return;
    }

    try {
      const json = JSON.parse(text);
      res.status(r.status).json(json);
      console.log(`[proxy] ${url} -> ${r.status} (json)`);
      return;
    } catch {
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

app.get('/', (req, res) => {
  res.json({ service: 'finance-news-backend', status: 'running', endpoints: ['/api/health', '/api/trending', '/api/...'] });
});

app.get('/_debug_env', (req, res) => {
  res.json({
    INDIANAPI_KEY_exists: !!process.env.INDIANAPI_KEY,
    VITE_INDIANAPI_KEY_exists: !!process.env.VITE_INDIANAPI_KEY,
    PORT: process.env.PORT || null,
    FRONTEND_ORIGIN: process.env.FRONTEND_ORIGIN || null
  });
});

app.get('/api/health', (req, res) => res.json({ ok: true }));

app.get('/api/stock', (req, res) => {
  const symbolOrName = req.query.symbol || req.query.name;
  if (!symbolOrName) return res.status(400).json({ error: 'Missing ?symbol or ?name parameter' });
  return proxyFetch(res, `${INDIANAPI_BASE}/stock?name=${encodeURIComponent(symbolOrName)}`);
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

app.get('/api/trending', (req, res) => proxyFetch(res, `${INDIANAPI_BASE}/trending`));
app.get('/api/fetch_52_week_high_low_data', (req, res) => proxyFetch(res, `${INDIANAPI_BASE}/fetch_52_week_high_low_data`));
app.get('/api/NSE_most_active', (req, res) => proxyFetch(res, `${INDIANAPI_BASE}/NSE_most_active`));
app.get('/api/BSE_most_active', (req, res) => proxyFetch(res, `${INDIANAPI_BASE}/BSE_most_active`));
app.get('/api/mutual_funds', (req, res) => proxyFetch(res, `${INDIANAPI_BASE}/mutual_funds`));
app.get('/api/price_shockers', (req, res) => proxyFetch(res, `${INDIANAPI_BASE}/price_shockers`));
app.get('/api/commodities', (req, res) => proxyFetch(res, `${INDIANAPI_BASE}/commodities`));

app.get('/api/stock_target_price', (req, res) => {
  const id = req.query.stock_id;
  if (!id) return res.status(400).json({ error: 'Missing ?stock_id' });
  return proxyFetch(res, `${INDIANAPI_BASE}/stock_target_price?stock_id=${encodeURIComponent(id)}`);
});

app.get('/api/stock_forecasts', (req, res) => {
  const params = new URLSearchParams(req.query);
  return proxyFetch(res, `${INDIANAPI_BASE}/stock_forecasts?${params.toString()}`);
});

app.get('/api/historical_data', (req, res) => {
  const params = new URLSearchParams(req.query);
  return proxyFetch(res, `${INDIANAPI_BASE}/historical_data?${params.toString()}`);
});

app.get('/api/historical_stats', (req, res) => {
  const params = new URLSearchParams(req.query);
  return proxyFetch(res, `${INDIANAPI_BASE}/historical_stats?${params.toString()}`);
});

app.use((req, res) => res.status(404).json({ error: 'Not found' }));

app.listen(PORT, () => {
  console.log(`🚀 Proxy running on port ${PORT} — IndianAPI base: ${INDIANAPI_BASE}`);
});
