import { API_ORIGIN } from '@/config';

const BASE = API_ORIGIN || '';

async function intelligenceFetch(path, { method = 'GET', body } = {}) {
  const url = `${BASE}/api/intelligence${path}`;
  const resp = await fetch(url, {
    method,
    credentials: 'include',
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!resp.ok) {
    const detail = await resp.text().catch(() => '');
    throw new Error(`Intelligence API error (${resp.status}) ${detail.slice(0, 160)}`);
  }
  return resp.json();
}

export const getIntelligenceHealth = () => intelligenceFetch('/health');
export const createResearchRun = (payload) => intelligenceFetch('/research/runs', { method: 'POST', body: payload });
export const getResearchRun = (runId) => intelligenceFetch(`/research/runs/${encodeURIComponent(runId)}`);
export const listResearchRuns = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return intelligenceFetch(`/research/runs${qs ? `?${qs}` : ''}`);
};

/** KF1 Knowledge Foundation */
export const getKfHealth = () => intelligenceFetch('/kf/health');
export const getKfCoverage = () => intelligenceFetch('/kf/coverage');
export const seedKf = () => intelligenceFetch('/kf/seed', { method: 'POST', body: {} });
export const rebuildKf = () => intelligenceFetch('/kf/rebuild', { method: 'POST', body: {} });
export const searchKf = (q, limit = 12) => {
  const qs = new URLSearchParams({ q, limit: String(limit) }).toString();
  return intelligenceFetch(`/kf/search?${qs}`);
};
export const listKfCompanies = () => intelligenceFetch('/kf/companies');
export const listKfSectors = () => intelligenceFetch('/kf/sectors');
export const listKfThemes = () => intelligenceFetch('/kf/themes');
export const listKfMacros = () => intelligenceFetch('/kf/macros');
export const listKfPredictions = () => intelligenceFetch('/kf/predictions');
export const listKfExtracts = () => intelligenceFetch('/kf/extracts');

/** KCV1 Knowledge Corpus */
export const getKcHealth = () => intelligenceFetch('/kc/health');
export const getKcMetrics = () => intelligenceFetch('/kc/metrics');
export const getKcDashboard = () => intelligenceFetch('/kc/dashboard');
export const populateKc = (rebuildKip = true) =>
  intelligenceFetch(`/kc/populate?rebuild_kip=${rebuildKip ? 'true' : 'false'}`, {
    method: 'POST',
    body: {},
  });
export const ensureKcUniverse = () => intelligenceFetch('/kc/universe', { method: 'POST', body: {} });
export const getKcGaps = () => intelligenceFetch('/kc/gaps');
export const getKcLearning = () => intelligenceFetch('/kc/learning');
export const getKcQuality = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return intelligenceFetch(`/kc/quality${qs ? `?${qs}` : ''}`);
};
export const consultKc = (q, limit = 8) => {
  const qs = new URLSearchParams({ q, limit: String(limit) }).toString();
  return intelligenceFetch(`/kc/consult?${qs}`);
};

/** AOI v1 Open Intelligence */
export const getAoiHealth = () => intelligenceFetch('/aoi/health');
export const getAoiDashboard = () => intelligenceFetch('/aoi/dashboard');
export const seedAoiRegistry = () => intelligenceFetch('/aoi/registry/seed', { method: 'POST', body: {} });
export const runAoiCycle = (params = {}) => {
  const qs = new URLSearchParams(
    Object.fromEntries(
      Object.entries(params)
        .filter(([, v]) => v !== undefined && v !== null)
        .map(([k, v]) => [k, String(v)])
    )
  ).toString();
  return intelligenceFetch(`/aoi/run${qs ? `?${qs}` : ''}`, { method: 'POST', body: {} });
};
export const listAoiCompanies = (universe = 'nifty_50') => {
  const qs = new URLSearchParams({ universe }).toString();
  return intelligenceFetch(`/aoi/companies?${qs}`);
};
export const getAoiCompany = (key) => intelligenceFetch(`/aoi/company/${encodeURIComponent(key)}`);
export const searchAoi = (q, limit = 20) => {
  const qs = new URLSearchParams({ q, limit: String(limit) }).toString();
  return intelligenceFetch(`/aoi/search?${qs}`);
};
export const consultAoi = (q, limit = 8) => {
  const qs = new URLSearchParams({ q, limit: String(limit) }).toString();
  return intelligenceFetch(`/aoi/consult?${qs}`);
};
export const getAoiConnectors = () => intelligenceFetch('/aoi/connectors');
export const getAoiScheduler = () => intelligenceFetch('/aoi/scheduler');
export const getAoiGaps = () => intelligenceFetch('/aoi/gaps');
export const getAoiLearning = () => intelligenceFetch('/aoi/learning');
