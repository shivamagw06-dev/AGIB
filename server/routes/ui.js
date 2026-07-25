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
import { getTickerData } from '../services/marketDataService.js';
import { fetchNseIndices } from '../providers/fallback.js';
import { fetchYahooIndices } from '../providers/yahooIndices.js';

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

const SNAPSHOT_NAME_ALIASES = {
  'NIFTY 50': 'NIFTY',
  NIFTY: 'NIFTY',
  'NIFTY BANK': 'BANK NIFTY',
  'BANK NIFTY': 'BANK NIFTY',
  BANKNIFTY: 'BANK NIFTY',
  SENSEX: 'SENSEX',
  'BSE SENSEX': 'SENSEX',
  'S&P BSE SENSEX': 'SENSEX',
  'INDIA VIX': 'VIX',
  VIX: 'VIX',
  'NIFTY MIDCAP 100': 'MIDCAP',
  'NIFTY MIDCAP 50': 'MIDCAP',
  // Next 50 is a weaker stand-in — only used if Midcap 100/50 are missing.
  'NIFTY NEXT 50': 'MIDCAP',
  MIDCAP: 'MIDCAP',
  'NIFTY SMALLCAP 100': 'SMALLCAP',
  'NIFTY SMALLCAP 50': 'SMALLCAP',
  'NIFTY SMLCAP 100': 'SMALLCAP',
  SMALLCAP: 'SMALLCAP',
};

/** Higher wins when multiple raw indices map to the same snapshot label. */
const SNAPSHOT_SOURCE_PRIORITY = {
  'NIFTY 50': 100,
  NIFTY: 100,
  'NIFTY BANK': 100,
  'BANK NIFTY': 100,
  BANKNIFTY: 100,
  SENSEX: 100,
  'BSE SENSEX': 90,
  'S&P BSE SENSEX': 90,
  'INDIA VIX': 100,
  VIX: 100,
  'NIFTY MIDCAP 100': 100,
  MIDCAP: 95,
  'NIFTY MIDCAP 50': 80,
  'NIFTY NEXT 50': 40,
  'NIFTY SMALLCAP 100': 100,
  'NIFTY SMLCAP 100': 95,
  SMALLCAP: 90,
  'NIFTY SMALLCAP 50': 70,
};

const CORE_INDIAN = ['NIFTY', 'BANK NIFTY', 'SENSEX', 'MIDCAP', 'SMALLCAP', 'VIX'];

function normalizeSnapshotName(raw) {
  const key = String(raw || '').trim().toUpperCase();
  return SNAPSHOT_NAME_ALIASES[key] || null;
}

function snapshotPriority(raw) {
  const key = String(raw || '').trim().toUpperCase();
  return SNAPSHOT_SOURCE_PRIORITY[key] || 50;
}

function hasLivePrice(card) {
  return card && Number.isFinite(Number(card.price));
}

async function buildMarketSnapshot() {
  const cards = [];
  const push = (name, price, percentChange, extra = {}, priority = 50) => {
    if (!name) return;
    const existing = cards.find((c) => c.name === name);
    const livePrice = Number(price);
    if (existing) {
      const existingPriority = Number(existing._priority || 0);
      const betterPriority = priority > existingPriority;
      if (hasLivePrice(existing) && !betterPriority) return;
      if (Number.isFinite(livePrice) && (betterPriority || !hasLivePrice(existing))) {
        existing.price = livePrice;
        existing.percentChange = percentChange ?? existing.percentChange ?? null;
        existing.sparkline = sparkFromChange(existing.percentChange);
        existing._priority = priority;
        Object.assign(existing, extra);
      }
      return;
    }
    cards.push({
      name,
      price: Number.isFinite(livePrice) ? livePrice : price ?? null,
      percentChange: percentChange ?? null,
      sparkline: sparkFromChange(percentChange),
      _priority: priority,
      ...extra,
    });
  };

  // 1) Groww primary (+ NSE inside marketDataService when Groww is thin)
  try {
    const ticker = await getTickerData({
      indianApiKey: process.env.INDIANAPI_KEY || process.env.VITE_INDIANAPI_KEY || '',
      indianApiBase: process.env.INDIANAPI_BASE || 'https://stock.indianapi.in',
    });
    for (const row of ticker?.items || []) {
      const raw = row.name || row.label;
      const name = normalizeSnapshotName(raw);
      if (!name) continue;
      if (!Number.isFinite(Number(row.price))) continue;
      push(
        name,
        row.price,
        row.percentChange ?? row.change ?? null,
        {
          session: row.source === 'groww' ? 'Groww' : row.source === 'nse' ? 'NSE' : 'Live',
          updatedAt: ticker.updatedAt || new Date().toISOString(),
        },
        snapshotPriority(raw) + (row.source === 'groww' ? 5 : 0)
      );
    }
  } catch {
    /* soft */
  }

  // 2) Direct NSE allIndices (covers MIDCAP / SMALLCAP beyond Groww ticker set)
  try {
    const nseRows = await fetchNseIndices();
    for (const row of nseRows) {
      const name = normalizeSnapshotName(row.name);
      if (!name || !Number.isFinite(Number(row.price))) continue;
      push(
        name,
        row.price,
        row.percentChange ?? null,
        {
          session: 'NSE',
          updatedAt: new Date().toISOString(),
        },
        snapshotPriority(row.name)
      );
    }
  } catch {
    /* soft */
  }

  // 3) Yahoo fallback — matches Groww/NSE prints when cloud hosts block NSE
  const missingCore = CORE_INDIAN.filter((name) => !hasLivePrice(cards.find((c) => c.name === name)));
  if (missingCore.length) {
    try {
      const yahooRows = await fetchYahooIndices(missingCore);
      for (const row of yahooRows) {
        if (!Number.isFinite(Number(row.price))) continue;
        push(
          row.name,
          row.price,
          row.percentChange ?? null,
          {
            session: 'Yahoo',
            updatedAt: new Date().toISOString(),
          },
          snapshotPriority(row.name) - 10
        );
      }
    } catch {
      /* soft */
    }
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
      push(name, m.level ?? m.price ?? null, m.changePct ?? m.percentChange ?? null);
    }
    for (const c of ctx.commodities || []) {
      const label = String(c.label || c.name || '');
      let name = null;
      if (/gold/i.test(label)) name = 'Gold';
      if (/silver/i.test(label)) name = 'Silver';
      if (/brent|crude/i.test(label)) name = 'Brent';
      if (!name) continue;
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
      if (Number.isFinite(rate)) push('USDINR', rate, null);
    }
  } catch {
    /* soft */
  }

  // Soft desk close levels — ONLY for still-missing names. Never override live Indian quotes.
  // Indian index desk numbers are intentionally omitted so stale 51k Bank Nifty cannot resurface.
  const deskClose = [
    ['NASDAQ', 19840.0, 0.35],
    ['S&P', 5480.0, 0.21],
    ['Dow', 39820.0, 0.11],
    ['Gold', 2385.0, 0.42],
    ['Silver', 29.8, 0.55],
    ['USDINR', 83.52, -0.08],
    ['Brent', 82.4, -0.3],
  ];
  if (!cards.length) {
    const cached = cachedMarketSnapshot();
    if (cached.rows?.length) return cached.rows.map((row) => ({ ...row }));
  }
  for (const [name, price, pct] of deskClose) {
    const existing = cards.find((c) => c.name === name);
    if (!existing) {
      push(name, price, pct, { session: 'Cached close', updatedAt: new Date().toISOString() });
      continue;
    }
    if (!hasLivePrice(existing)) {
      existing.price = price;
      existing.percentChange = existing.percentChange ?? pct;
      existing.sparkline = existing.sparkline?.length ? existing.sparkline : sparkFromChange(pct);
      existing.session = existing.session || 'Cached close';
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
  return cards.map(({ _priority, ...rest }) => rest);
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
    // BFF homepage enrichment can serve /api/ui/home without the Python engine.
    // Report operational+degraded instead of hard-unavailable when only the engine is down.
    let engine = null;
    try {
      const result = await engineFetch('/v1/ui/health', { timeoutMs: 5_000 });
      engine = {
        ok: Boolean(result.ok),
        status: result.status,
        data: result.data,
      };
    } catch (error) {
      engine = { ok: false, status: 503, error: error.message };
    }

    const payload = {
      status: engine.ok ? 'ok' : 'degraded',
      layer: 'UI Aggregation',
      architecture_status: 'v1.0.1 LOCKED',
      bff: {
        home: true,
        enrichment: true,
        note: 'Express /api/ui/home serves AGI intelligence + institutional desk defaults even when the engine is offline.',
      },
      engine: engine.ok
        ? { status: 'ok', detail: engine.data }
        : {
            status: 'unavailable',
            error: engine.error || engine.data?.error || 'fetch failed',
            hint: 'Set INTELLIGENCE_ENGINE_URL to a live agib-intelligence-engine service and redeploy.',
          },
    };
    return res.status(200).json(payload);
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
