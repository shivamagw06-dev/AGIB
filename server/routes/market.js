/**
 * AGI Market Intelligence API routes
 * Public endpoints return derived analytics only — no raw exchange quotes.
 */

import { Router } from 'express';
import { getAgiIntelligence, getDashboardFromIntelligence } from '../services/intelligenceService.js';

export default function createMarketRouter(env = {}) {
  const router = Router();

  /** Primary endpoint — full AGI intelligence bundle */
  router.get('/intelligence', async (_req, res) => {
    try {
      const data = await getAgiIntelligence(env);
      return res.json(data);
    } catch (err) {
      console.error('[market/intelligence]', err?.message);
      return res.status(502).json({ error: 'Intelligence engine failed' });
    }
  });

  /** Legacy routes — now serve derived data only */
  router.get('/dashboard', async (_req, res) => {
    try {
      const data = await getDashboardFromIntelligence(env);
      return res.json(data);
    } catch (err) {
      console.error('[market/dashboard]', err?.message);
      return res.status(502).json({ error: 'Dashboard fetch failed' });
    }
  });

  router.get('/pulse', async (_req, res) => {
    try {
      const data = await getAgiIntelligence(env);
      return res.json({ pulse: data.pulse, outlook: data.outlook, summary: data.summary });
    } catch (err) {
      console.error('[market/pulse]', err?.message);
      return res.status(502).json({ error: 'Pulse fetch failed' });
    }
  });

  /** Deprecated — returns insight strip instead of raw ticker */
  router.get('/ticker', async (_req, res) => {
    try {
      const data = await getAgiIntelligence(env);
      return res.json({
        items: data.insightStrip,
        source: 'agi-intelligence',
        disclaimer: data.disclaimer,
        updatedAt: data.updatedAt,
      });
    } catch (err) {
      console.error('[market/ticker]', err?.message);
      return res.status(502).json({ error: 'Insight strip failed', items: [] });
    }
  });

  return router;
}
