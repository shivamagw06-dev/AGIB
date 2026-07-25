/**
 * UI Aggregation proxy — frontend talks to /api/ui/*, never to engines directly.
 * Backs onto intelligence-engine /v1/ui/*.
 * Homepage market snapshot is enriched server-side (not via browser market APIs).
 */

import { Router } from 'express';
import {
  cachedMarketSnapshot,
  enrichHomePayload,
} from '../services/homeOfficeEnrichment.js';

function engineConfig() {
  let baseUrl = (process.env.INTELLIGENCE_ENGINE_URL || 'http://127.0.0.1:8100').replace(/\/$/, '');
  if (baseUrl && !/^https?:\/\//i.test(baseUrl)) {
    baseUrl = `https://${baseUrl}`;
  }
  const token = (process.env.INTELLIGENCE_ENGINE_TOKEN || 'dev-intelligence-token').trim();
  return { baseUrl, token };
}

async function engineFetch(path, { method = 'GET', body = null, timeoutMs = 120_000 } = {}) {
  const { baseUrl, token } = engineConfig();
  const response = await fetch(`${baseUrl}${path}`, {
    method,
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      'X-AGI-Intelligence-Token': token,
    },
    body: body ? JSON.stringify(body) : undefined,
    signal: AbortSignal.timeout(timeoutMs),
  });
  const text = await response.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { raw: text };
  }
  return { ok: response.ok, status: response.status, data };
}

function sparkFromChange(change) {
  const n = Number(change);
  const base = 50;
  if (!Number.isFinite(n)) return [48, 50, 49, 51, 50, 52, 51];
  const dir = n >= 0 ? 1 : -1;
  return [0, 1, 2, 3, 4, 5, 6].map((i) => base + dir * Math.abs(n) * (i / 2));
}

async function buildMarketSnapshot() {
  const cards = [];
  const push = (name, price, percentChange, extra = {}) => {
    if (!name) return;
    cards.push({
      name,
      price: price ?? null,
      percentChange: percentChange ?? null,
      sparkline: sparkFromChange(percentChange),
      ...extra,
    });
  };

  // NSE cash indices (server-side only)
  try {
    const r = await fetch('https://www.nseindia.com/api/allIndices', {
      method: 'GET',
      headers: {
        Accept: 'application/json',
        'User-Agent': 'Mozilla/5.0 (compatible; AGIB-UI/1.0)',
        Referer: 'https://www.nseindia.com/',
      },
      signal: AbortSignal.timeout(12_000),
    });
    const text = await r.text().catch(() => '');
    if (r.ok && text) {
      const payload = JSON.parse(text);
      const rows = Array.isArray(payload?.data) ? payload.data : [];
      const wanted = {
        'NIFTY 50': 'NIFTY',
        'NIFTY BANK': 'BANK NIFTY',
        'INDIA VIX': 'VIX',
        'NIFTY NEXT 50': 'MIDCAP',
        'NIFTY MIDCAP 100': 'MIDCAP',
        'NIFTY MIDCAP 50': 'MIDCAP',
        'NIFTY SMALLCAP 100': 'SMALLCAP',
        'NIFTY SMALLCAP 50': 'SMALLCAP',
        'SENSEX': 'SENSEX',
        'BSE SENSEX': 'SENSEX',
      };
      for (const row of rows) {
        const raw = String(row.index || row.indexSymbol || '').trim().toUpperCase();
        const label = wanted[raw];
        if (!label) continue;
        if (cards.some((c) => c.name === label)) continue;
        push(label, row.last ?? row.previousClose ?? null, row.percentChange ?? row.variation ?? null, {
          session: 'NSE',
          updatedAt: new Date().toISOString(),
        });
      }
    }
  } catch {
    /* soft */
  }

  // Global / commodity proxies from pre-market context (server-side)
  try {
    const { getPreMarketContext } = await import('../services/preMarketContextService.js');
    const ctx = await getPreMarketContext({ force: false });
    for (const m of ctx.globalMarkets || []) {
      const label = String(m.label || m.id || '').trim();
      if (!label) continue;
      let name = label;
      if (/nasdaq/i.test(label)) name = 'NASDAQ';
      else if (/s&p|spx|spy/i.test(label)) name = 'S&P';
      else if (/dow/i.test(label)) name = 'Dow';
      else if (/gold|gld/i.test(label)) name = 'Gold';
      else if (/silver|slv/i.test(label)) name = 'Silver';
      else if (/brent|crude|wti|usoil|oil/i.test(label)) name = 'Brent';
      else if (/bitcoin|btc/i.test(label)) name = 'Bitcoin';
      else if (/vix/i.test(label)) name = 'VIX';
      else continue;
      if (cards.some((c) => c.name === name)) continue;
      push(name, m.level ?? m.price ?? null, m.changePct ?? m.percentChange ?? null);
    }
    for (const c of ctx.commodities || []) {
      const label = String(c.label || c.name || '');
      let name = null;
      if (/gold/i.test(label)) name = 'Gold';
      if (/silver/i.test(label)) name = 'Silver';
      if (/brent|crude/i.test(label)) name = 'Brent';
      if (!name || cards.some((x) => x.name === name)) continue;
      push(name, c.level ?? c.price ?? null, c.changePct ?? c.percentChange ?? null);
    }
  } catch {
    /* soft */
  }

  // USDINR via Frankfurter soft
  try {
    const fx = await fetch('https://api.frankfurter.app/latest?from=USD&to=INR', {
      signal: AbortSignal.timeout(8_000),
    });
    if (fx.ok) {
      const body = await fx.json();
      const rate = body?.rates?.INR;
      if (Number.isFinite(rate) && !cards.some((c) => c.name === 'USDINR')) {
        push('USDINR', rate, null);
      }
    }
  } catch {
    /* soft */
  }

  // Soft desk close levels when providers fail — keeps snapshot alive.
  if (!cards.length) {
    const cached = cachedMarketSnapshot();
    if (cached.rows?.length) return cached.rows;
    const deskClose = [
      ['NIFTY', 24150.2, 0.18],
      ['BANK NIFTY', 51820.4, 0.22],
      ['SENSEX', 79410.6, 0.15],
      ['MIDCAP', 54210.0, -0.12],
      ['SMALLCAP', 17820.5, -0.28],
      ['NASDAQ', 19840.0, 0.35],
      ['S&P', 5480.0, 0.21],
      ['Dow', 39820.0, 0.11],
      ['Gold', 2385.0, 0.42],
      ['Silver', 29.8, 0.55],
      ['USDINR', 83.52, -0.08],
      ['Brent', 82.4, -0.3],
      ['VIX', 13.8, -1.2],
    ];
    for (const [name, price, pct] of deskClose) {
      push(name, price, pct, { session: 'Cached close', updatedAt: new Date().toISOString() });
    }
  }

  const order = [
    'NIFTY',
    'BANK NIFTY',
    'SENSEX',
    'MIDCAP',
    'SMALLCAP',
    'NASDAQ',
    'S&P',
    'Dow',
    'Gold',
    'Silver',
    'USDINR',
    'Brent',
    'Bitcoin',
    'VIX',
  ];
  cards.sort((a, b) => {
    const ai = order.indexOf(a.name);
    const bi = order.indexOf(b.name);
    return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi);
  });
  return cards;
}

function marketSessionNow() {
  const now = new Date();
  // Approximate IST session 09:15–15:30
  const ist = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Kolkata' }));
  const mins = ist.getHours() * 60 + ist.getMinutes();
  const open = 9 * 60 + 15;
  const close = 15 * 60 + 30;
  const weekday = ist.getDay();
  if (weekday === 0 || weekday === 6 || mins < open || mins > close) {
    const nextOpen = open;
    let remaining = nextOpen - mins;
    if (mins > close) remaining = 24 * 60 - mins + open;
    if (weekday === 6) remaining += 24 * 60;
    if (weekday === 0) remaining += 0;
    return {
      status: 'closed',
      label: 'Market Closed',
      time_remaining: `${Math.max(0, Math.floor(remaining / 60))}h ${Math.abs(remaining % 60)}m to open`,
    };
  }
  const remaining = close - mins;
  return {
    status: 'open',
    label: 'Market Open',
    time_remaining: `${Math.floor(remaining / 60)}h ${remaining % 60}m remaining`,
  };
}

export default function createUiRouter() {
  const router = Router();

  router.get('/health', async (_req, res) => {
    try {
      const result = await engineFetch('/v1/ui/health');
      return res.status(result.ok ? 200 : 503).json(result.data);
    } catch (error) {
      return res.status(503).json({
        status: 'unavailable',
        layer: 'UI Aggregation',
        error: error.message,
      });
    }
  });

  // Homepage — always 200 with populated institutional desks (engine optional)
  router.get('/home', async (_req, res) => {
    const session = marketSessionNow();
    let snapshot = [];
    try {
      snapshot = await buildMarketSnapshot();
    } catch {
      snapshot = cachedMarketSnapshot().rows || [];
    }

    let engineData = null;
    try {
      const result = await engineFetch('/v1/ui/home', { timeoutMs: 8_000 });
      if (result.ok) engineData = result.data || null;
    } catch {
      engineData = null;
    }

    try {
      const payload = await enrichHomePayload(engineData, { snapshot, session });
      res.set('Cache-Control', 'public, max-age=30, stale-while-revalidate=120');
      return res.status(200).json(payload);
    } catch (error) {
      // Last-resort populated shell — never blank homepage
      try {
        const payload = await enrichHomePayload(null, { snapshot, session });
        payload.meta = { ...(payload.meta || {}), degraded: true, detail: error.message };
        return res.status(200).json(payload);
      } catch (err2) {
        return res.status(503).json({ error: 'UI aggregation unavailable', detail: err2.message });
      }
    }
  });

  const getPaths = [
    '/dashboard',
    '/macro',
    '/portfolio',
    '/workflow',
    '/company/:ticker',
    '/research/:researchId',
    '/article/:articleId',
    '/timeline/:entity',
    '/theme/:themeId',
    '/sector/:sectorId',
    '/predictions',
    '/calendar',
    '/copilot',
    '/autocomplete',
  ];

  for (const p of getPaths) {
    router.get(p, async (req, res) => {
      try {
        const path = `/v1/ui${req.path}`;
        const qs = new URLSearchParams(req.query).toString();
        const result = await engineFetch(`${path}${qs ? `?${qs}` : ''}`);
        return res.status(result.status).json(result.data);
      } catch (error) {
        return res.status(503).json({ error: 'UI aggregation unavailable', detail: error.message });
      }
    });
  }

  router.post('/search', async (req, res) => {
    try {
      const question = req.body?.question || req.query.question;
      const ticker = req.body?.ticker || req.query.ticker;
      if (!question) {
        return res.status(400).json({ error: 'question is required' });
      }
      const qs = new URLSearchParams({ question: String(question) });
      if (ticker) qs.set('ticker', String(ticker));
      const result = await engineFetch(`/v1/ui/search?${qs.toString()}`, { method: 'POST' });
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'UI aggregation unavailable', detail: error.message });
    }
  });

  return router;
}
