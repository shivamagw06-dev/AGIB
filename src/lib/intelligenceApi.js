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
