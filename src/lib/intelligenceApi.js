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
export const createResearchRun = (payload) =>
  intelligenceFetch('/research/runs', { method: 'POST', body: payload });
export const getResearchRun = (runId) =>
  intelligenceFetch(`/research/runs/${encodeURIComponent(runId)}`);
export const listResearchRuns = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return intelligenceFetch(`/research/runs${qs ? `?${qs}` : ''}`);
};

/** Optional workspace endpoint — may 404 on older engines; callers must catch. */
export const createResearchWorkspace = (payload) =>
  intelligenceFetch('/research/workspace', { method: 'POST', body: payload });
export const getResearchWorkspace = (runId) =>
  intelligenceFetch(`/research/workspace/${encodeURIComponent(runId)}`);

export const copilotChat = (payload) =>
  intelligenceFetch('/copilot/chat', { method: 'POST', body: payload });

export const getSimilarCompanies = (symbol, params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return intelligenceFetch(
    `/comparison/similar/${encodeURIComponent(symbol)}${qs ? `?${qs}` : ''}`,
  );
};

export const getValidationDashboard = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return intelligenceFetch(`/analytics/validation${qs ? `?${qs}` : ''}`);
};

export const listWatchlists = () => intelligenceFetch('/watchlists');

/**
 * Create a research run and poll until complete (or timeout).
 * Works with the current engine that only exposes /research/runs.
 */
export async function runAndWait(payload, { timeoutMs = 90_000, intervalMs = 1200 } = {}) {
  const created = await createResearchRun(payload);
  const runId = created?.run_id || created?.runId;
  if (!runId) return created;
  const started = Date.now();
  let current = created;
  while (Date.now() - started < timeoutMs) {
    const status = String(current?.status || '').toLowerCase();
    if (['completed', 'partial', 'failed'].includes(status)) return current;
    await new Promise((r) => setTimeout(r, intervalMs));
    current = await getResearchRun(runId);
  }
  return current;
}
