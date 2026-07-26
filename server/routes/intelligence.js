/**
 * AGI Intelligence Engine proxy — frontend never talks to Python directly.
 */

import { Router } from 'express';
import {
  buildRecentLearningSummary,
  cmsLearningStatus,
  learnCmsArticles,
  startCmsArticleLearningScheduler,
} from '../services/cmsArticleLearning.js';

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

  // Soft daily CMS → KIP/KF/KC learner (IST learning_date calendar)
  startCmsArticleLearningScheduler(engineFetch);

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

  // CMS bulk learn — read uploaded articles into KIP and stamp learning dates (daily).
  router.post('/cms/learn-articles', async (req, res) => {
    try {
      const body = req.body || {};
      const result = await learnCmsArticles({
        engineFetch,
        limit: body.limit,
        onlyUnlearned: Boolean(body.only_unlearned ?? body.onlyUnlearned),
        sinceDate: body.since_date || body.sinceDate || null,
        mode: body.mode || null,
        compound: body.compound !== false,
      });
      const status = result?.ok ? 200 : result?.skipped ? 503 : 500;
      return res.status(status).json(result);
    } catch (error) {
      return res.status(503).json({
        error: 'CMS article learning unavailable',
        detail: error.message,
      });
    }
  });

  router.get('/cms/learning-status', async (req, res) => {
    try {
      const days = req.query.days ? Number(req.query.days) : 14;
      const result = await cmsLearningStatus({ days });
      const status = result?.ok ? 200 : result?.skipped ? 503 : 500;
      return res.status(status).json(result);
    } catch (error) {
      return res.status(503).json({
        error: 'CMS learning status unavailable',
        detail: error.message,
      });
    }
  });

  router.get('/cms/learning-summary', async (req, res) => {
    try {
      const days = req.query.days ? Number(req.query.days) : 5;
      const result = await buildRecentLearningSummary({ engineFetch, days });
      return res.status(result?.ok ? 200 : 503).json(result);
    } catch (error) {
      return res.status(503).json({
        error: 'CMS learning summary unavailable',
        detail: error.message,
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

  // AOI v1 — Open Intelligence acquisition platform (no core redesign).
  router.get('/aoi/health', kfGet('/v1/aoi/health'));
  router.get('/aoi/dashboard', kfGet('/v1/aoi/dashboard'));
  router.post('/aoi/registry/seed', kfPost('/v1/aoi/registry/seed'));
  router.post('/aoi/run', async (req, res) => {
    try {
      const qs = new URLSearchParams(req.query).toString();
      const result = await engineFetch(`/v1/aoi/run${qs ? `?${qs}` : ''}`, {
        method: 'POST',
        body: {},
      });
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Open Intelligence unavailable', detail: error.message });
    }
  });
  router.get('/aoi/companies', kfGet('/v1/aoi/companies'));
  router.get('/aoi/company/:key', async (req, res) => {
    try {
      const result = await engineFetch(`/v1/aoi/company/${encodeURIComponent(req.params.key)}`);
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Open Intelligence unavailable', detail: error.message });
    }
  });
  router.get('/aoi/search', kfGet('/v1/aoi/search'));
  router.get('/aoi/consult', kfGet('/v1/aoi/consult'));
  router.get('/aoi/connectors', kfGet('/v1/aoi/connectors'));
  router.get('/aoi/scheduler', kfGet('/v1/aoi/scheduler'));
  router.get('/aoi/gaps', kfGet('/v1/aoi/gaps'));
  router.get('/aoi/learning', kfGet('/v1/aoi/learning'));

  // EVE v1 — Evidence & Verification Engine (between AOI and KCV/KF).
  router.get('/eve/health', kfGet('/v1/eve/health'));
  router.get('/eve/dashboard', kfGet('/v1/eve/dashboard'));
  router.get('/eve/evidence', kfGet('/v1/eve/evidence'));
  router.get('/eve/evidence/:evidenceId', async (req, res) => {
    try {
      const result = await engineFetch(`/v1/eve/evidence/${encodeURIComponent(req.params.evidenceId)}`);
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Evidence engine unavailable', detail: error.message });
    }
  });
  router.get('/eve/company/:key', async (req, res) => {
    try {
      const result = await engineFetch(`/v1/eve/company/${encodeURIComponent(req.params.key)}`);
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Evidence engine unavailable', detail: error.message });
    }
  });
  router.get('/eve/conflicts', kfGet('/v1/eve/conflicts'));
  router.get('/eve/timeline', kfGet('/v1/eve/timeline'));
  router.get('/eve/trust', kfGet('/v1/eve/trust'));
  router.get('/eve/source', kfGet('/v1/eve/source'));
  router.get('/eve/verification', kfGet('/v1/eve/verification'));
  router.post('/eve/verification/run', kfPost('/v1/eve/verification/run'));
  router.get('/eve/search', kfGet('/v1/eve/search'));
  router.get('/eve/consult', kfGet('/v1/eve/consult'));
  router.get('/eve/audit', kfGet('/v1/eve/audit'));

  // IIE v1 — Investment Intelligence Engine (after EVE/KCV/KF, before reasoning).
  router.get('/iie/health', kfGet('/v1/iie/health'));
  router.get('/iie/dashboard', kfGet('/v1/iie/dashboard'));
  router.post('/iie/analyse', async (req, res) => {
    try {
      const qs = new URLSearchParams(req.query).toString();
      const result = await engineFetch(`/v1/iie/analyse${qs ? `?${qs}` : ''}`, { method: 'POST', body: {} });
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Investment intelligence unavailable', detail: error.message });
    }
  });
  router.post('/iie/batch', async (req, res) => {
    try {
      const qs = new URLSearchParams(req.query).toString();
      const result = await engineFetch(`/v1/iie/batch${qs ? `?${qs}` : ''}`, { method: 'POST', body: {} });
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Investment intelligence unavailable', detail: error.message });
    }
  });
  router.get('/iie/company/:key', async (req, res) => {
    try {
      const result = await engineFetch(`/v1/iie/company/${encodeURIComponent(req.params.key)}`);
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Investment intelligence unavailable', detail: error.message });
    }
  });
  router.get('/iie/sector', kfGet('/v1/iie/sector'));
  router.get('/iie/sector/:sectorId', async (req, res) => {
    try {
      const result = await engineFetch(`/v1/iie/sector/${encodeURIComponent(req.params.sectorId)}`);
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Investment intelligence unavailable', detail: error.message });
    }
  });
  router.get('/iie/theme', kfGet('/v1/iie/theme'));
  router.get('/iie/theme/:themeId', async (req, res) => {
    try {
      const result = await engineFetch(`/v1/iie/theme/${encodeURIComponent(req.params.themeId)}`);
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Investment intelligence unavailable', detail: error.message });
    }
  });
  router.get('/iie/thesis/:key', async (req, res) => {
    try {
      const result = await engineFetch(`/v1/iie/thesis/${encodeURIComponent(req.params.key)}`);
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Investment intelligence unavailable', detail: error.message });
    }
  });
  router.get('/iie/scenario/:key', async (req, res) => {
    try {
      const result = await engineFetch(`/v1/iie/scenario/${encodeURIComponent(req.params.key)}`);
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Investment intelligence unavailable', detail: error.message });
    }
  });
  router.get('/iie/catalysts', kfGet('/v1/iie/catalysts'));
  router.get('/iie/risks', kfGet('/v1/iie/risks'));
  router.get('/iie/opportunities', kfGet('/v1/iie/opportunities'));
  router.get('/iie/compare', kfGet('/v1/iie/compare'));
  router.get('/iie/monitor/:key', async (req, res) => {
    try {
      const result = await engineFetch(`/v1/iie/monitor/${encodeURIComponent(req.params.key)}`);
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Investment intelligence unavailable', detail: error.message });
    }
  });
  router.get('/iie/dna/:key', async (req, res) => {
    try {
      const result = await engineFetch(`/v1/iie/dna/${encodeURIComponent(req.params.key)}`);
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Investment intelligence unavailable', detail: error.message });
    }
  });
  router.get('/iie/macro', kfGet('/v1/iie/macro'));
  router.get('/iie/evolution', kfGet('/v1/iie/evolution'));
  router.get('/iie/search', kfGet('/v1/iie/search'));
  router.get('/iie/consult', kfGet('/v1/iie/consult'));

  // FLE v1 — Forecasting & Learning Engine (after IIE, before reasoning).
  router.get('/fle/health', kfGet('/v1/fle/health'));
  router.get('/fle/dashboard', kfGet('/v1/fle/dashboard'));
  router.get('/fle/forecast', kfGet('/v1/fle/forecast'));
  router.post('/fle/forecast', async (req, res) => {
    try {
      const result = await engineFetch('/v1/fle/forecast', { method: 'POST', body: req.body || {} });
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Forecasting engine unavailable', detail: error.message });
    }
  });
  router.get('/fle/forecast/:forecastId', async (req, res) => {
    try {
      const result = await engineFetch(`/v1/fle/forecast/${encodeURIComponent(req.params.forecastId)}`);
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Forecasting engine unavailable', detail: error.message });
    }
  });
  router.post('/fle/forecast/:forecastId/resolve', async (req, res) => {
    try {
      const result = await engineFetch(
        `/v1/fle/forecast/${encodeURIComponent(req.params.forecastId)}/resolve`,
        { method: 'POST', body: req.body || {} }
      );
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Forecasting engine unavailable', detail: error.message });
    }
  });
  router.post('/fle/forecast/:forecastId/version', async (req, res) => {
    try {
      const result = await engineFetch(
        `/v1/fle/forecast/${encodeURIComponent(req.params.forecastId)}/version`,
        { method: 'POST', body: req.body || {} }
      );
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Forecasting engine unavailable', detail: error.message });
    }
  });
  router.get('/fle/compare/:forecastId', async (req, res) => {
    try {
      const result = await engineFetch(`/v1/fle/compare/${encodeURIComponent(req.params.forecastId)}`);
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Forecasting engine unavailable', detail: error.message });
    }
  });
  router.get('/fle/company/:key', async (req, res) => {
    try {
      const result = await engineFetch(`/v1/fle/company/${encodeURIComponent(req.params.key)}`);
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Forecasting engine unavailable', detail: error.message });
    }
  });
  router.get('/fle/outcomes', kfGet('/v1/fle/outcomes'));
  router.get('/fle/learning', kfGet('/v1/fle/learning'));
  router.get('/fle/calibration', kfGet('/v1/fle/calibration'));
  router.get('/fle/scenarios/:forecastId', async (req, res) => {
    try {
      const result = await engineFetch(`/v1/fle/scenarios/${encodeURIComponent(req.params.forecastId)}`);
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Forecasting engine unavailable', detail: error.message });
    }
  });
  router.get('/fle/accuracy', kfGet('/v1/fle/accuracy'));
  router.get('/fle/history', kfGet('/v1/fle/history'));
  router.post('/fle/generate', async (req, res) => {
    try {
      const qs = new URLSearchParams(req.query).toString();
      const result = await engineFetch(`/v1/fle/generate${qs ? `?${qs}` : ''}`, { method: 'POST', body: {} });
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Forecasting engine unavailable', detail: error.message });
    }
  });
  router.post('/fle/batch', async (req, res) => {
    try {
      const qs = new URLSearchParams(req.query).toString();
      const result = await engineFetch(`/v1/fle/batch${qs ? `?${qs}` : ''}`, { method: 'POST', body: {} });
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Forecasting engine unavailable', detail: error.message });
    }
  });
  router.post('/fle/jobs', async (_req, res) => {
    try {
      const result = await engineFetch('/v1/fle/jobs', { method: 'POST', body: {} });
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Forecasting engine unavailable', detail: error.message });
    }
  });
  router.get('/fle/search', kfGet('/v1/fle/search'));
  router.get('/fle/consult', kfGet('/v1/fle/consult'));

  // MEE v1 — Market Event Engine (after FLE; event backbone).
  router.get('/mee/health', kfGet('/v1/mee/health'));
  router.get('/mee/dashboard', kfGet('/v1/mee/dashboard'));
  router.get('/mee/events', kfGet('/v1/mee/events'));
  router.post('/mee/events', async (req, res) => {
    try {
      const result = await engineFetch('/v1/mee/events', { method: 'POST', body: req.body || {} });
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Market event engine unavailable', detail: error.message });
    }
  });
  router.get('/mee/events/:eventId', async (req, res) => {
    try {
      const result = await engineFetch(`/v1/mee/events/${encodeURIComponent(req.params.eventId)}`);
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Market event engine unavailable', detail: error.message });
    }
  });
  router.post('/mee/events/:eventId/verify', async (req, res) => {
    try {
      const result = await engineFetch(
        `/v1/mee/events/${encodeURIComponent(req.params.eventId)}/verify`,
        { method: 'POST', body: {} }
      );
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Market event engine unavailable', detail: error.message });
    }
  });
  router.post('/mee/events/:eventId/version', async (req, res) => {
    try {
      const result = await engineFetch(
        `/v1/mee/events/${encodeURIComponent(req.params.eventId)}/version`,
        { method: 'POST', body: req.body || {} }
      );
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Market event engine unavailable', detail: error.message });
    }
  });
  router.get('/mee/company/:key', async (req, res) => {
    try {
      const result = await engineFetch(`/v1/mee/company/${encodeURIComponent(req.params.key)}`);
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Market event engine unavailable', detail: error.message });
    }
  });
  router.get('/mee/sector/:sectorId', async (req, res) => {
    try {
      const result = await engineFetch(`/v1/mee/sector/${encodeURIComponent(req.params.sectorId)}`);
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Market event engine unavailable', detail: error.message });
    }
  });
  router.get('/mee/theme/:themeId', async (req, res) => {
    try {
      const result = await engineFetch(`/v1/mee/theme/${encodeURIComponent(req.params.themeId)}`);
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Market event engine unavailable', detail: error.message });
    }
  });
  router.get('/mee/timeline', kfGet('/v1/mee/timeline'));
  router.get('/mee/impact/:eventId', async (req, res) => {
    try {
      const result = await engineFetch(`/v1/mee/impact/${encodeURIComponent(req.params.eventId)}`);
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Market event engine unavailable', detail: error.message });
    }
  });
  router.get('/mee/relationships', kfGet('/v1/mee/relationships'));
  router.get('/mee/history', kfGet('/v1/mee/history'));
  router.get('/mee/similar/:eventId', async (req, res) => {
    try {
      const qs = new URLSearchParams(req.query).toString();
      const result = await engineFetch(
        `/v1/mee/similar/${encodeURIComponent(req.params.eventId)}${qs ? `?${qs}` : ''}`
      );
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Market event engine unavailable', detail: error.message });
    }
  });
  router.post('/mee/cycle', async (req, res) => {
    try {
      const qs = new URLSearchParams(req.query).toString();
      const result = await engineFetch(`/v1/mee/cycle${qs ? `?${qs}` : ''}`, { method: 'POST', body: {} });
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Market event engine unavailable', detail: error.message });
    }
  });
  router.get('/mee/search', kfGet('/v1/mee/search'));
  router.get('/mee/consult', kfGet('/v1/mee/consult'));

  // CAE v1 — Context Assembly Engine (Ask AGI orchestration gateway).
  router.get('/cae/health', kfGet('/v1/cae/health'));
  router.get('/cae/dashboard', kfGet('/v1/cae/dashboard'));
  router.get('/cae/context', kfGet('/v1/cae/context'));
  router.get('/cae/query-plan', kfGet('/v1/cae/query-plan'));
  router.get('/cae/retrieval', kfGet('/v1/cae/retrieval'));
  router.get('/cae/cache', kfGet('/v1/cae/cache'));
  router.post('/cae/cache/clear', async (_req, res) => {
    try {
      const result = await engineFetch('/v1/cae/cache/clear', { method: 'POST', body: {} });
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Context assembly unavailable', detail: error.message });
    }
  });
  router.get('/cae/metrics', kfGet('/v1/cae/metrics'));
  router.get('/cae/explain/:packageId', async (req, res) => {
    try {
      const result = await engineFetch(`/v1/cae/explain/${encodeURIComponent(req.params.packageId)}`);
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Context assembly unavailable', detail: error.message });
    }
  });
  router.get('/cae/package/:packageId', async (req, res) => {
    try {
      const result = await engineFetch(`/v1/cae/package/${encodeURIComponent(req.params.packageId)}`);
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Context assembly unavailable', detail: error.message });
    }
  });
  router.get('/cae/search', kfGet('/v1/cae/search'));

  // IB v1 — AGI Intelligence Bus (event-driven backbone).
  router.get('/ib/health', kfGet('/v1/ib/health'));
  router.get('/ib/dashboard', kfGet('/v1/ib/dashboard'));
  router.get('/ib/events', kfGet('/v1/ib/events'));
  router.post('/ib/publish', async (req, res) => {
    try {
      const result = await engineFetch('/v1/ib/publish', { method: 'POST', body: req.body || {} });
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Intelligence bus unavailable', detail: error.message });
    }
  });
  router.get('/ib/subscriptions', kfGet('/v1/ib/subscriptions'));
  router.post('/ib/subscriptions', async (req, res) => {
    try {
      const result = await engineFetch('/v1/ib/subscriptions', { method: 'POST', body: req.body || {} });
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Intelligence bus unavailable', detail: error.message });
    }
  });
  router.post('/ib/replay', async (req, res) => {
    try {
      const result = await engineFetch('/v1/ib/replay', { method: 'POST', body: req.body || {} });
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Intelligence bus unavailable', detail: error.message });
    }
  });
  router.get('/ib/history', kfGet('/v1/ib/history'));
  router.get('/ib/metrics', kfGet('/v1/ib/metrics'));
  router.get('/ib/traces', kfGet('/v1/ib/traces'));
  router.get('/ib/dead-letter', kfGet('/v1/ib/dead-letter'));
  router.post('/ib/dead-letter/:dlqId/resolve', async (req, res) => {
    try {
      const result = await engineFetch(
        `/v1/ib/dead-letter/${encodeURIComponent(req.params.dlqId)}/resolve`,
        { method: 'POST', body: {} }
      );
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Intelligence bus unavailable', detail: error.message });
    }
  });
  router.get('/ib/schema', kfGet('/v1/ib/schema'));
  router.post('/ib/demo-chain', async (req, res) => {
    try {
      const qs = new URLSearchParams(req.query || {}).toString();
      const result = await engineFetch(`/v1/ib/demo-chain${qs ? `?${qs}` : ''}`, {
        method: 'POST',
        body: {},
      });
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Intelligence bus unavailable', detail: error.message });
    }
  });

  // VE v1 — Valuation Engine (intrinsic value platform).
  router.get('/ve/health', kfGet('/v1/ve/health'));
  router.get('/ve/dashboard', kfGet('/v1/ve/dashboard'));
  router.get('/ve/company/:key', async (req, res) => {
    try {
      const qs = new URLSearchParams(req.query || {}).toString();
      const result = await engineFetch(
        `/v1/ve/company/${encodeURIComponent(req.params.key)}${qs ? `?${qs}` : ''}`
      );
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Valuation engine unavailable', detail: error.message });
    }
  });
  router.get('/ve/model', kfGet('/v1/ve/model'));
  router.get('/ve/history', kfGet('/v1/ve/history'));
  router.get('/ve/scenarios', kfGet('/v1/ve/scenarios'));
  router.get('/ve/compare', kfGet('/v1/ve/compare'));
  router.get('/ve/sensitivity', kfGet('/v1/ve/sensitivity'));
  router.get('/ve/search', kfGet('/v1/ve/search'));
  router.get('/ve/consult', kfGet('/v1/ve/consult'));
  router.post('/ve/value', async (req, res) => {
    try {
      const result = await engineFetch('/v1/ve/value', { method: 'POST', body: req.body || {} });
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Valuation engine unavailable', detail: error.message });
    }
  });
  router.get('/ve/valuation/:valuationId', async (req, res) => {
    try {
      const result = await engineFetch(
        `/v1/ve/valuation/${encodeURIComponent(req.params.valuationId)}`
      );
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Valuation engine unavailable', detail: error.message });
    }
  });

  // FIML v1 — Financial Intelligence Model Library (not an engine).
  router.get('/fiml/health', kfGet('/v1/fiml/health'));
  router.get('/fiml/dashboard', kfGet('/v1/fiml/dashboard'));
  router.get('/fiml/models', kfGet('/v1/fiml/models'));
  router.get('/fiml/industries', kfGet('/v1/fiml/industries'));
  router.get('/fiml/search', kfGet('/v1/fiml/search'));
  router.get('/fiml/metrics', kfGet('/v1/fiml/metrics'));
  router.get('/fiml/graph', kfGet('/v1/fiml/graph'));
  router.post('/fiml/analyse/:domain', async (req, res) => {
    try {
      const result = await engineFetch(`/v1/fiml/analyse/${encodeURIComponent(req.params.domain)}`, {
        method: 'POST',
        body: req.body || {},
      });
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'FIML unavailable', detail: error.message });
    }
  });
  router.post('/fiml/score/:domain', async (req, res) => {
    try {
      const result = await engineFetch(`/v1/fiml/score/${encodeURIComponent(req.params.domain)}`, {
        method: 'POST',
        body: req.body || {},
      });
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'FIML unavailable', detail: error.message });
    }
  });
  router.post('/fiml/explain/:domain', async (req, res) => {
    try {
      const result = await engineFetch(`/v1/fiml/explain/${encodeURIComponent(req.params.domain)}`, {
        method: 'POST',
        body: req.body || {},
      });
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'FIML unavailable', detail: error.message });
    }
  });
  router.post('/fiml/compare/:domain', async (req, res) => {
    try {
      const result = await engineFetch(`/v1/fiml/compare/${encodeURIComponent(req.params.domain)}`, {
        method: 'POST',
        body: req.body || {},
      });
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'FIML unavailable', detail: error.message });
    }
  });
  router.post('/fiml/bundle', async (req, res) => {
    try {
      const result = await engineFetch('/v1/fiml/bundle', { method: 'POST', body: req.body || {} });
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'FIML unavailable', detail: error.message });
    }
  });
  router.post('/fiml/consumer/:engine', async (req, res) => {
    try {
      const result = await engineFetch(`/v1/fiml/consumer/${encodeURIComponent(req.params.engine)}`, {
        method: 'POST',
        body: req.body || {},
      });
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'FIML unavailable', detail: error.message });
    }
  });

  // AGI Finance Academy v1.1 — multi-course curriculum library (not an engine).
  router.get('/academy/health', kfGet('/v1/academy/health'));
  router.get('/academy/dashboard', kfGet('/v1/academy/dashboard'));
  router.get('/academy/courses', kfGet('/v1/academy/courses'));
  router.get('/academy/course', kfGet('/v1/academy/course'));
  router.get('/academy/concepts', kfGet('/v1/academy/concepts'));
  router.get('/academy/concepts/:conceptId', async (req, res) => {
    try {
      const result = await engineFetch(`/v1/academy/concepts/${encodeURIComponent(req.params.conceptId)}`);
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Finance Academy unavailable', detail: error.message });
    }
  });
  router.get('/academy/teach/:conceptId', async (req, res) => {
    try {
      const result = await engineFetch(`/v1/academy/teach/${encodeURIComponent(req.params.conceptId)}`);
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Finance Academy unavailable', detail: error.message });
    }
  });
  router.get('/academy/graph', kfGet('/v1/academy/graph'));
  router.get('/academy/neighborhood/:conceptId', async (req, res) => {
    try {
      const result = await engineFetch(`/v1/academy/neighborhood/${encodeURIComponent(req.params.conceptId)}`);
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Finance Academy unavailable', detail: error.message });
    }
  });
  router.get('/academy/causal-models', kfGet('/v1/academy/causal-models'));
  router.get('/academy/mental-models', kfGet('/v1/academy/mental-models'));
  router.get('/academy/quality', kfGet('/v1/academy/quality'));
  router.get('/academy/provenance', kfGet('/v1/academy/provenance'));
  router.get('/academy/exams', kfGet('/v1/academy/exams'));
  router.get('/academy/exams/:questionId', async (req, res) => {
    try {
      const result = await engineFetch(`/v1/academy/exams/${encodeURIComponent(req.params.questionId)}`);
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Finance Academy unavailable', detail: error.message });
    }
  });
  router.get('/academy/search', kfGet('/v1/academy/search'));
  router.get('/academy/red-flags', kfGet('/v1/academy/red-flags'));
  router.get('/academy/accounting', kfGet('/v1/academy/accounting'));
  router.get('/academy/corporate-finance', kfGet('/v1/academy/corporate-finance'));
  router.get('/academy/completion', kfGet('/v1/academy/completion'));
  router.get('/academy/metrics', kfGet('/v1/academy/metrics'));
  router.get('/academy/production', kfGet('/v1/academy/production'));
  router.get('/academy/production/ab', kfGet('/v1/academy/production/ab'));
  router.get('/academy/production/quality-gates', kfGet('/v1/academy/production/quality-gates'));
  router.post('/academy/production/package', async (req, res) => {
    try {
      const qs = new URLSearchParams();
      if (req.query.query) qs.set('query', String(req.query.query));
      if (req.query.engine) qs.set('engine', String(req.query.engine));
      if (req.query.ticker) qs.set('ticker', String(req.query.ticker));
      if (req.body?.query) qs.set('query', String(req.body.query));
      if (req.body?.engine) qs.set('engine', String(req.body.engine));
      if (req.body?.ticker) qs.set('ticker', String(req.body.ticker));
      const result = await engineFetch(`/v1/academy/production/package?${qs.toString()}`, {
        method: 'POST',
        body: req.body || {},
      });
      res.json(result);
    } catch (err) {
      res.status(502).json({ error: err?.message || 'Academy production package failed' });
    }
  });
  // AGI Academy Books V1 — structured institutional learning (not searchable PDFs)
  router.get('/academy/books/health', kfGet('/v1/academy/books/health'));
  router.get('/academy/books/dashboard', kfGet('/v1/academy/books/dashboard'));
  router.get('/academy/books/quality-gates', kfGet('/v1/academy/books/quality-gates'));
  router.get('/academy/books/graph', kfGet('/v1/academy/books/graph'));
  router.post('/academy/books/ingest', async (req, res) => {
    try {
      const result = await engineFetch('/v1/academy/books/ingest', {
        method: 'POST',
        body: req.body || {},
      });
      res.json(result);
    } catch (err) {
      res.status(502).json({ error: err?.message || 'Academy books ingest failed' });
    }
  });
  router.post('/academy/books/package', async (req, res) => {
    try {
      const qs = new URLSearchParams();
      const query = req.query.query || req.body?.query;
      const ticker = req.query.ticker || req.body?.ticker;
      if (query) qs.set('query', String(query));
      if (ticker) qs.set('ticker', String(ticker));
      const result = await engineFetch(`/v1/academy/books/package?${qs.toString()}`, {
        method: 'POST',
        body: {},
      });
      res.json(result);
    } catch (err) {
      res.status(502).json({ error: err?.message || 'Academy books package failed' });
    }
  });
  router.post('/academy/books/attach-kf', async (req, res) => {
    try {
      const result = await engineFetch('/v1/academy/books/attach-kf', { method: 'POST', body: {} });
      res.json(result);
    } catch (err) {
      res.status(502).json({ error: err?.message || 'Academy books KF attach failed' });
    }
  });
  router.get('/academy/books/library', kfGet('/v1/academy/books/library'));
  router.get('/academy/books/ingestion-report', kfGet('/v1/academy/books/ingestion-report'));
  router.post('/academy/books/ingest-library', async (req, res) => {
    try {
      const result = await engineFetch('/v1/academy/books/ingest-library', {
        method: 'POST',
        body: req.body || {},
      });
      res.json(result);
    } catch (err) {
      res.status(502).json({ error: err?.message || 'Academy library ingest failed' });
    }
  });
  // SIF v1.0 — Sector Intelligence Framework (additive; not an engine)
  router.get('/sif/health', kfGet('/v1/sif/health'));
  router.get('/sif/dashboard', kfGet('/v1/sif/dashboard'));
  router.get('/sif/frameworks', kfGet('/v1/sif/frameworks'));
  router.get('/sif/frameworks/:sectorId', async (req, res) => {
    try {
      const result = await engineFetch(`/v1/sif/frameworks/${encodeURIComponent(req.params.sectorId)}`);
      res.json(result);
    } catch (err) {
      res.status(502).json({ error: err?.message || 'SIF framework failed' });
    }
  });
  router.get('/sif/quality-gates', kfGet('/v1/sif/quality-gates'));
  router.post('/sif/analyse', async (req, res) => {
    try {
      const qs = new URLSearchParams();
      const query = req.query.query || req.body?.query;
      const ticker = req.query.ticker || req.body?.ticker;
      const engine = req.query.engine || req.body?.engine || 'ask_agi';
      if (query) qs.set('query', String(query));
      if (ticker) qs.set('ticker', String(ticker));
      if (engine) qs.set('engine', String(engine));
      const result = await engineFetch(`/v1/sif/analyse?${qs.toString()}`, {
        method: 'POST',
        body: req.body || {},
      });
      res.json(result);
    } catch (err) {
      res.status(502).json({ error: err?.message || 'SIF analyse failed' });
    }
  });
  router.post('/academy/red-flags/score', async (req, res) => {
    try {
      const result = await engineFetch('/v1/academy/red-flags/score', {
        method: 'POST',
        body: req.body || {},
      });
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Finance Academy unavailable', detail: error.message });
    }
  });
  router.post('/academy/earnings-quality', async (req, res) => {
    try {
      const result = await engineFetch('/v1/academy/earnings-quality', {
        method: 'POST',
        body: req.body || {},
      });
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Finance Academy unavailable', detail: error.message });
    }
  });
  router.post('/academy/consumer/:engine', async (req, res) => {
    try {
      const result = await engineFetch(`/v1/academy/consumer/${encodeURIComponent(req.params.engine)}`, {
        method: 'POST',
        body: req.body || {},
      });
      return res.status(result.status).json(result.data);
    } catch (error) {
      return res.status(503).json({ error: 'Finance Academy unavailable', detail: error.message });
    }
  });

  // Mission Control V1 — administrator operations centre (read-only)
  router.get('/mission-control/health', kfGet('/v1/mission-control/health'));
  router.get('/mission-control/dashboard', async (_req, res) => {
    try {
      const result = await engineFetch('/v1/mission-control/dashboard');
      if (!result.ok) {
        return res.status(result.status).json(result.data);
      }
      let desk = result.data && typeof result.data === 'object' ? { ...result.data } : {};
      // Soft enrich with CMS/KC learning digest — never block cockpit if digest fails
      let learning = null;
      try {
        learning = await buildRecentLearningSummary({ engineFetch, days: 5 });
      } catch {
        learning = null;
      }
      if (learning) {
        desk.learning_last_5_days = learning;
        desk.knowledge_growth = {
          ...(desk.knowledge_growth || {}),
          research_learned: learning.articles_learned,
          research_notes: learning.unique_articles,
          last_5_days_summary: learning.summary,
          last_5_days_highlights: learning.highlights,
          last_5_days: learning.by_day,
        };
        desk.executive_status = {
          ...(desk.executive_status || {}),
          last_successful_learning:
            learning.latest_learning_date || desk.executive_status?.last_successful_learning || null,
        };
        if (Array.isArray(desk.live_event_stream) && learning.summary) {
          desk.live_event_stream = [
            {
              at: new Date().toISOString(),
              type: 'learning',
              message: learning.summary,
            },
            ...desk.live_event_stream,
          ].slice(0, 40);
        }
      }
      // Soft enrich Groww + full .env API catalogue into API Status
      try {
        const { enrichMissionControlApis } = await import('../services/envApiCatalog.js');
        desk = await enrichMissionControlApis(desk);
      } catch {
        // never block Mission Control on provider catalogue
      }
      return res.json(desk);
    } catch (error) {
      return res.status(503).json({
        error: 'Mission Control dashboard unavailable',
        detail: error.message,
      });
    }
  });
  router.get('/mission-control/quality-gates', kfGet('/v1/mission-control/quality-gates'));
  router.get('/mission-control/report', kfGet('/v1/mission-control/report'));
  router.post('/mission-control/acknowledge', async (req, res) => {
    try {
      const result = await engineFetch('/v1/mission-control/acknowledge', {
        method: 'POST',
        body: req.body || {},
      });
      res.json(result);
    } catch (err) {
      res.status(502).json({ error: err?.message || 'Mission Control acknowledge failed' });
    }
  });

  // Investment Office V1 — executive operating cockpit
  router.get('/investment-office/health', kfGet('/v1/investment-office/health'));
  router.get('/investment-office/dashboard', kfGet('/v1/investment-office/dashboard'));
  router.get('/investment-office/quality-gates', kfGet('/v1/investment-office/quality-gates'));
  router.post('/investment-office/package', async (req, res) => {
    try {
      const result = await engineFetch('/v1/investment-office/package', {
        method: 'POST',
        body: req.body || {},
      });
      res.json(result);
    } catch (err) {
      res.status(502).json({ error: err?.message || 'Investment Office package failed' });
    }
  });

  // Company Monitoring System V1 — continuous living analyst
  router.get('/company-monitor/health', kfGet('/v1/company-monitor/health'));
  router.get('/company-monitor/dashboard', kfGet('/v1/company-monitor/dashboard'));
  router.get('/company-monitor/quality-gates', kfGet('/v1/company-monitor/quality-gates'));
  router.get('/company-monitor/changes', kfGet('/v1/company-monitor/changes'));
  router.get('/company-monitor/alerts', kfGet('/v1/company-monitor/alerts'));
  router.get('/company-monitor/reviews', kfGet('/v1/company-monitor/reviews'));
  router.post('/company-monitor/run', async (req, res) => {
    try {
      const result = await engineFetch('/v1/company-monitor/run', {
        method: 'POST',
        body: req.body || {},
      });
      res.json(result);
    } catch (err) {
      res.status(502).json({ error: err?.message || 'Company monitor run failed' });
    }
  });
  router.post('/company-monitor/run-universe', async (req, res) => {
    try {
      const result = await engineFetch('/v1/company-monitor/run-universe', {
        method: 'POST',
        body: req.body || {},
      });
      res.json(result);
    } catch (err) {
      res.status(502).json({ error: err?.message || 'Company monitor universe run failed' });
    }
  });

  // Company Analysis Engine V1 — apply Academy to companies (not Context Assembly)
  router.get('/company-analysis/health', kfGet('/v1/company-analysis/health'));
  router.get('/company-analysis/dashboard', kfGet('/v1/company-analysis/dashboard'));
  router.get('/company-analysis/quality-gates', kfGet('/v1/company-analysis/quality-gates'));
  router.get('/company-analysis/reports', kfGet('/v1/company-analysis/reports'));
  router.get('/company-analysis/report/:ticker', async (req, res) => {
    try {
      const result = await engineFetch(
        `/v1/company-analysis/report/${encodeURIComponent(req.params.ticker)}`
      );
      res.json(result);
    } catch (err) {
      res.status(502).json({ error: err?.message || 'Company analysis report failed' });
    }
  });
  router.post('/company-analysis/analyse', async (req, res) => {
    try {
      const result = await engineFetch('/v1/company-analysis/analyse', {
        method: 'POST',
        body: req.body || {},
      });
      res.json(result);
    } catch (err) {
      res.status(502).json({ error: err?.message || 'Company analysis failed' });
    }
  });

  return router;
}
