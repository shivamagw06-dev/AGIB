/**
 * AGI Market Intelligence API routes
 * Always returns 200 with data — stale cache or fallback on upstream errors.
 */

import { Router } from 'express';
import { getAgiIntelligence, getDashboardFromIntelligence } from '../services/intelligenceService.js';
import { MARKET_REFRESH_MS } from '../config/marketRefresh.js';

const CACHE_CONTROL = `public, max-age=${Math.floor(MARKET_REFRESH_MS / 1000)}, stale-while-revalidate=60`;

function sendJson(res, data) {
  res.set('Cache-Control', CACHE_CONTROL);
  return res.status(200).json(data);
}

export default function createMarketRouter(env = {}) {
  const router = Router();

  router.get('/intelligence', async (_req, res) => {
    const data = await getAgiIntelligence(env);
    return sendJson(res, data);
  });

  router.get('/dashboard', async (_req, res) => {
    try {
      const data = await getDashboardFromIntelligence(env);
      return sendJson(res, data);
    } catch (err) {
      console.error('[market/dashboard]', err?.message);
      const fallback = await getAgiIntelligence(env);
      return sendJson(res, {
        pulse: fallback.pulse,
        outlook: fallback.outlook,
        gainers: fallback.stocksInFocus?.filter((s) => s.trend === 'Bullish') || [],
        losers: [],
        breadth: fallback.breadth,
        stocksInFocus: fallback.stocksInFocus || [],
        sectors: fallback.sectors || [],
        summary: fallback.summary,
        insightStrip: fallback.insightStrip,
        stale: true,
      });
    }
  });

  router.get('/pulse', async (_req, res) => {
    const data = await getAgiIntelligence(env);
    return sendJson(res, { pulse: data.pulse, outlook: data.outlook, summary: data.summary });
  });

  router.get('/ticker', async (_req, res) => {
    const data = await getAgiIntelligence(env);
    return sendJson(res, {
      items: data.insightStrip || [],
      source: data.source || 'agi-intelligence',
      disclaimer: data.disclaimer,
      updatedAt: data.updatedAt,
      stale: data.stale || false,
    });
  });

  return router;
}
