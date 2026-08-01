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
import { getAgiIntelligence } from '../services/intelligenceService.js';
import { fetchNseIndices } from '../providers/fallback.js';
import { fetchYahooIndices } from '../providers/yahooIndices.js';
import {
  marketCycleCacheMaxAgeSeconds,
  oncePerMarketCycle,
} from '../config/marketRefresh.js';

function engineConfig() {
  let baseUrl = (process.env.INTELLIGENCE_ENGINE_URL || 'http://127.0.0.1:8100').replace(/\/$/, '');
  if (baseUrl && !/^https?:\/\//i.test(baseUrl)) {
    baseUrl = `https://${baseUrl}`;
  }
  const token = (process.env.INTELLIGENCE_ENGINE_TOKEN || 'dev-intelligence-token').trim();
  return { baseUrl, token };
}

async function engineFetch(
  path,
  { method = 'GET', body = null, timeoutMs = 360_000, headers: extraHeaders = null } = {},
) {
  const { baseUrl, token } = engineConfig();
  const response = await fetch(`${baseUrl}${path}`, {
    method,
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      'X-AGI-Intelligence-Token': token,
      ...(extraHeaders && typeof extraHeaders === 'object' ? extraHeaders : {}),
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
const CORE_GLOBAL = ['NASDAQ', 'S&P', 'Dow', 'Gold', 'Silver', 'Brent', 'Bitcoin', 'USDINR'];

/** ETF proxy prices must never be shown as cash index levels. */
function looksLikeEtfProxy(name, price) {
  const n = Number(price);
  if (!Number.isFinite(n) || n <= 0) return false;
  if (name === 'S&P' && n < 2000) return true; // SPY ~700s vs S&P cash ~thousands
  if (name === 'NASDAQ' && n < 5000) return true; // QQQ vs NASDAQ Composite
  if (name === 'Dow' && n < 10000) return true; // DIA vs Dow cash
  if (name === 'Gold' && n < 1000) return true; // GLD ETF vs gold futures/oz
  return false;
}

function normalizeSnapshotName(raw) {
  const key = String(raw || '').trim().toUpperCase();
  return SNAPSHOT_NAME_ALIASES[key] || null;
}

function snapshotPriority(raw) {
  const key = String(raw || '').trim().toUpperCase();
  return SNAPSHOT_SOURCE_PRIORITY[key] || 50;
}

function hasLivePrice(card) {
  const n = Number(card?.price);
  // Groww sometimes returns 0 for unresolved symbols — treat as missing.
  return Number.isFinite(n) && n > 0;
}

function isValidPrice(price) {
  const n = Number(price);
  return Number.isFinite(n) && n > 0;
}

async function buildMarketSnapshot() {
  return oncePerMarketCycle('home-market-snapshot', () => buildMarketSnapshotFresh());
}

async function buildMarketSnapshotFresh() {
  const cycleUpdatedAt = new Date().toISOString();
  const cards = [];
  const push = (name, price, percentChange, extra = {}, priority = 50) => {
    if (!name) return;
    const existing = cards.find((c) => c.name === name);
    const livePrice = isValidPrice(price) ? Number(price) : null;
    if (existing) {
      const existingPriority = Number(existing._priority || 0);
      const betterPriority = priority > existingPriority;
      if (hasLivePrice(existing) && !betterPriority) return;
      if (livePrice != null && (betterPriority || !hasLivePrice(existing))) {
        existing.price = livePrice;
        existing.percentChange = percentChange ?? existing.percentChange ?? null;
        existing.sparkline = sparkFromChange(existing.percentChange);
        existing._priority = priority;
        Object.assign(existing, extra);
      }
      return;
    }
    if (livePrice == null) return;
    cards.push({
      name,
      price: livePrice,
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
      if (!name || !isValidPrice(row.price)) continue;
      push(
        name,
        row.price,
        row.percentChange ?? row.change ?? null,
        {
          session: row.source === 'groww' ? 'Groww' : row.source === 'nse' ? 'NSE' : 'Live',
          updatedAt: cycleUpdatedAt,
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
      if (!name || !isValidPrice(row.price)) continue;
      push(
        name,
        row.price,
        row.percentChange ?? null,
        {
          session: 'NSE',
          updatedAt: cycleUpdatedAt,
        },
        snapshotPriority(row.name)
      );
    }
  } catch {
    /* soft */
  }

  // 3) Yahoo cash indices / commodities — preferred for global cards.
  // Pre-market context historically used ETF proxies (SPY/QQQ/DIA/GLD); those must not win.
  const missingYahoo = [...CORE_INDIAN, ...CORE_GLOBAL].filter((name) => {
    const card = cards.find((c) => c.name === name);
    return !hasLivePrice(card) || looksLikeEtfProxy(name, card.price);
  });
  if (missingYahoo.length) {
    try {
      const yahooRows = await fetchYahooIndices(missingYahoo);
      for (const row of yahooRows) {
        if (!isValidPrice(row.price) || looksLikeEtfProxy(row.name, row.price)) continue;
        push(
          row.name,
          row.price,
          row.percentChange ?? null,
          {
            session: 'Yahoo',
            updatedAt: cycleUpdatedAt,
          },
          120
        );
      }
    } catch {
      /* soft */
    }
  }

  // Global / commodity tone feed — only fill names still missing after Yahoo cash quotes.
  try {
    const { getPreMarketContext } = await import('../services/preMarketContextService.js');
    const ctx = await getPreMarketContext({ force: false });
    for (const m of ctx.globalMarkets || []) {
      const label = String(m.label || m.id || '').trim();
      if (!label) continue;
      let name = label;
      if (/nasdaq/i.test(label)) name = 'NASDAQ';
      else if (/s&p|spx/i.test(label)) name = 'S&P';
      else if (/dow/i.test(label)) name = 'Dow';
      else if (/gold/i.test(label)) name = 'Gold';
      else if (/silver/i.test(label)) name = 'Silver';
      else if (/brent|crude|wti|usoil/i.test(label)) name = 'Brent';
      else if (/bitcoin|btc/i.test(label)) name = 'Bitcoin';
      else if (/vix/i.test(label)) name = 'VIX';
      else continue;
      const price = m.level ?? m.price ?? null;
      if (looksLikeEtfProxy(name, price)) continue;
      if (hasLivePrice(cards.find((c) => c.name === name))) continue;
      push(name, price, m.changePct ?? m.percentChange ?? null, {
        session: m.source || 'Global',
        updatedAt: cycleUpdatedAt,
      }, 40);
    }
    for (const c of ctx.commodities || []) {
      const label = String(c.label || c.name || '');
      let name = null;
      if (/gold/i.test(label)) name = 'Gold';
      if (/silver/i.test(label)) name = 'Silver';
      if (/brent|crude/i.test(label)) name = 'Brent';
      if (!name) continue;
      const price = c.level ?? c.price ?? null;
      if (looksLikeEtfProxy(name, price)) continue;
      if (hasLivePrice(cards.find((x) => x.name === name))) continue;
      push(name, price, c.changePct ?? c.percentChange ?? null, {
        session: c.source || 'Global',
        updatedAt: cycleUpdatedAt,
      }, 40);
    }
  } catch {
    /* soft */
  }

  // USDINR via Frankfurter soft (Yahoo INR=X preferred above when available)
  try {
    if (!hasLivePrice(cards.find((c) => c.name === 'USDINR'))) {
      const fx = await fetch('https://api.frankfurter.app/latest?from=USD&to=INR', {
        signal: AbortSignal.timeout(8_000),
      });
      if (fx.ok) {
        const body = await fx.json();
        const rate = body?.rates?.INR;
        if (Number.isFinite(rate)) {
          push('USDINR', rate, null, { session: 'Frankfurter', updatedAt: cycleUpdatedAt }, 30);
        }
      }
    }
  } catch {
    /* soft */
  }

  // Soft desk close levels — last resort only. No Indian / US cash / commodity desk fakes.
  if (!cards.length) {
    const cached = cachedMarketSnapshot();
    if (cached.rows?.length) return cached.rows.map((row) => ({ ...row }));
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
  return cards.map(({ _priority, ...rest }) => ({
    ...rest,
    updatedAt: cycleUpdatedAt,
  }));
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
    // Warm AGI intelligence in the same 30-min cycle as the Groww/Yahoo snapshot
    // so Market Outlook strip and homepage prices refresh together.
    void getAgiIntelligence({
      indianApiKey: process.env.INDIANAPI_KEY || process.env.VITE_INDIANAPI_KEY || '',
      indianApiBase: process.env.INDIANAPI_BASE || 'https://stock.indianapi.in',
    }).catch(() => null);

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
      const maxAge = marketCycleCacheMaxAgeSeconds();
      res.set(
        'Cache-Control',
        `public, max-age=${Math.min(maxAge, 120)}, stale-while-revalidate=${Math.max(60, maxAge)}`
      );
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
    const question = req.body?.question || req.query.question;
    const ticker = req.body?.ticker || req.query.ticker;
    if (!question) {
      return res.status(400).json({ error: 'question is required' });
    }

    const askTimeoutMs = Math.max(
      30_000,
      Number.parseInt(process.env.ASK_ENGINE_TIMEOUT_MS || '120000', 10) || 120_000,
    );
    const httpStarted = Date.now();
    const day = new Date().toISOString().slice(0, 10).replace(/-/g, '');
    const gatewayTraceId =
      req.body?.ask_trace_id ||
      req.headers['x-ask-trace-id'] ||
      `ASK-${day}-${Math.random().toString(16).slice(2, 8).toUpperCase()}`;

    const buildTimeoutOrch = (detail, meta = {}) => {
      const elapsed = Date.now() - httpStarted;
      const timedOut = Boolean(meta.timeout);
      const funnel = { retrieved: 0, ranked: 0, passed: 0, referenced: 0 };
      const orch = {
        version: 'ask-orchestration-trace-2',
        ask_trace_id: gatewayTraceId,
        engine_reached: false,
        fallback: true,
        fallback_used: true,
        completed: false,
        timeout: timedOut,
        partial: true,
        last_completed_stage: timedOut ? 'http_ingress' : 'http_ingress',
        elapsed_ms: elapsed,
        reason: detail,
        timeout_ms: askTimeoutMs,
        engine_status: meta.engineStatus ?? null,
        html_502: Boolean(meta.html502),
        entity: {
          name: ticker ? String(ticker).toUpperCase() : null,
          detected: ticker ? String(ticker).toUpperCase() : null,
          confidence: ticker ? 0.95 : 0,
          question_excerpt: String(question || '').slice(0, 160),
        },
        funnel,
        evidence: funnel,
        latency: {
          http_ms: elapsed,
          total_ms: elapsed,
          http_ingress_ms: 0,
          entity_ms: 0,
          ikl_ms: 0,
          retrieval_ms: 0,
          ranking_ms: 0,
          reasoning_ms: 0,
          assembly_ms: 0,
          serialization_ms: 0,
          last_completed_stage: 'http_ingress',
          stages: { http_ingress: 0, http: elapsed },
          warnings: timedOut
            ? [
                {
                  kind: 'gateway_engine_timeout',
                  elapsed_ms: elapsed,
                  threshold_ms: askTimeoutMs,
                  ask_trace_id: gatewayTraceId,
                },
              ]
            : [],
        },
        diagnostics_visibility: 'internal',
        execution_trace: [
          `Ask Trace ID: ${gatewayTraceId}`,
          `Entity: ${ticker ? String(ticker).toUpperCase() : '—'} (${ticker ? '0.95' : '—'})`,
          'IKL: 0ms',
          'Retrieved: 0',
          'Ranked: 0',
          'Passed: 0',
          'Referenced: 0',
          'Reasoning: 0.0s',
          'Assembly: 0ms',
          'Completed: false',
          'Last completed stage: http_ingress',
          `Elapsed: ${(elapsed / 1000).toFixed(1)}s`,
          timedOut ? 'Timeout: true' : 'Fallback: true',
        ].join('\n'),
        trace_summary: `Trace: ${gatewayTraceId} | Timeout: ${timedOut ? 'Yes' : 'No'} | Fallback: Yes | Last stage: http_ingress | Total: ${(elapsed / 1000).toFixed(1)}s`,
      };
      return orch;
    };

    const serveFallback = async (detail, meta = {}) => {
      try {
        const { buildAskDeskFallback } = await import('../services/askDeskFallback.js');
        const pack = await buildAskDeskFallback(question);
        pack.detail = detail;
        pack.ask_orchestration = {
          ...(pack.ask_orchestration || {}),
          ...buildTimeoutOrch(detail, meta),
        };
        res.setHeader('X-Ask-Trace-Id', gatewayTraceId);
        // Best-effort wake for the next client retry.
        engineFetch('/v1/health', { timeoutMs: 8_000 }).catch(() => {});
        return res.status(200).json(pack);
      } catch (fallbackError) {
        return res.status(503).json({
          error: 'research_desk_unavailable',
          retryable: true,
          detail: detail || fallbackError.message,
          ask_orchestration: buildTimeoutOrch(detail || fallbackError.message, meta),
        });
      }
    };

    try {
      const qs = new URLSearchParams({ question: String(question) });
      if (ticker) qs.set('ticker', String(ticker));
      const path = `/v1/ui/search?${qs.toString()}`;
      // Default 120s (env ASK_ENGINE_TIMEOUT_MS). Client may retry a fresh request.
      const result = await engineFetch(path, {
        method: 'POST',
        body: {
          question: String(question),
          ask_trace_id: gatewayTraceId,
          ...(ticker ? { ticker: String(ticker) } : {}),
        },
        timeoutMs: askTimeoutMs,
        headers: { 'X-Ask-Trace-Id': gatewayTraceId },
      });
      const html502 =
        typeof result.data?.raw === 'string' && result.data.raw.trim().startsWith('<');
      if (html502 || result.status === 502 || result.status === 503 || result.status >= 500) {
        return serveFallback(
          `Intelligence engine unavailable (HTTP ${result.status}${html502 ? ', HTML body' : ''}) — Node desk fallback.`,
          { engineStatus: result.status, html502, timeout: false },
        );
      }
      if (result.data && typeof result.data === 'object') {
        const orch =
          result.data.ask_orchestration || result.data.degradation?.ask_orchestration || {};
        const httpMs = Date.now() - httpStarted;
        result.data.ask_orchestration = {
          ...orch,
          ask_trace_id: orch.ask_trace_id || gatewayTraceId,
          engine_reached: true,
          fallback: false,
          fallback_used: false,
          completed: orch.completed !== false,
          timeout: Boolean(orch.timeout),
          last_completed_stage:
            orch.last_completed_stage || orch.latency?.last_completed_stage || 'serialization',
          elapsed_ms: orch.elapsed_ms || orch.latency?.total_ms || httpMs,
          timeout_ms: askTimeoutMs,
          engine_status: result.status,
          latency: {
            ...(orch.latency || {}),
            http_ms: httpMs,
          },
          diagnostics_visibility: 'internal',
        };
        res.setHeader('X-Ask-Trace-Id', result.data.ask_orchestration.ask_trace_id);
      }
      return res.status(result.status).json(result.data);
    } catch (error) {
      const timedOut =
        error?.name === 'TimeoutError' || /aborted|timeout/i.test(String(error?.message || ''));
      const msg = timedOut
        ? `Intelligence engine exceeded ASK timeout (${askTimeoutMs}ms) — Node desk fallback.`
        : error.message;
      return serveFallback(msg, { engineStatus: 0, timeout: timedOut });
    }
  });

  return router;
}
