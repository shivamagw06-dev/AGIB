import { API_ORIGIN } from '@/config';

const BASE = API_ORIGIN || '';

async function intelligenceFetch(path, { method = 'GET', body } = {}) {
  if (!BASE) {
    throw new Error('API origin is not configured. Set VITE_API_URL to the Render backend.');
  }
  const url = `${BASE}/api/intelligence${path}`;
  const resp = await fetch(url, {
    method,
    credentials: 'include',
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  const contentType = resp.headers.get('content-type') || '';
  const text = await resp.text().catch(() => '');
  if (!contentType.includes('application/json') || text.trim().startsWith('<')) {
    throw new Error(
      `Intelligence API returned HTML instead of JSON for ${path}. Check VITE_API_URL points at Render, not the website.`
    );
  }
  if (!resp.ok) {
    throw new Error(`Intelligence API error (${resp.status}) ${text.slice(0, 160)}`);
  }
  try {
    return text ? JSON.parse(text) : null;
  } catch {
    throw new Error(`Intelligence API invalid JSON for ${path}`);
  }
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

/** EVE v1 Evidence & Verification */
export const getEveHealth = () => intelligenceFetch('/eve/health');
export const getEveDashboard = () => intelligenceFetch('/eve/dashboard');
export const listEveEvidence = (params = {}) => {
  const qs = new URLSearchParams(
    Object.fromEntries(
      Object.entries(params)
        .filter(([, v]) => v !== undefined && v !== null && v !== '')
        .map(([k, v]) => [k, String(v)])
    )
  ).toString();
  return intelligenceFetch(`/eve/evidence${qs ? `?${qs}` : ''}`);
};
export const getEveEvidence = (id) => intelligenceFetch(`/eve/evidence/${encodeURIComponent(id)}`);
export const getEveCompany = (key) => intelligenceFetch(`/eve/company/${encodeURIComponent(key)}`);
export const getEveConflicts = (status = 'open') => {
  const qs = new URLSearchParams({ status }).toString();
  return intelligenceFetch(`/eve/conflicts?${qs}`);
};
export const getEveTimeline = (params = {}) => {
  const qs = new URLSearchParams(
    Object.fromEntries(
      Object.entries(params)
        .filter(([, v]) => v !== undefined && v !== null && v !== '')
        .map(([k, v]) => [k, String(v)])
    )
  ).toString();
  return intelligenceFetch(`/eve/timeline${qs ? `?${qs}` : ''}`);
};
export const getEveTrust = () => intelligenceFetch('/eve/trust');
export const getEveSources = () => intelligenceFetch('/eve/source');
export const getEveVerification = () => intelligenceFetch('/eve/verification');
export const runEveVerification = () => intelligenceFetch('/eve/verification/run', { method: 'POST', body: {} });
export const searchEve = (q, limit = 20) => {
  const qs = new URLSearchParams({ q, limit: String(limit) }).toString();
  return intelligenceFetch(`/eve/search?${qs}`);
};
export const consultEve = (q, limit = 8) => {
  const qs = new URLSearchParams({ q, limit: String(limit) }).toString();
  return intelligenceFetch(`/eve/consult?${qs}`);
};
export const getEveAudit = (limit = 50) => {
  const qs = new URLSearchParams({ limit: String(limit) }).toString();
  return intelligenceFetch(`/eve/audit?${qs}`);
};

/** IIE v1 Investment Intelligence */
export const getIieHealth = () => intelligenceFetch('/iie/health');
export const getIieDashboard = () => intelligenceFetch('/iie/dashboard');
export const analyseIieCompany = (key) => {
  const qs = new URLSearchParams({ key }).toString();
  return intelligenceFetch(`/iie/analyse?${qs}`, { method: 'POST', body: {} });
};
export const runIieBatch = (limit = 20) => {
  const qs = new URLSearchParams({ limit: String(limit) }).toString();
  return intelligenceFetch(`/iie/batch?${qs}`, { method: 'POST', body: {} });
};
export const getIieCompany = (key) => intelligenceFetch(`/iie/company/${encodeURIComponent(key)}`);
export const getIieSectors = () => intelligenceFetch('/iie/sector');
export const getIieSector = (id) => intelligenceFetch(`/iie/sector/${encodeURIComponent(id)}`);
export const getIieThemes = () => intelligenceFetch('/iie/theme');
export const getIieTheme = (id) => intelligenceFetch(`/iie/theme/${encodeURIComponent(id)}`);
export const getIieThesis = (key) => intelligenceFetch(`/iie/thesis/${encodeURIComponent(key)}`);
export const getIieScenario = (key) => intelligenceFetch(`/iie/scenario/${encodeURIComponent(key)}`);
export const getIieCatalysts = (params = {}) => {
  const qs = new URLSearchParams(
    Object.fromEntries(
      Object.entries(params)
        .filter(([, v]) => v !== undefined && v !== null && v !== '')
        .map(([k, v]) => [k, String(v)])
    )
  ).toString();
  return intelligenceFetch(`/iie/catalysts${qs ? `?${qs}` : ''}`);
};
export const getIieRisks = (params = {}) => {
  const qs = new URLSearchParams(
    Object.fromEntries(
      Object.entries(params)
        .filter(([, v]) => v !== undefined && v !== null && v !== '')
        .map(([k, v]) => [k, String(v)])
    )
  ).toString();
  return intelligenceFetch(`/iie/risks${qs ? `?${qs}` : ''}`);
};
export const getIieOpportunities = (params = {}) => {
  const qs = new URLSearchParams(
    Object.fromEntries(
      Object.entries(params)
        .filter(([, v]) => v !== undefined && v !== null && v !== '')
        .map(([k, v]) => [k, String(v)])
    )
  ).toString();
  return intelligenceFetch(`/iie/opportunities${qs ? `?${qs}` : ''}`);
};
export const compareIie = (companies, dimensions) => {
  const qs = new URLSearchParams({ companies: Array.isArray(companies) ? companies.join(',') : companies });
  if (dimensions) qs.set('dimensions', Array.isArray(dimensions) ? dimensions.join(',') : dimensions);
  return intelligenceFetch(`/iie/compare?${qs}`);
};
export const getIieMonitor = (key) => intelligenceFetch(`/iie/monitor/${encodeURIComponent(key)}`);
export const getIieDna = (key) => intelligenceFetch(`/iie/dna/${encodeURIComponent(key)}`);
export const getIieMacro = (event) => {
  const qs = new URLSearchParams({ event }).toString();
  return intelligenceFetch(`/iie/macro?${qs}`);
};
export const getIieEvolution = (params = {}) => {
  const qs = new URLSearchParams(
    Object.fromEntries(
      Object.entries(params)
        .filter(([, v]) => v !== undefined && v !== null && v !== '')
        .map(([k, v]) => [k, String(v)])
    )
  ).toString();
  return intelligenceFetch(`/iie/evolution${qs ? `?${qs}` : ''}`);
};
export const searchIie = (q, limit = 20) => {
  const qs = new URLSearchParams({ q, limit: String(limit) }).toString();
  return intelligenceFetch(`/iie/search?${qs}`);
};
export const consultIie = (q, limit = 8) => {
  const qs = new URLSearchParams({ q, limit: String(limit) }).toString();
  return intelligenceFetch(`/iie/consult?${qs}`);
};

/** FAA v1 Finance Acquisition Agent — gather public docs, feed FRE */
export const getFaaHealth = () => intelligenceFetch('/faa/health');
export const getFaaDashboard = () => intelligenceFetch('/faa/dashboard');
export const discoverFaa = (q, limit = 40) => {
  const qs = new URLSearchParams({ q, limit: String(limit) }).toString();
  return intelligenceFetch(`/faa/discover?${qs}`);
};
export const acquireFaa = (q, limit = 24) => {
  const qs = new URLSearchParams({ q, limit: String(limit) }).toString();
  return intelligenceFetch(`/faa/acquire?${qs}`, { method: 'POST', body: {} });
};
export const getFaaConnectors = () => intelligenceFetch('/faa/connectors');
export const getFaaScheduler = () => intelligenceFetch('/faa/scheduler');
export const runFaaJobs = () => intelligenceFetch('/faa/jobs', { method: 'POST', body: {} });
export const consultFaa = (q, limit = 8) => {
  const qs = new URLSearchParams({ q, limit: String(limit) }).toString();
  return intelligenceFetch(`/faa/consult?${qs}`);
};

/** FRE v1 Finance Retrieval Engine — evidence only, never answers */
export const getFreHealth = () => intelligenceFetch('/fre/health');
export const getFreDashboard = () => intelligenceFetch('/fre/dashboard');
export const queryFre = (q, params = {}) => {
  const qs = new URLSearchParams({
    q,
    ...Object.fromEntries(
      Object.entries(params)
        .filter(([, v]) => v !== undefined && v !== null && v !== '')
        .map(([k, v]) => [k, String(v)])
    ),
  }).toString();
  return intelligenceFetch(`/fre/query?${qs}`);
};
export const searchFre = (q, params = {}) => {
  const qs = new URLSearchParams({
    q,
    ...Object.fromEntries(
      Object.entries(params)
        .filter(([, v]) => v !== undefined && v !== null && v !== '')
        .map(([k, v]) => [k, String(v)])
    ),
  }).toString();
  return intelligenceFetch(`/fre/search?${qs}`);
};
export const getFreCompany = (key, limit = 20) => {
  const qs = new URLSearchParams({ limit: String(limit) }).toString();
  return intelligenceFetch(`/fre/company/${encodeURIComponent(key)}?${qs}`);
};
export const getFreDocument = (id) => intelligenceFetch(`/fre/document/${encodeURIComponent(id)}`);
export const getFreEvidence = (params = {}) => {
  const qs = new URLSearchParams(
    Object.fromEntries(
      Object.entries(params)
        .filter(([, v]) => v !== undefined && v !== null && v !== '')
        .map(([k, v]) => [k, String(v)])
    )
  ).toString();
  return intelligenceFetch(`/fre/evidence${qs ? `?${qs}` : ''}`);
};
export const getFreTimeline = (params = {}) => {
  const qs = new URLSearchParams(
    Object.fromEntries(
      Object.entries(params)
        .filter(([, v]) => v !== undefined && v !== null && v !== '')
        .map(([k, v]) => [k, String(v)])
    )
  ).toString();
  return intelligenceFetch(`/fre/timeline${qs ? `?${qs}` : ''}`);
};
export const getFreNews = (limit = 20) => {
  const qs = new URLSearchParams({ limit: String(limit) }).toString();
  return intelligenceFetch(`/fre/news?${qs}`);
};
export const getFreGraph = (entity) => {
  const qs = entity ? new URLSearchParams({ entity }).toString() : '';
  return intelligenceFetch(`/fre/graph${qs ? `?${qs}` : ''}`);
};
export const ingestFre = (payload) => intelligenceFetch('/fre/ingest', { method: 'POST', body: payload || {} });
export const runFreJobs = () => intelligenceFetch('/fre/jobs', { method: 'POST', body: {} });
export const consultFre = (q, limit = 8) => {
  const qs = new URLSearchParams({ q, limit: String(limit) }).toString();
  return intelligenceFetch(`/fre/consult?${qs}`);
};
export const getFreScheduler = () => intelligenceFetch('/fre/scheduler');

/** FLE v1 Forecasting & Learning */
export const getFleHealth = () => intelligenceFetch('/fle/health');
export const getFleDashboard = () => intelligenceFetch('/fle/dashboard');
export const listFleForecasts = (params = {}) => {
  const qs = new URLSearchParams(
    Object.fromEntries(
      Object.entries(params)
        .filter(([, v]) => v !== undefined && v !== null && v !== '')
        .map(([k, v]) => [k, String(v)])
    )
  ).toString();
  return intelligenceFetch(`/fle/forecast${qs ? `?${qs}` : ''}`);
};
export const createFleForecast = (payload) =>
  intelligenceFetch('/fle/forecast', { method: 'POST', body: payload || {} });
export const getFleForecast = (id) => intelligenceFetch(`/fle/forecast/${encodeURIComponent(id)}`);
export const resolveFleForecast = (id, payload) =>
  intelligenceFetch(`/fle/forecast/${encodeURIComponent(id)}/resolve`, {
    method: 'POST',
    body: payload || {},
  });
export const versionFleForecast = (id, payload) =>
  intelligenceFetch(`/fle/forecast/${encodeURIComponent(id)}/version`, {
    method: 'POST',
    body: payload || {},
  });
export const compareFleForecast = (id) => intelligenceFetch(`/fle/compare/${encodeURIComponent(id)}`);
export const getFleCompany = (key) => intelligenceFetch(`/fle/company/${encodeURIComponent(key)}`);
export const getFleOutcomes = (params = {}) => {
  const qs = new URLSearchParams(
    Object.fromEntries(
      Object.entries(params)
        .filter(([, v]) => v !== undefined && v !== null && v !== '')
        .map(([k, v]) => [k, String(v)])
    )
  ).toString();
  return intelligenceFetch(`/fle/outcomes${qs ? `?${qs}` : ''}`);
};
export const getFleLearning = (params = {}) => {
  const qs = new URLSearchParams(
    Object.fromEntries(
      Object.entries(params)
        .filter(([, v]) => v !== undefined && v !== null && v !== '')
        .map(([k, v]) => [k, String(v)])
    )
  ).toString();
  return intelligenceFetch(`/fle/learning${qs ? `?${qs}` : ''}`);
};
export const getFleCalibration = () => intelligenceFetch('/fle/calibration');
export const getFleScenarios = (id) => intelligenceFetch(`/fle/scenarios/${encodeURIComponent(id)}`);
export const getFleAccuracy = (params = {}) => {
  const qs = new URLSearchParams(
    Object.fromEntries(
      Object.entries(params)
        .filter(([, v]) => v !== undefined && v !== null && v !== '')
        .map(([k, v]) => [k, String(v)])
    )
  ).toString();
  return intelligenceFetch(`/fle/accuracy${qs ? `?${qs}` : ''}`);
};
export const getFleHistory = (params = {}) => {
  const qs = new URLSearchParams(
    Object.fromEntries(
      Object.entries(params)
        .filter(([, v]) => v !== undefined && v !== null && v !== '')
        .map(([k, v]) => [k, String(v)])
    )
  ).toString();
  return intelligenceFetch(`/fle/history${qs ? `?${qs}` : ''}`);
};
export const generateFleForecasts = (key) => {
  const qs = new URLSearchParams({ key }).toString();
  return intelligenceFetch(`/fle/generate?${qs}`, { method: 'POST', body: {} });
};
export const runFleBatch = (limit = 20) => {
  const qs = new URLSearchParams({ limit: String(limit) }).toString();
  return intelligenceFetch(`/fle/batch?${qs}`, { method: 'POST', body: {} });
};
export const runFleJobs = () => intelligenceFetch('/fle/jobs', { method: 'POST', body: {} });
export const searchFle = (q, limit = 20) => {
  const qs = new URLSearchParams({ q, limit: String(limit) }).toString();
  return intelligenceFetch(`/fle/search?${qs}`);
};
export const consultFle = (q, limit = 8) => {
  const qs = new URLSearchParams({ q, limit: String(limit) }).toString();
  return intelligenceFetch(`/fle/consult?${qs}`);
};

/** MEE v1 Market Event Engine */
export const getMeeHealth = () => intelligenceFetch('/mee/health');
export const getMeeDashboard = () => intelligenceFetch('/mee/dashboard');
export const listMeeEvents = (params = {}) => {
  const qs = new URLSearchParams(
    Object.fromEntries(
      Object.entries(params)
        .filter(([, v]) => v !== undefined && v !== null && v !== '')
        .map(([k, v]) => [k, String(v)])
    )
  ).toString();
  return intelligenceFetch(`/mee/events${qs ? `?${qs}` : ''}`);
};
export const createMeeEvent = (payload) =>
  intelligenceFetch('/mee/events', { method: 'POST', body: payload || {} });
export const getMeeEvent = (id) => intelligenceFetch(`/mee/events/${encodeURIComponent(id)}`);
export const verifyMeeEvent = (id) =>
  intelligenceFetch(`/mee/events/${encodeURIComponent(id)}/verify`, { method: 'POST', body: {} });
export const versionMeeEvent = (id, payload) =>
  intelligenceFetch(`/mee/events/${encodeURIComponent(id)}/version`, {
    method: 'POST',
    body: payload || {},
  });
export const getMeeCompany = (key) => intelligenceFetch(`/mee/company/${encodeURIComponent(key)}`);
export const getMeeSector = (id) => intelligenceFetch(`/mee/sector/${encodeURIComponent(id)}`);
export const getMeeTheme = (id) => intelligenceFetch(`/mee/theme/${encodeURIComponent(id)}`);
export const getMeeTimeline = (params = {}) => {
  const qs = new URLSearchParams(
    Object.fromEntries(
      Object.entries(params)
        .filter(([, v]) => v !== undefined && v !== null && v !== '')
        .map(([k, v]) => [k, String(v)])
    )
  ).toString();
  return intelligenceFetch(`/mee/timeline${qs ? `?${qs}` : ''}`);
};
export const getMeeImpact = (id) => intelligenceFetch(`/mee/impact/${encodeURIComponent(id)}`);
export const getMeeRelationships = (params = {}) => {
  const qs = new URLSearchParams(
    Object.fromEntries(
      Object.entries(params)
        .filter(([, v]) => v !== undefined && v !== null && v !== '')
        .map(([k, v]) => [k, String(v)])
    )
  ).toString();
  return intelligenceFetch(`/mee/relationships${qs ? `?${qs}` : ''}`);
};
export const getMeeHistory = (params = {}) => {
  const qs = new URLSearchParams(
    Object.fromEntries(
      Object.entries(params)
        .filter(([, v]) => v !== undefined && v !== null && v !== '')
        .map(([k, v]) => [k, String(v)])
    )
  ).toString();
  return intelligenceFetch(`/mee/history${qs ? `?${qs}` : ''}`);
};
export const getMeeSimilar = (id, limit = 8) => {
  const qs = new URLSearchParams({ limit: String(limit) }).toString();
  return intelligenceFetch(`/mee/similar/${encodeURIComponent(id)}?${qs}`);
};
export const runMeeCycle = (limit = 40) => {
  const qs = new URLSearchParams({ limit: String(limit) }).toString();
  return intelligenceFetch(`/mee/cycle?${qs}`, { method: 'POST', body: {} });
};
export const searchMee = (q, limit = 20) => {
  const qs = new URLSearchParams({ q, limit: String(limit) }).toString();
  return intelligenceFetch(`/mee/search?${qs}`);
};
export const consultMee = (q, limit = 8) => {
  const qs = new URLSearchParams({ q, limit: String(limit) }).toString();
  return intelligenceFetch(`/mee/consult?${qs}`);
};

/** CAE v1 Context Assembly */
export const getCaeHealth = () => intelligenceFetch('/cae/health');
export const getCaeDashboard = () => intelligenceFetch('/cae/dashboard');
export const getCaeContext = (q, params = {}) => {
  const qs = new URLSearchParams({
    q,
    ...Object.fromEntries(
      Object.entries(params)
        .filter(([, v]) => v !== undefined && v !== null && v !== '')
        .map(([k, v]) => [k, String(v)])
    ),
  }).toString();
  return intelligenceFetch(`/cae/context?${qs}`);
};
export const getCaeQueryPlan = (q, ticker) => {
  const qs = new URLSearchParams({ q });
  if (ticker) qs.set('ticker', ticker);
  return intelligenceFetch(`/cae/query-plan?${qs}`);
};
export const getCaeRetrieval = (q, ticker) => {
  const qs = new URLSearchParams({ q });
  if (ticker) qs.set('ticker', ticker);
  return intelligenceFetch(`/cae/retrieval?${qs}`);
};
export const getCaeCache = () => intelligenceFetch('/cae/cache');
export const clearCaeCache = () => intelligenceFetch('/cae/cache/clear', { method: 'POST', body: {} });
export const getCaeMetrics = () => intelligenceFetch('/cae/metrics');
export const explainCaePackage = (id) => intelligenceFetch(`/cae/explain/${encodeURIComponent(id)}`);
export const getCaePackage = (id) => intelligenceFetch(`/cae/package/${encodeURIComponent(id)}`);
export const searchCae = (q, limit = 20) => {
  const qs = new URLSearchParams({ q, limit: String(limit) }).toString();
  return intelligenceFetch(`/cae/search?${qs}`);
};

/** IB v1 Intelligence Bus */
export const getIbHealth = () => intelligenceFetch('/ib/health');
export const getIbDashboard = () => intelligenceFetch('/ib/dashboard');
export const getIbEvents = (params = {}) => {
  const qs = new URLSearchParams(
    Object.fromEntries(
      Object.entries(params)
        .filter(([, v]) => v !== undefined && v !== null && v !== '')
        .map(([k, v]) => [k, String(v)])
    )
  ).toString();
  return intelligenceFetch(`/ib/events${qs ? `?${qs}` : ''}`);
};
export const publishIbEvent = (body = {}) =>
  intelligenceFetch('/ib/publish', { method: 'POST', body });
export const getIbSubscriptions = () => intelligenceFetch('/ib/subscriptions');
export const createIbSubscription = (body = {}) =>
  intelligenceFetch('/ib/subscriptions', { method: 'POST', body });
export const replayIbEvents = (body = {}) =>
  intelligenceFetch('/ib/replay', { method: 'POST', body });
export const getIbHistory = (params = {}) => {
  const qs = new URLSearchParams(
    Object.fromEntries(
      Object.entries(params)
        .filter(([, v]) => v !== undefined && v !== null && v !== '')
        .map(([k, v]) => [k, String(v)])
    )
  ).toString();
  return intelligenceFetch(`/ib/history${qs ? `?${qs}` : ''}`);
};
export const getIbMetrics = () => intelligenceFetch('/ib/metrics');
export const getIbTraces = (params = {}) => {
  const qs = new URLSearchParams(
    Object.fromEntries(
      Object.entries(params)
        .filter(([, v]) => v !== undefined && v !== null && v !== '')
        .map(([k, v]) => [k, String(v)])
    )
  ).toString();
  return intelligenceFetch(`/ib/traces${qs ? `?${qs}` : ''}`);
};
export const getIbDeadLetter = (limit = 50) => {
  const qs = new URLSearchParams({ limit: String(limit) }).toString();
  return intelligenceFetch(`/ib/dead-letter?${qs}`);
};
export const resolveIbDeadLetter = (id) =>
  intelligenceFetch(`/ib/dead-letter/${encodeURIComponent(id)}/resolve`, {
    method: 'POST',
    body: {},
  });
export const getIbSchema = (eventType) => {
  const qs = new URLSearchParams();
  if (eventType) qs.set('event_type', eventType);
  const s = qs.toString();
  return intelligenceFetch(`/ib/schema${s ? `?${s}` : ''}`);
};
export const runIbDemoChain = (companySymbol = 'INFY') => {
  const qs = new URLSearchParams({ company_symbol: companySymbol }).toString();
  return intelligenceFetch(`/ib/demo-chain?${qs}`, { method: 'POST', body: {} });
};

/** VE v1 Valuation Engine */
export const getVeHealth = () => intelligenceFetch('/ve/health');
export const getVeDashboard = () => intelligenceFetch('/ve/dashboard');
export const getVeCompany = (key, params = {}) => {
  const qs = new URLSearchParams(
    Object.fromEntries(
      Object.entries(params)
        .filter(([, v]) => v !== undefined && v !== null && v !== '')
        .map(([k, v]) => [k, String(v)])
    )
  ).toString();
  return intelligenceFetch(`/ve/company/${encodeURIComponent(key)}${qs ? `?${qs}` : ''}`);
};
export const getVeModel = (model, key, marketPrice) => {
  const qs = new URLSearchParams({ model, key });
  if (marketPrice != null) qs.set('market_price', String(marketPrice));
  return intelligenceFetch(`/ve/model?${qs}`);
};
export const getVeHistory = (key, limit = 50) => {
  const qs = new URLSearchParams({ key, limit: String(limit) }).toString();
  return intelligenceFetch(`/ve/history?${qs}`);
};
export const getVeScenarios = (key) => {
  const qs = new URLSearchParams({ key }).toString();
  return intelligenceFetch(`/ve/scenarios?${qs}`);
};
export const getVeCompare = (key, peers) => {
  const qs = new URLSearchParams({ key });
  if (peers) qs.set('peers', Array.isArray(peers) ? peers.join(',') : String(peers));
  return intelligenceFetch(`/ve/compare?${qs}`);
};
export const getVeSensitivity = (key) => {
  const qs = new URLSearchParams({ key }).toString();
  return intelligenceFetch(`/ve/sensitivity?${qs}`);
};
export const searchVe = (q, limit = 20) => {
  const qs = new URLSearchParams({ q, limit: String(limit) }).toString();
  return intelligenceFetch(`/ve/search?${qs}`);
};
export const consultVe = (q, limit = 8) => {
  const qs = new URLSearchParams({ q, limit: String(limit) }).toString();
  return intelligenceFetch(`/ve/consult?${qs}`);
};
export const valueVeCompany = (body = {}) =>
  intelligenceFetch('/ve/value', { method: 'POST', body });
export const getVeValuation = (id) =>
  intelligenceFetch(`/ve/valuation/${encodeURIComponent(id)}`);

/** FIML v1 — Financial Intelligence Model Library */
export const getFimlHealth = () => intelligenceFetch('/fiml/health');
export const getFimlDashboard = () => intelligenceFetch('/fiml/dashboard');
export const getFimlModels = () => intelligenceFetch('/fiml/models');
export const getFimlIndustries = () => intelligenceFetch('/fiml/industries');
export const getFimlMetrics = () => intelligenceFetch('/fiml/metrics');
export const getFimlGraph = () => intelligenceFetch('/fiml/graph');
export const searchFiml = (q, domain, limit = 20) => {
  const qs = new URLSearchParams({ q, limit: String(limit) });
  if (domain) qs.set('domain', domain);
  return intelligenceFetch(`/fiml/search?${qs}`);
};
export const analyseFiml = (domain, body = {}) =>
  intelligenceFetch(`/fiml/analyse/${encodeURIComponent(domain)}`, { method: 'POST', body });
export const scoreFiml = (domain, body = {}) =>
  intelligenceFetch(`/fiml/score/${encodeURIComponent(domain)}`, { method: 'POST', body });
export const explainFiml = (domain, body = {}) =>
  intelligenceFetch(`/fiml/explain/${encodeURIComponent(domain)}`, { method: 'POST', body });
export const compareFiml = (domain, body = {}) =>
  intelligenceFetch(`/fiml/compare/${encodeURIComponent(domain)}`, { method: 'POST', body });
export const bundleFiml = (body = {}) =>
  intelligenceFetch('/fiml/bundle', { method: 'POST', body });
export const consumerFiml = (engine, body = {}) =>
  intelligenceFetch(`/fiml/consumer/${encodeURIComponent(engine)}`, { method: 'POST', body });

/** AGI Finance Academy v1.1 — institutional multi-course curriculum library */
export const getAcademyHealth = () => intelligenceFetch('/academy/health');
export const getAcademyDashboard = () => intelligenceFetch('/academy/dashboard');
export const getAcademyCourses = () => intelligenceFetch('/academy/courses');
export const getAcademyCourse = (courseId) => {
  const qs = new URLSearchParams();
  if (courseId) qs.set('course_id', courseId);
  const suffix = qs.toString() ? `?${qs}` : '';
  return intelligenceFetch(`/academy/course${suffix}`);
};
export const getAcademyConcepts = (tag, courseId) => {
  const qs = new URLSearchParams();
  if (tag) qs.set('tag', tag);
  if (courseId) qs.set('course_id', courseId);
  const suffix = qs.toString() ? `?${qs}` : '';
  return intelligenceFetch(`/academy/concepts${suffix}`);
};
export const getAcademyConcept = (id) =>
  intelligenceFetch(`/academy/concepts/${encodeURIComponent(id)}`);
export const teachAcademyConcept = (id) =>
  intelligenceFetch(`/academy/teach/${encodeURIComponent(id)}`);
export const getAcademyGraph = (courseId) => {
  const qs = new URLSearchParams();
  if (courseId) qs.set('course_id', courseId);
  const suffix = qs.toString() ? `?${qs}` : '';
  return intelligenceFetch(`/academy/graph${suffix}`);
};
export const getAcademyCausalModels = () => intelligenceFetch('/academy/causal-models');
export const getAcademyMentalModels = () => intelligenceFetch('/academy/mental-models');
export const getAcademyQuality = (courseId) => {
  const qs = new URLSearchParams();
  if (courseId) qs.set('course_id', courseId);
  const suffix = qs.toString() ? `?${qs}` : '';
  return intelligenceFetch(`/academy/quality${suffix}`);
};
export const getAcademyProvenance = () => intelligenceFetch('/academy/provenance');
export const getAcademyExams = (courseId) => {
  const qs = new URLSearchParams();
  if (courseId) qs.set('course_id', courseId);
  const suffix = qs.toString() ? `?${qs}` : '';
  return intelligenceFetch(`/academy/exams${suffix}`);
};
export const getAcademyExamAnswer = (id) =>
  intelligenceFetch(`/academy/exams/${encodeURIComponent(id)}`);
export const getAcademyCompletion = (courseId) => {
  const qs = new URLSearchParams();
  if (courseId) qs.set('course_id', courseId);
  const suffix = qs.toString() ? `?${qs}` : '';
  return intelligenceFetch(`/academy/completion${suffix}`);
};
export const getAcademyRedFlags = () => intelligenceFetch('/academy/red-flags');
export const getAcademyAccounting = () => intelligenceFetch('/academy/accounting');
export const getAcademyCorporateFinance = () => intelligenceFetch('/academy/corporate-finance');
export const scoreAcademyEarningsQuality = (body = {}) =>
  intelligenceFetch('/academy/earnings-quality', { method: 'POST', body });
export const scoreAcademyRedFlags = (body = {}) =>
  intelligenceFetch('/academy/red-flags/score', { method: 'POST', body });
export const searchAcademy = (q, limit = 20, courseId) => {
  const qs = new URLSearchParams({ q, limit: String(limit) });
  if (courseId) qs.set('course_id', courseId);
  return intelligenceFetch(`/academy/search?${qs}`);
};
export const consumerAcademy = (engine, body = {}) =>
  intelligenceFetch(`/academy/consumer/${encodeURIComponent(engine)}`, { method: 'POST', body });
export const getAcademyProduction = () => intelligenceFetch('/academy/production');
export const getAcademyProductionAb = (question) => {
  const qs = question ? `?question=${encodeURIComponent(question)}` : '';
  return intelligenceFetch(`/academy/production/ab${qs}`);
};
export const getAcademyProductionQualityGates = () =>
  intelligenceFetch('/academy/production/quality-gates');
export const packageAcademyProduction = (query, engine = 'cae', ticker) => {
  const qs = new URLSearchParams({ query: query || '', engine });
  if (ticker) qs.set('ticker', ticker);
  return intelligenceFetch(`/academy/production/package?${qs}`, { method: 'POST', body: {} });
};
export const getAcademyBooksHealth = () => intelligenceFetch('/academy/books/health');
export const getAcademyBooksDashboard = () => intelligenceFetch('/academy/books/dashboard');
export const getAcademyBooksQualityGates = () => intelligenceFetch('/academy/books/quality-gates');
export const getAcademyBooksGraph = () => intelligenceFetch('/academy/books/graph');
export const ingestAcademyBook = (body = {}) =>
  intelligenceFetch('/academy/books/ingest', { method: 'POST', body });
export const packageAcademyBooks = (query, ticker) => {
  const qs = new URLSearchParams({ query: query || '' });
  if (ticker) qs.set('ticker', ticker);
  return intelligenceFetch(`/academy/books/package?${qs}`, { method: 'POST', body: {} });
};
export const attachAcademyBooksKf = () =>
  intelligenceFetch('/academy/books/attach-kf', { method: 'POST', body: {} });
export const getAcademyBooksLibrary = () => intelligenceFetch('/academy/books/library');
export const getAcademyBooksIngestionReport = () =>
  intelligenceFetch('/academy/books/ingestion-report');
export const ingestAcademyBooksLibrary = (body = {}) =>
  intelligenceFetch('/academy/books/ingest-library', { method: 'POST', body });

/** CMS article learning — bulk read uploaded articles into KIP/KF/KC with learning dates */
export const learnCmsArticles = (body = {}) =>
  intelligenceFetch('/cms/learn-articles', { method: 'POST', body });
export const getCmsLearningStatus = (days = 14) =>
  intelligenceFetch(`/cms/learning-status?days=${encodeURIComponent(String(days))}`);
export const getCmsLearningSummary = (days = 5) =>
  intelligenceFetch(`/cms/learning-summary?days=${encodeURIComponent(String(days))}`);
export const getSifHealth = () => intelligenceFetch('/sif/health');
export const getSifDashboard = () => intelligenceFetch('/sif/dashboard');
export const getSifFrameworks = () => intelligenceFetch('/sif/frameworks');
export const getSifFramework = (sectorId) =>
  intelligenceFetch(`/sif/frameworks/${encodeURIComponent(sectorId)}`);
export const getSifQualityGates = () => intelligenceFetch('/sif/quality-gates');
export const analyseSif = (query, ticker, engine = 'ask_agi') => {
  const qs = new URLSearchParams({ query: query || '', engine });
  if (ticker) qs.set('ticker', ticker);
  return intelligenceFetch(`/sif/analyse?${qs}`, { method: 'POST', body: {} });
};
export const getLeoHealth = () => intelligenceFetch('/leo/health');
export const getLeoDashboard = () => intelligenceFetch('/leo/dashboard');
export const getLeoQualityGates = () => intelligenceFetch('/leo/quality-gates');
export const getLeoDossier = (ticker) =>
  intelligenceFetch(`/leo/dossier/${encodeURIComponent(ticker)}`);
export const packageLeo = (query, ticker, engine = 'ask_agi') => {
  const qs = new URLSearchParams({ query: query || '', engine });
  if (ticker) qs.set('ticker', ticker);
  return intelligenceFetch(`/leo/package?${qs}`, { method: 'POST', body: {} });
};
export const getCidHealth = () => intelligenceFetch('/company-dossier/health');
export const getCidDashboard = () => intelligenceFetch('/company-dossier');
export const getCidQualityGates = () => intelligenceFetch('/company-dossier/quality-gates');
export const getCompanyDossier = (ticker) =>
  intelligenceFetch(`/company-dossier/${encodeURIComponent(ticker)}`);
export const getCompanyDossierTimeline = (ticker, limit = 100) =>
  intelligenceFetch(`/company-dossier/${encodeURIComponent(ticker)}/timeline?limit=${limit}`);
export const getCompanyDossierCoverage = (ticker) =>
  intelligenceFetch(`/company-dossier/${encodeURIComponent(ticker)}/coverage`);
export const getCompanyDossierValuation = (ticker) =>
  intelligenceFetch(`/company-dossier/${encodeURIComponent(ticker)}/valuation`);
export const getCompanyDossierRisk = (ticker) =>
  intelligenceFetch(`/company-dossier/${encodeURIComponent(ticker)}/risk`);
export const getCompanyDossierForecast = (ticker) =>
  intelligenceFetch(`/company-dossier/${encodeURIComponent(ticker)}/forecast`);
export const getCompanyDossierDocuments = (ticker) =>
  intelligenceFetch(`/company-dossier/${encodeURIComponent(ticker)}/documents`);
export const getYfpHealth = () => intelligenceFetch('/yfp/health');
export const getYfpDashboard = () => intelligenceFetch('/yfp/dashboard');
export const getYfpQualityGates = () => intelligenceFetch('/yfp/quality-gates');
export const searchYfp = (q, limit = 8) =>
  intelligenceFetch(`/yfp/search?q=${encodeURIComponent(q || '')}&limit=${limit}`);
export const enrichYfp = (ticker) =>
  intelligenceFetch(`/yfp/enrich/${encodeURIComponent(ticker)}`, { method: 'POST', body: {} });
export const getDvcHealth = () => intelligenceFetch('/dvc/health');
export const getDvcDashboard = () => intelligenceFetch('/dvc/dashboard');
export const getDvcQualityGates = () => intelligenceFetch('/dvc/quality-gates');
export const getDvcMetrics = () => intelligenceFetch('/dvc/metrics');
export const getDvcCompany = (ticker) =>
  intelligenceFetch(`/dvc/company/${encodeURIComponent(ticker)}`);
export const getDvcConflicts = (limit = 40, severity) => {
  const qs = new URLSearchParams({ limit: String(limit) });
  if (severity) qs.set('severity', severity);
  return intelligenceFetch(`/dvc/conflicts?${qs}`);
};
export const validateDvc = (ticker) =>
  intelligenceFetch(`/dvc/validate/${encodeURIComponent(ticker)}`, { method: 'POST', body: {} });
export const enrichDvc = (ticker) =>
  intelligenceFetch(`/dvc/enrich/${encodeURIComponent(ticker)}`, { method: 'POST', body: {} });
export const getEcpHealth = () => intelligenceFetch('/ecp/health');
export const getEcpDashboard = () => intelligenceFetch('/ecp/dashboard');
export const getEcpQualityGates = () => intelligenceFetch('/ecp/quality-gates');
export const getEcpReports = (limit = 30) =>
  intelligenceFetch(`/ecp/reports?limit=${limit}`);
export const getEcpReport = (ticker) =>
  intelligenceFetch(`/ecp/report/${encodeURIComponent(ticker)}`);
export const completeEcp = (ticker, q = 'Should I buy?') => {
  const qs = new URLSearchParams({
    ticker: ticker || '',
    q: q || 'Should I buy?',
  });
  return intelligenceFetch(`/ecp/complete?${qs}`, { method: 'POST', body: {} });
};

/** Mission Control V1 — administrator operations centre (read-only) */
export const getMissionControlHealth = () => intelligenceFetch('/mission-control/health');
export const getMissionControlDashboard = () => intelligenceFetch('/mission-control/dashboard');
export const getMissionControlQualityGates = () =>
  intelligenceFetch('/mission-control/quality-gates');
export const getMissionControlReport = () => intelligenceFetch('/mission-control/report');
export const acknowledgeMissionControlAlert = (alertId) =>
  intelligenceFetch('/mission-control/acknowledge', {
    method: 'POST',
    body: { alert_id: alertId },
  });

/** Investment Office V1 — executive operating cockpit */
export const getInvestmentOfficeHealth = () => intelligenceFetch('/investment-office/health');
export const getInvestmentOfficeDashboard = () => intelligenceFetch('/investment-office/dashboard');
export const getInvestmentOfficeQualityGates = () =>
  intelligenceFetch('/investment-office/quality-gates');
export const packageInvestmentOffice = (query = '', ticker) =>
  intelligenceFetch('/investment-office/package', {
    method: 'POST',
    body: { query, ticker },
  });

/** Company Monitoring System V1 — continuous living analyst */
export const getCompanyMonitorHealth = () => intelligenceFetch('/company-monitor/health');
export const getCompanyMonitorDashboard = () => intelligenceFetch('/company-monitor/dashboard');
export const getCompanyMonitorQualityGates = () =>
  intelligenceFetch('/company-monitor/quality-gates');
export const getCompanyMonitorChanges = (ticker, limit = 40) => {
  const qs = new URLSearchParams({ limit: String(limit) });
  if (ticker) qs.set('ticker', ticker);
  return intelligenceFetch(`/company-monitor/changes?${qs}`);
};
export const getCompanyMonitorAlerts = (limit = 40) =>
  intelligenceFetch(`/company-monitor/alerts?limit=${limit}`);
export const getCompanyMonitorReviews = (limit = 40) =>
  intelligenceFetch(`/company-monitor/reviews?limit=${limit}`);
export const runCompanyMonitor = (ticker, query = '') =>
  intelligenceFetch('/company-monitor/run', {
    method: 'POST',
    body: { ticker, query: query || `Monitor ${ticker}` },
  });
export const runCompanyMonitorUniverse = (limit) =>
  intelligenceFetch('/company-monitor/run-universe', {
    method: 'POST',
    body: limit != null ? { limit } : {},
  });

/** Company Analysis Engine V1 — institutional company-specific reasoning (not Context Assembly) */
export const getCompanyAnalysisHealth = () => intelligenceFetch('/company-analysis/health');
export const getCompanyAnalysisDashboard = () => intelligenceFetch('/company-analysis/dashboard');
export const getCompanyAnalysisQualityGates = () =>
  intelligenceFetch('/company-analysis/quality-gates');
export const getCompanyAnalysisReports = (limit = 30) =>
  intelligenceFetch(`/company-analysis/reports?limit=${limit}`);
export const getCompanyAnalysisReport = (ticker) =>
  intelligenceFetch(`/company-analysis/report/${encodeURIComponent(ticker)}`);
export const analyseCompany = (ticker, query = 'Company analysis') =>
  intelligenceFetch('/company-analysis/analyse', {
    method: 'POST',
    body: { ticker, query },
  });

/** Institutional Analyst Framework V1 — specialist opinions → committee → CIO */
export const getInstitutionalAnalystsHealth = () =>
  intelligenceFetch('/institutional-analysts/health');
export const getInstitutionalAnalystsQualityGates = () =>
  intelligenceFetch('/institutional-analysts/quality-gates');

/** Investment Committee Intelligence V1 — deliberation / vote / minutes */
export const getInvestmentCommitteeHealth = () =>
  intelligenceFetch('/investment-committee/health');
export const getInvestmentCommitteeQualityGates = () =>
  intelligenceFetch('/investment-committee/quality-gates');
export const getInvestmentCommitteeTimeline = (ticker, limit = 20) =>
  intelligenceFetch(
    `/investment-committee/timeline/${encodeURIComponent(ticker)}?limit=${limit}`
  );
export const recordInvestmentCommitteeActuals = (ticker, actuals, meetingId) =>
  intelligenceFetch('/investment-committee/record-actuals', {
    method: 'POST',
    body: { ticker, actuals, meeting_id: meetingId },
  });

/** Institutional Research Writer V1 — publication writing after CIO */
export const getResearchWriterHealth = () => intelligenceFetch('/research-writer/health');
export const getResearchWriterQualityGates = () =>
  intelligenceFetch('/research-writer/quality-gates');

/** AGIB Intelligence Layer V2 — living dossier / thesis / forecast / ledger */
export const getAilHealth = () => intelligenceFetch('/ail/health');
export const getAilDashboard = () => intelligenceFetch('/ail/dashboard');
export const analyseAil = (q, ticker) => {
  const qs = new URLSearchParams({ q });
  if (ticker) qs.set('ticker', ticker);
  return intelligenceFetch(`/ail/analyse?${qs}`);
};
export const runAilMonitor = (watchlist = 'default') =>
  intelligenceFetch(`/ail/monitor/run?watchlist=${encodeURIComponent(watchlist)}`, {
    method: 'POST',
    body: {},
  });
export const getCompanyDossierAil = (ticker) =>
  intelligenceFetch(`/company/${encodeURIComponent(ticker)}/dossier`);
export const getCompanyTimelineAil = (ticker, limit = 100) =>
  intelligenceFetch(`/company/${encodeURIComponent(ticker)}/timeline?limit=${limit}`);
export const getCompanyEventsAil = (ticker, limit = 50) =>
  intelligenceFetch(`/company/${encodeURIComponent(ticker)}/events?limit=${limit}`);
export const getCompanyThesisAil = (ticker) =>
  intelligenceFetch(`/company/${encodeURIComponent(ticker)}/thesis`);
export const getCompanyForecastAil = (ticker) =>
  intelligenceFetch(`/company/${encodeURIComponent(ticker)}/forecast`);
export const getCompanyLedgerAil = (ticker) =>
  intelligenceFetch(`/company/${encodeURIComponent(ticker)}/ledger`);
export const getCompanyMonitorAil = (ticker) =>
  intelligenceFetch(`/company/${encodeURIComponent(ticker)}/monitor`);
export const getAilEvent = (id) => intelligenceFetch(`/event/${encodeURIComponent(id)}`);
export const getAilEvidence = (id) => intelligenceFetch(`/evidence/${encodeURIComponent(id)}`);
export const getAilPrediction = (id) => intelligenceFetch(`/prediction/${encodeURIComponent(id)}`);

/** Institutional Intelligence Stack — FIL → FDI → MII → EIL → PIL */
export const getInstitutionalStackHealth = () => intelligenceFetch('/institutional-stack/health');
export const getInstitutionalStackDashboard = () => intelligenceFetch('/institutional-stack/dashboard');
export const getInstitutionalStackQualityGates = () =>
  intelligenceFetch('/institutional-stack/quality-gates');
export const getInstitutionalStackCompany = (ticker, analyst = 'committee') => {
  const qs = new URLSearchParams({ analyst }).toString();
  return intelligenceFetch(`/institutional-stack/company/${encodeURIComponent(ticker)}?${qs}`);
};
export const analyseInstitutionalStack = (ticker) =>
  intelligenceFetch('/institutional-stack/analyse', { method: 'POST', body: { ticker } });
export const bootstrapInstitutionalStack = (tickers) =>
  intelligenceFetch('/institutional-stack/bootstrap', {
    method: 'POST',
    body: tickers ? { tickers } : {},
  });
export const ingestInstitutionalStack = (payload) =>
  intelligenceFetch('/institutional-stack/ingest', { method: 'POST', body: payload || {} });

/** Evidence Intelligence Layer */
export const getEilHealth = () => intelligenceFetch('/academy/evidence/health');
export const getEilDashboard = () => intelligenceFetch('/academy/evidence/dashboard');
export const getEilQualityGates = () => intelligenceFetch('/academy/evidence/quality-gates');

/** Peer Intelligence Layer */
export const getPilHealth = () => intelligenceFetch('/peer-intelligence/health');
export const getPilDashboard = () => intelligenceFetch('/peer-intelligence/dashboard');
export const getPilQualityGates = () => intelligenceFetch('/peer-intelligence/quality-gates');
export const getPilCompany = (ticker) =>
  intelligenceFetch(`/peer-intelligence/company/${encodeURIComponent(ticker)}`);
export const analysePil = (ticker) =>
  intelligenceFetch('/peer-intelligence/analyse', { method: 'POST', body: { ticker } });

/** Filing Intelligence Layer */
export const getFilHealth = () => intelligenceFetch('/filing-intelligence/health');
export const getFilDashboard = () => intelligenceFetch('/filing-intelligence/dashboard');
export const getFilQualityGates = () => intelligenceFetch('/filing-intelligence/quality-gates');
export const getFilCompany = (ticker) =>
  intelligenceFetch(`/filing-intelligence/company/${encodeURIComponent(ticker)}`);
export const analyseFil = (ticker) =>
  intelligenceFetch('/filing-intelligence/analyse', { method: 'POST', body: { ticker } });
export const ingestFil = (payload) =>
  intelligenceFetch('/filing-intelligence/ingest', { method: 'POST', body: payload || {} });

/** Filing Diff Engine */
export const getFdiHealth = () => intelligenceFetch('/filing-diff/health');
export const getFdiDashboard = () => intelligenceFetch('/filing-diff/dashboard');
export const getFdiQualityGates = () => intelligenceFetch('/filing-diff/quality-gates');
export const getFdiCompany = (ticker) =>
  intelligenceFetch(`/filing-diff/company/${encodeURIComponent(ticker)}`);
export const analyseFdi = (ticker) =>
  intelligenceFetch('/filing-diff/analyse', { method: 'POST', body: { ticker } });

/** Management Intelligence Engine */
export const getMiiHealth = () => intelligenceFetch('/management-intelligence/health');
export const getMiiDashboard = () => intelligenceFetch('/management-intelligence/dashboard');
export const getMiiQualityGates = () => intelligenceFetch('/management-intelligence/quality-gates');
export const getMiiCompany = (ticker) =>
  intelligenceFetch(`/management-intelligence/company/${encodeURIComponent(ticker)}`);
export const getMiiGuidance = (ticker) =>
  intelligenceFetch(`/management-intelligence/guidance/${encodeURIComponent(ticker)}`);
export const analyseMii = (ticker) =>
  intelligenceFetch('/management-intelligence/analyse', { method: 'POST', body: { ticker } });

/** Accounting Intelligence Engine */
export const getAciHealth = () => intelligenceFetch('/accounting-intelligence/health');
export const getAciDashboard = () => intelligenceFetch('/accounting-intelligence/dashboard');
export const getAciQualityGates = () => intelligenceFetch('/accounting-intelligence/quality-gates');
export const getAciCompany = (ticker) =>
  intelligenceFetch(`/accounting-intelligence/company/${encodeURIComponent(ticker)}`);
export const getAciHistory = (ticker) =>
  intelligenceFetch(`/accounting-intelligence/history/${encodeURIComponent(ticker)}`);
export const analyseAci = (ticker) =>
  intelligenceFetch('/accounting-intelligence/analyse', { method: 'POST', body: { ticker } });

/** Portfolio Intelligence Office */
export const getPioHealth = () => intelligenceFetch('/portfolio-intelligence/health');
export const getPioDashboard = () => intelligenceFetch('/portfolio-intelligence/dashboard');
export const getPioQualityGates = () => intelligenceFetch('/portfolio-intelligence/quality-gates');
export const getPioPortfolio = (id) =>
  intelligenceFetch(`/portfolio-intelligence/portfolio/${encodeURIComponent(id)}`);
export const getPioPortfolioHealth = (id) =>
  intelligenceFetch(`/portfolio-intelligence/health/${encodeURIComponent(id)}`);
export const getPioScenarios = (id) =>
  intelligenceFetch(`/portfolio-intelligence/scenarios/${encodeURIComponent(id)}`);
export const analysePio = (payload = {}) =>
  intelligenceFetch('/portfolio-intelligence/analyse', { method: 'POST', body: payload || {} });

/** Causal Intelligence Graph */
export const getCigHealth = () => intelligenceFetch('/causal-intelligence/health');
export const getCigDashboard = () => intelligenceFetch('/causal-intelligence/dashboard');
export const getCigQualityGates = () => intelligenceFetch('/causal-intelligence/quality-gates');
export const getCigGraph = () => intelligenceFetch('/causal-intelligence/graph');
export const getCigCompany = (ticker) =>
  intelligenceFetch(`/causal-intelligence/company/${encodeURIComponent(ticker)}`);
export const getCigEvent = (event) =>
  intelligenceFetch(`/causal-intelligence/event/${encodeURIComponent(event)}`);
export const analyseCig = (payload = {}) =>
  intelligenceFetch('/causal-intelligence/analyse', { method: 'POST', body: payload || {} });

/** Forecast Intelligence Engine */
export const getFieHealth = () => intelligenceFetch('/forecast/health');
export const getFieDashboard = () => intelligenceFetch('/forecast/dashboard');
export const getFieQualityGates = () => intelligenceFetch('/forecast/quality-gates');
export const getFieCompany = (ticker) =>
  intelligenceFetch(`/forecast/company/${encodeURIComponent(ticker)}`);
export const getFieScenarios = (ticker) =>
  intelligenceFetch(`/forecast/scenarios/${encodeURIComponent(ticker)}`);
export const getFieCatalysts = (ticker) =>
  intelligenceFetch(`/forecast/catalysts/${encodeURIComponent(ticker)}`);
export const analyseFie = (payload = {}) =>
  intelligenceFetch('/forecast/analyse', { method: 'POST', body: payload || {} });

/** Institutional Knowledge Graph */
export const getIkgHealth = () => intelligenceFetch('/knowledge-graph/health');
export const getIkgDashboard = () => intelligenceFetch('/knowledge-graph/dashboard');
export const getIkgQualityGates = () => intelligenceFetch('/knowledge-graph/quality-gates');
export const getIkgEntity = (id) =>
  intelligenceFetch(`/knowledge-graph/entity/${encodeURIComponent(id)}`);
export const getIkgCompany = (ticker) =>
  intelligenceFetch(`/knowledge-graph/company/${encodeURIComponent(ticker)}`);
export const getIkgRelationships = (id) =>
  intelligenceFetch(`/knowledge-graph/relationships/${encodeURIComponent(id)}`);
export const getIkgPath = (source, target) => {
  const qs = new URLSearchParams({ source: source || '', target: target || '' }).toString();
  return intelligenceFetch(`/knowledge-graph/path?${qs}`);
};
export const queryIkg = (payload = {}) =>
  intelligenceFetch('/knowledge-graph/query', { method: 'POST', body: payload || {} });
