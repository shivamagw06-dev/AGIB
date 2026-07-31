import { Router } from 'express';
import { getPeFirm, getPeOverview, listPeFirms } from '../services/peIntelligenceService.js';

export default function createPeIntelligenceRouter() {
  const router = Router();

  router.get('/overview', (req, res) => {
    const sector = req.query.sector || null;
    return res.json(getPeOverview({ sector }));
  });

  router.get('/firms', (_req, res) => {
    return res.json({ firms: listPeFirms() });
  });

  router.get('/firms/:slug', (req, res) => {
    const firm = getPeFirm(req.params.slug);
    if (!firm) return res.status(404).json({ error: 'Firm not found' });
    return res.json(firm);
  });

  return router;
}
