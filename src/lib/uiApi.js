/**
 * Client facade for UI Aggregation Layer.
 * Browser → /api/ui/* (Express) → /v1/ui/* (intelligence-engine).
 * Never call engines directly from the frontend.
 */

import { API_ORIGIN } from '@/config';

const BASE = API_ORIGIN || '';

async function uiFetch(path, { method = 'GET', body, query } = {}) {
  const qs = query ? `?${new URLSearchParams(query).toString()}` : '';
  const url = `${BASE}/api/ui${path}${qs}`;
  const resp = await fetch(url, {
    method,
    credentials: 'include',
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!resp.ok) {
    const detail = await resp.text().catch(() => '');
    throw new Error(`UI API error (${resp.status}) ${detail.slice(0, 180)}`);
  }
  return resp.json();
}

export const getUiHealth = () => uiFetch('/health');
export const getUiHome = () => uiFetch('/home');
export const getUiDashboard = () => uiFetch('/dashboard');
export const getUiMacro = () => uiFetch('/macro');
export const getUiPortfolio = () => uiFetch('/portfolio');
export const getUiWorkflow = () => uiFetch('/workflow');
export const getUiCompany = (ticker) => uiFetch(`/company/${encodeURIComponent(ticker)}`);
export const getUiResearch = (id) => uiFetch(`/research/${encodeURIComponent(id)}`);
export const getUiTheme = (id) => uiFetch(`/theme/${encodeURIComponent(id)}`);
export const getUiSector = (id) => uiFetch(`/sector/${encodeURIComponent(id)}`);
export const getUiArticle = (id, ticker) =>
  uiFetch(`/article/${encodeURIComponent(id)}`, ticker ? { query: { ticker } } : undefined);
export const getUiTimeline = (entity) => uiFetch(`/timeline/${encodeURIComponent(entity)}`);
export const getUiAutocomplete = (q) => uiFetch('/autocomplete', { query: { q: q || '' } });
export const getUiCopilot = (params = {}) => uiFetch('/copilot', { query: params });
export const postUiSearch = (question, ticker) =>
  uiFetch('/search', {
    method: 'POST',
    body: { question, ticker },
  });
