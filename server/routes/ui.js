/**
 * UI Aggregation proxy — frontend talks to /api/ui/*, never to engines directly.
 * Backs onto intelligence-engine /v1/ui/*.
 */

import { Router } from 'express';

function engineConfig() {
  let baseUrl = (process.env.INTELLIGENCE_ENGINE_URL || 'http://127.0.0.1:8100').replace(/\/$/, '');
  if (baseUrl && !/^https?:\/\//i.test(baseUrl)) {
    baseUrl = `https://${baseUrl}`;
  }
  const token = (process.env.INTELLIGENCE_ENGINE_TOKEN || 'dev-intelligence-token').trim();
  return { baseUrl, token };
}

async function engineFetch(path, { method = 'GET', body = null } = {}) {
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
    signal: AbortSignal.timeout(120_000),
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

  const getPaths = [
    '/home',
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
    '/copilot',
    '/autocomplete',
  ];

  for (const p of getPaths) {
    router.get(p, async (req, res) => {
      try {
        let path = `/v1/ui${req.path}`;
        // Express strips mount; req.path is relative to router
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
