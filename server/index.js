/**
 * server/index.js (ESM)
 * Loads ../.env.local and proxies Indian API endpoints using x-api-key.
 */

import express from 'express';
import rateLimit from 'express-rate-limit';
import dotenv from 'dotenv';

// ✅ Load environment variables from project root .env.local
dotenv.config({ path: '../.env.local' });

const app = express();
app.use(express.json());

// Simple rate limiter for safety
const limiter = rateLimit({
  windowMs: 60 * 1000,
  max: 120,
});
app.use(limiter);

// --- API Setup ---
const INDIANAPI_BASE = 'https://stock.indianapi.in';
const INDIANAPI_KEY = process.env.VITE_INDIANAPI_KEY || process.env.INDIANAPI_KEY || '';

if (!INDIANAPI_KEY) {
  console.error('❌ Missing INDIANAPI_KEY in .env.local');
  process.exit(1);
}

console.log('✅ Loaded INDIANAPI_KEY from .env.local');

// --- Helper: Forward headers to upstream ---
function forwardHeaders() {
  return {
    'x-api-key': INDIANAPI_KEY,
    'Content-Type': 'application/json',
    Accept: 'application/json',
  };
}

// --- Core proxy function ---
async function proxyFetch(res, url) {
  try {
    console.log('➡️ Fetching:', url);

    const r = await fetch(url, { headers: forwardHeaders() });
    const text = await r.text();

    console.log('⬅️ Upstream status:', r.status);

    try {
      const json = JSON.parse(text);
      return res.status(r.status).json(json);
    } catch {
      return res.status(r.status).send(text);
    }
  } catch (err) {
    console.error('🔥 Fetch error:', err);
    return res.status(500).json({ error: 'Proxy fetch error' });
  }
}

// --- Routes ---
app.get('/api/trending', (req, res) => {
  const url = `${INDIANAPI_BASE}/trending`;
  return proxyFetch(res, url);
});

app.get('/api/stock', (req, res) => {
  const symbol = req.query.symbol;
  if (!symbol) return res.status(400).json({ error: 'Missing symbol query param' });
  const url = `${INDIANAPI_BASE}/stock?symbol=${encodeURIComponent(symbol)}`;
  return proxyFetch(res, url);
});

app.get('/api/health', (req, res) => res.json({ ok: true }));

// --- Start server ---
const PORT = process.env.PORT || 3001;
app.listen(PORT, () => console.log(`🚀 Server proxy listening on ${PORT}`));
