/**
 * server/index.js
 * Unified Express proxy for IndianAPI
 */

import express from 'express';
import rateLimit from 'express-rate-limit';
import dotenv from 'dotenv';
import cors from 'cors';
import fetch from 'node-fetch';

dotenv.config({ path: '../.env.local' });

const app = express();
app.use(express.json());

// --- CONFIG ---
const PORT = process.env.PORT || 3001;
const INDIANAPI_KEY = process.env.VITE_INDIANAPI_KEY || process.env.INDIANAPI_KEY || '';
const INDIANAPI_BASE = 'https://stock.indianapi.in';

if (!INDIANAPI_KEY) {
  console.error('❌ Missing INDIANAPI_KEY in .env.local');
  process.exit(1);
}

// --- MIDDLEWARE ---
app.use(cors({ origin: '*', methods: ['GET'] }));
app.use(rateLimit({ windowMs: 60 * 1000, max: 100 }));

function forwardHeaders() {
  return {
    'x-api-key': INDIANAPI_KEY,
    'Content-Type': 'application/json',
    Accept: 'application/json',
  };
}

async function proxyFetch(res, url) {
  try {
    const r = await fetch(url, { headers: forwardHeaders() });
    const text = await r.text();
    try {
      const json = JSON.parse(text);
      return res.status(r.status).json(json);
    } catch {
      return res.status(r.status).send(text);
    }
  } catch (err) {
    console.error('🔥 Fetch error:', err.message);
    res.status(500).json({ error: 'Proxy fetch failed', detail: err.message });
  }
}

// --- ROUTES ---
app.get('/api/health', (req, res) => res.json({ ok: true }));

// 1️⃣ Company data
app.get('/api/stock', (req, res) => {
  const name = req.query.name || req.query.symbol;
  if (!name) return res.status(400).json({ error: 'Missing ?name parameter' });
  return proxyFetch(res, `${INDIANAPI_BASE}/stock?name=${encodeURIComponent(name)}`);
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

// 🧩 Default 404 JSON
app.use((req, res) => res.status(404).json({ error: 'Not found' }));

// --- START SERVER ---
app.listen(PORT, () => console.log(`🚀 Proxy running on port ${PORT}`));
