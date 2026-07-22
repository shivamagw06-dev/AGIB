/**
 * AGI Market Intelligence API routes
 * GET /api/market/ticker  — Bloomberg-style ticker strip
 * GET /api/market/pulse   — AGI Market Pulse + outlook
 * GET /api/market/dashboard — Today's dashboard bundle
 */

import { Router } from 'express';
import { getTickerData, getDashboardData } from '../services/marketDataService.js';

export default function createMarketRouter(env = {}) {
  const router = Router();

  router.get('/ticker', async (_req, res) => {
    try {
      const data = await getTickerData(env);
      return res.json(data);
    } catch (err) {
      console.error('[market/ticker]', err?.message);
      return res.status(502).json({ error: 'Ticker fetch failed', items: [] });
    }
  });

  router.get('/pulse', async (_req, res) => {
    try {
      const data = await getDashboardData(env);
      return res.json({ pulse: data.pulse, outlook: data.outlook });
    } catch (err) {
      console.error('[market/pulse]', err?.message);
      return res.status(502).json({ error: 'Pulse fetch failed' });
    }
  });

  router.get('/dashboard', async (_req, res) => {
    try {
      const data = await getDashboardData(env);
      return res.json(data);
    } catch (err) {
      console.error('[market/dashboard]', err?.message);
      return res.status(502).json({ error: 'Dashboard fetch failed' });
    }
  });

  return router;
}
