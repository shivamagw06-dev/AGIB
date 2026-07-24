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
