/**
 * Newsletter + Publishing API routes.
 * Reuses Express app auth patterns; admin paths check X-AGI-Admin-Token or session proxy header.
 */

import { Router } from 'express';
import rateLimit from 'express-rate-limit';
import {
  commitCsvImport,
  deleteSubscriber,
  getAnalytics,
  listCampaigns,
  listPublishJobs,
  listSubscribers,
  PREFERENCE_KEYS,
  previewCsvImport,
  previewNewsletter,
  publishArticleWorkflow,
  recordEvent,
  segmentSubscribers,
  SOURCES,
  subscribe,
  unsubscribe,
  updatePreferences,
} from '../services/publishing/index.js';

const subscribeLimiter = rateLimit({
  windowMs: 60_000,
  max: 10,
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: 'Too many subscription attempts. Try again shortly.' },
});

function requireAdmin(req, res, next) {
  const expected = (process.env.PUBLISHING_ADMIN_TOKEN || process.env.INTELLIGENCE_ENGINE_TOKEN || 'dev-intelligence-token').trim();
  const auth = req.headers.authorization || '';
  const headerToken = req.headers['x-agi-admin-token'] || req.headers['x-agi-intelligence-token'];
  const bearer = auth.toLowerCase().startsWith('bearer ') ? auth.slice(7).trim() : '';
  const provided = String(headerToken || bearer || '').trim();
  if (!provided || provided !== expected) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  return next();
}

export default function createNewsletterRouter() {
  const router = Router();

  router.get('/health', (_req, res) => {
    res.json({
      ok: true,
      service: 'agi-publishing-newsletter',
      preferences: PREFERENCE_KEYS,
      sources: SOURCES,
    });
  });

  router.post('/newsletter/subscribe', subscribeLimiter, async (req, res) => {
    const result = await subscribe(req.body || {});
    if (!result.ok) return res.status(result.status || 400).json(result);
    return res.json(result);
  });

  router.post('/newsletter/import', requireAdmin, async (req, res) => {
    const { csv_text, csvText, source, filename, dry_run, dryRun, preview_only } = req.body || {};
    const text = csv_text || csvText || '';
    if (!text.trim()) return res.status(400).json({ error: 'csv_text required' });
    if (preview_only || dry_run || dryRun) {
      const preview = previewCsvImport(text, { source: source || 'csv_upload' });
      return res.json({ ...preview, committed: false });
    }
    const result = await commitCsvImport(text, {
      source: source || 'csv_upload',
      filename,
      created_by: req.headers['x-agi-user'] || null,
    });
    return res.json(result);
  });

  router.get('/newsletter/subscribers', requireAdmin, (req, res) => {
    const result = listSubscribers({
      q: req.query.q,
      email: req.query.email,
      name: req.query.name,
      source: req.query.source,
      tags: req.query.tags,
      preference: req.query.preference,
      status: req.query.status,
      limit: Number(req.query.limit || 100),
      offset: Number(req.query.offset || 0),
    });
    return res.json(result);
  });

  router.patch('/newsletter/preferences', async (req, res) => {
    const result = await updatePreferences(req.body || {});
    if (!result.ok) return res.status(result.status || 400).json(result);
    return res.json(result);
  });

  router.delete('/newsletter/unsubscribe', async (req, res) => {
    const body = { ...(req.body || {}), ...(req.query || {}) };
    if (body.gdpr_delete || body.gdprDelete) {
      const result = await deleteSubscriber(body);
      if (!result.ok) return res.status(result.status || 400).json(result);
      return res.json(result);
    }
    const result = await unsubscribe(body);
    if (!result.ok) return res.status(result.status || 400).json(result);
    return res.json(result);
  });

  // POST alias for unsubscribe (email clients / forms)
  router.post('/newsletter/unsubscribe', async (req, res) => {
    const result = await unsubscribe(req.body || {});
    if (!result.ok) return res.status(result.status || 400).json(result);
    return res.json(result);
  });

  router.post('/newsletter/send', requireAdmin, async (req, res) => {
    const article = req.body?.article || req.body || {};
    const segment = req.body?.segment || 'all';
    if (!article.title && !article.slug) {
      return res.status(400).json({ error: 'article title or slug required' });
    }
    const result = await publishArticleWorkflow(article, {
      segment,
      dryRun: Boolean(req.body?.dry_run || req.body?.dryRun),
    });
    return res.json(result);
  });

  router.post('/publish/article', requireAdmin, async (req, res) => {
    const article = req.body?.article || req.body || {};
    if (!article.title && !article.slug) {
      return res.status(400).json({ error: 'article payload required' });
    }
    const result = await publishArticleWorkflow(article, {
      segment: req.body?.segment || 'all',
      dryRun: Boolean(req.body?.dry_run || req.body?.dryRun),
    });
    return res.json(result);
  });

  router.get('/newsletter/analytics', requireAdmin, (_req, res) => {
    return res.json(getAnalytics());
  });

  router.get('/newsletter/campaigns', requireAdmin, (req, res) => {
    return res.json({ campaigns: listCampaigns(Number(req.query.limit || 50)) });
  });

  router.get('/newsletter/jobs', requireAdmin, (req, res) => {
    return res.json({ jobs: listPublishJobs(Number(req.query.limit || 50)) });
  });

  router.post('/newsletter/preview', requireAdmin, (req, res) => {
    return res.json(previewNewsletter(req.body?.article || req.body || {}));
  });

  router.get('/newsletter/segments/:segment', requireAdmin, (req, res) => {
    const rows = segmentSubscribers(req.params.segment);
    return res.json({ segment: req.params.segment, count: rows.length, emails: rows.map((r) => r.email) });
  });

  router.post('/newsletter/events', async (req, res) => {
    const row = recordEvent(req.body || {});
    return res.json({ ok: true, event: row });
  });

  return router;
}
