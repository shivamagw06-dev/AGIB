import { Router } from 'express';
import { ENTITY_TYPES, RELATION_TYPES } from '../services/intelligencePlatform/entityTypes.js';
import {
  listEntities,
  getEntityBySlug,
  getEntityById,
  entityStats,
} from '../services/intelligencePlatform/entityStore.js';
import {
  getEntityRelationships,
  relationshipStats,
} from '../services/intelligencePlatform/relationshipStore.js';
import {
  listTimelineEvents,
  timelineStats,
} from '../services/intelligencePlatform/timelineService.js';
import { generateEntitySummary } from '../services/intelligencePlatform/aiSummaryService.js';
import { universalSearch, searchSuggestions } from '../services/intelligencePlatform/searchService.js';
import {
  bootstrapIntelligencePlatform,
  ensurePlatformBootstrapped,
} from '../services/intelligencePlatform/bootstrap.js';

let bootstrapPromise = null;

function runBootstrapOnce() {
  if (!bootstrapPromise) {
    bootstrapPromise = ensurePlatformBootstrapped().catch((err) => {
      bootstrapPromise = null;
      console.warn('[intelligence-platform] bootstrap failed:', err.message);
    });
  }
  return bootstrapPromise;
}

export default function createIntelligencePlatformRouter() {
  const router = Router();

  router.use(async (_req, _res, next) => {
    await runBootstrapOnce();
    next();
  });

  router.get('/health', (_req, res) => {
    res.json({
      ok: true,
      service: 'intelligence-platform',
      entityTypes: Object.keys(ENTITY_TYPES),
      relationTypes: Object.keys(RELATION_TYPES),
    });
  });

  router.get('/stats', (_req, res) => {
    res.json({
      entities: entityStats(),
      relationships: relationshipStats(),
      timeline: timelineStats(),
    });
  });

  router.post('/bootstrap', async (req, res) => {
    try {
      const result = await bootstrapIntelligencePlatform({ force: req.body?.force === true });
      res.json(result);
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  router.get('/search', (req, res) => {
    const q = req.query.q || '';
    const limit = Math.min(Number(req.query.limit) || 8, 20);
    res.json(universalSearch(q, { limit }));
  });

  router.get('/search/suggestions', (req, res) => {
    res.json({ suggestions: searchSuggestions(req.query.q || '', { limit: 6 }) });
  });

  router.get('/entities', (req, res) => {
    const result = listEntities({
      type: req.query.type || null,
      status: req.query.status || 'published',
      q: req.query.q || null,
      limit: Math.min(Number(req.query.limit) || 50, 200),
      offset: Number(req.query.offset) || 0,
    });
    res.json(result);
  });

  router.get('/entities/:slug', async (req, res) => {
    const entity = getEntityBySlug(req.params.slug);
    if (!entity || (entity.status !== 'published' && req.query.admin !== '1')) {
      return res.status(404).json({ error: 'Entity not found' });
    }
    const relationships = getEntityRelationships(entity.id);
    const timeline = listTimelineEvents(entity.id, { limit: 40 });
    let aiSummary = entity.ai_summary;
    if (!aiSummary || req.query.refresh === '1') {
      aiSummary = await generateEntitySummary(entity.id, { force: req.query.refresh === '1' });
    }
    res.json({ entity: { ...entity, ai_summary: aiSummary }, relationships, timeline });
  });

  router.get('/entities/:slug/relationships', (req, res) => {
    const entity = getEntityBySlug(req.params.slug);
    if (!entity) return res.status(404).json({ error: 'Entity not found' });
    res.json({ relationships: getEntityRelationships(entity.id) });
  });

  router.get('/entities/:slug/timeline', (req, res) => {
    const entity = getEntityBySlug(req.params.slug);
    if (!entity) return res.status(404).json({ error: 'Entity not found' });
    res.json({ timeline: listTimelineEvents(entity.id, { limit: 50 }) });
  });

  router.post('/entities/:slug/summary', async (req, res) => {
    const entity = getEntityBySlug(req.params.slug);
    if (!entity) return res.status(404).json({ error: 'Entity not found' });
    const summary = await generateEntitySummary(entity.id, { force: true });
    res.json({ summary, entity_id: entity.id });
  });

  router.get('/entity-types', (_req, res) => {
    res.json({ types: ENTITY_TYPES, relations: RELATION_TYPES });
  });

  return router;
}

export { getEntityById, getEntityBySlug };
