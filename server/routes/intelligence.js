/**
 * AGI Intelligence Engine proxy — frontend never talks to Python directly.
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

function proxyPost(path) {
  return async (req, res) => {
    try {
      const result = await engineFetch(path, { method: 'POST', body: req.body || {} });
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Intelligence engine unavailable', detail: error.message });
    }
  };
}

function proxyGet(pathBuilder) {
  return async (req, res) => {
    try {
      const path = typeof pathBuilder === 'function' ? pathBuilder(req) : pathBuilder;
      const result = await engineFetch(path);
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Intelligence engine unavailable', detail: error.message });
    }
  };
}

export default function createIntelligenceRouter() {
  const router = Router();

  router.get('/health', async (_req, res) => {
    try {
      const result = await engineFetch('/v1/health');
      return res.status(result.ok ? 200 : 503).json({
        gateway: 'agi-node',
        engine: result.data,
        engineStatus: result.status,
      });
    } catch (error) {
      return res.status(503).json({
        gateway: 'agi-node',
        ok: false,
        error: error.message,
        hint: 'Start intelligence-engine on INTELLIGENCE_ENGINE_URL (default http://127.0.0.1:8100)',
      });
    }
  });

  router.post('/research/runs', proxyPost('/v1/research/runs'));
  router.get('/research/runs', async (req, res) => {
    try {
      const qs = new URLSearchParams(req.query).toString();
      const result = await engineFetch(`/v1/research/runs${qs ? `?${qs}` : ''}`);
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Intelligence engine unavailable', detail: error.message });
    }
  });
  router.get(
    '/research/runs/:runId',
    proxyGet((req) => `/v1/research/runs/${encodeURIComponent(req.params.runId)}`),
  );

  // Portfolio Office
  router.get('/portfolio/models', proxyGet('/v1/portfolio/models'));
  router.post('/portfolio/normalize', proxyPost('/v1/portfolio/normalize'));
  router.post('/portfolio/ingest', proxyPost('/v1/portfolio/ingest'));
  router.post('/portfolio/scenario', proxyPost('/v1/portfolio/scenario'));
  router.post('/portfolio/office', proxyPost('/v1/portfolio/office'));

  return router;
}
