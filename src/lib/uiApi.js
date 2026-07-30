/**
 * Client facade for UI Aggregation Layer.
 * Browser → /api/ui/* (Express) → /v1/ui/* (intelligence-engine).
 * Never call engines directly from the frontend.
 */

import { API_ORIGIN } from '@/config';
import { hydrateHomeFromMarketApis } from '@/office/homeDeskFallback';

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
  const contentType = resp.headers.get('content-type') || '';
  const text = await resp.text().catch(() => '');
  if (!resp.ok) {
    throw new Error(`UI API error (${resp.status}) ${text.slice(0, 180)}`);
  }
  // Hostinger SPA fallback can return index.html with 200 for unknown /api paths.
  if (!contentType.includes('application/json') && text.trim().startsWith('<')) {
    throw new Error(`UI API returned HTML instead of JSON for ${path}`);
  }
  try {
    return text ? JSON.parse(text) : null;
  } catch {
    throw new Error(`UI API invalid JSON for ${path}`);
  }
}

export const getUiHealth = () => uiFetch('/health');

/** Home: prefer /api/ui/home, else hydrate from working /api/market/* desks. */
export async function getUiHome() {
  try {
    return await uiFetch('/home');
  } catch (uiError) {
    try {
      return await hydrateHomeFromMarketApis(BASE);
    } catch {
      throw uiError;
    }
  }
}
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
export const getUiPredictions = () => uiFetch('/predictions');
export const getUiCalendar = () => uiFetch('/calendar');
export const getUiCopilot = (params = {}) => uiFetch('/copilot', { query: params });
export async function postUiSearch(question, ticker) {
  try {
    return await uiFetch('/search', {
      method: 'POST',
      body: { question, ticker },
    });
  } catch (err) {
    const msg = String(err?.message || '');
    const retryable = /503|502|research_desk_unavailable|timed out|unavailable/i.test(msg);
    if (!retryable) throw err;
    // One wake/retry — give the engine a moment after the gateway wake probe.
    await new Promise((r) => setTimeout(r, 2500));
    return uiFetch('/search', {
      method: 'POST',
      body: { question, ticker },
    });
  }
}
