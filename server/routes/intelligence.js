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

  router.post('/research/runs', async (req, res) => {
    try {
      const result = await engineFetch('/v1/research/runs', { method: 'POST', body: req.body || {} });
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Intelligence engine unavailable', detail: error.message });
    }
  });

  router.get('/research/runs', async (req, res) => {
    try {
      const qs = new URLSearchParams(req.query).toString();
      const result = await engineFetch(`/v1/research/runs${qs ? `?${qs}` : ''}`);
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Intelligence engine unavailable', detail: error.message });
    }
  });

  router.get('/research/runs/:runId', async (req, res) => {
    try {
      const result = await engineFetch(`/v1/research/runs/${encodeURIComponent(req.params.runId)}`);
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Intelligence engine unavailable', detail: error.message });
    }
  });

  // CMS → KIP: ingest AGI research (public or private) into institutional memory.
  router.post('/kip/ingest/agi', async (req, res) => {
    try {
      const body = req.body || {};
      const title = String(body.title || '').trim();
      const content = String(body.content || body.content_md || '').trim();
      if (!title || !content) {
        return res.status(400).json({ error: 'title and content are required' });
      }

      const payload = {
        title,
        content,
        author: body.author || 'AGI Research Desk',
        source: 'agi',
        document_type: body.document_type || 'agi_research',
        language: 'en',
        tickers: Array.isArray(body.tickers) ? body.tickers : [],
        themes: Array.isArray(body.themes) ? body.themes : [],
        sectors: Array.isArray(body.sectors) ? body.sectors : [],
        article_id: body.article_id || body.slug || null,
        research_type: body.research_type || body.section || '',
        metadata: {
          cms_status: body.cms_status || body.status || null,
          slug: body.slug || null,
          section: body.section || null,
          destination: body.destination || 'intelligence',
          ...(body.metadata && typeof body.metadata === 'object' ? body.metadata : {}),
        },
      };

      const result = await engineFetch('/v1/kip/ingest/agi', { method: 'POST', body: payload });
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({
        error: 'Intelligence ingest unavailable',
        detail: error.message,
        hint: 'Ensure agib-intelligence-engine is live and INTELLIGENCE_ENGINE_URL/TOKEN are set on the API.',
      });
    }
  });

  router.get('/kip/health', async (_req, res) => {
    try {
      const result = await engineFetch('/v1/kip/health');
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'KIP unavailable', detail: error.message });
    }
  });

  // KF1 Knowledge Foundation — structured knowledge objects over KIP.
  const kfGet = (enginePath) => async (req, res) => {
    try {
      const qs = new URLSearchParams(req.query).toString();
      const suffix = qs ? `?${qs}` : '';
      const result = await engineFetch(`${enginePath}${suffix}`);
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Knowledge Foundation unavailable', detail: error.message });
    }
  };

  const kfPost = (enginePath) => async (_req, res) => {
    try {
      const result = await engineFetch(enginePath, { method: 'POST', body: {} });
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Knowledge Foundation unavailable', detail: error.message });
    }
  };

  router.get('/kf/health', kfGet('/v1/kf/health'));
  router.get('/kf/coverage', kfGet('/v1/kf/coverage'));
  router.post('/kf/seed', kfPost('/v1/kf/seed'));
  router.post('/kf/rebuild', kfPost('/v1/kf/rebuild'));
  router.get('/kf/search', kfGet('/v1/kf/search'));
  router.get('/kf/companies', kfGet('/v1/kf/companies'));
  router.get('/kf/company/:ticker', async (req, res) => {
    try {
      const result = await engineFetch(`/v1/kf/company/${encodeURIComponent(req.params.ticker)}`);
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Knowledge Foundation unavailable', detail: error.message });
    }
  });
  router.get('/kf/sectors', kfGet('/v1/kf/sectors'));
  router.get('/kf/sector/:sectorId', async (req, res) => {
    try {
      const result = await engineFetch(`/v1/kf/sector/${encodeURIComponent(req.params.sectorId)}`);
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Knowledge Foundation unavailable', detail: error.message });
    }
  });
  router.get('/kf/themes', kfGet('/v1/kf/themes'));
  router.get('/kf/theme/:themeId', async (req, res) => {
    try {
      const result = await engineFetch(`/v1/kf/theme/${encodeURIComponent(req.params.themeId)}`);
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Knowledge Foundation unavailable', detail: error.message });
    }
  });
  router.get('/kf/macros', kfGet('/v1/kf/macros'));
  router.get('/kf/macro/:macroId', async (req, res) => {
    try {
      const result = await engineFetch(`/v1/kf/macro/${encodeURIComponent(req.params.macroId)}`);
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Knowledge Foundation unavailable', detail: error.message });
    }
  });
  router.get('/kf/predictions', kfGet('/v1/kf/predictions'));
  router.get('/kf/extracts', kfGet('/v1/kf/extracts'));

  // KCV1 Knowledge Corpus — populate/improve KF; no redesign.
  router.get('/kc/health', kfGet('/v1/kc/health'));
  router.get('/kc/metrics', kfGet('/v1/kc/metrics'));
  router.get('/kc/dashboard', kfGet('/v1/kc/dashboard'));
  router.post('/kc/populate', async (req, res) => {
    try {
      const qs = new URLSearchParams(req.query).toString();
      const result = await engineFetch(`/v1/kc/populate${qs ? `?${qs}` : ''}`, {
        method: 'POST',
        body: {},
      });
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Knowledge Corpus unavailable', detail: error.message });
    }
  });
  router.post('/kc/universe', kfPost('/v1/kc/universe'));
  router.get('/kc/gaps', kfGet('/v1/kc/gaps'));
  router.get('/kc/learning', kfGet('/v1/kc/learning'));
  router.get('/kc/quality', kfGet('/v1/kc/quality'));
  router.get('/kc/consult', kfGet('/v1/kc/consult'));

  return router;
}
