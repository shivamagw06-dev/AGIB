import { API_ORIGIN } from '@/config';

const BASE = API_ORIGIN || '';

async function marketFetch(path) {
  const url = `${BASE}/api/market${path}`;
  const resp = await fetch(url, { credentials: 'include' });
  if (resp.status === 429) {
    // Rate limited — return empty so UI keeps last cached state
    console.warn('[marketApi] rate limited, using cached UI state');
    return null;
  }
  if (!resp.ok) throw new Error(`Market API error (${resp.status})`);
  return resp.json();
}

export const getMarketIntelligence = () => marketFetch('/intelligence');
export const getMarketTicker = () => marketFetch('/ticker');
export const getMarketPulse = () => marketFetch('/pulse');
export const getMarketDashboard = () => marketFetch('/dashboard');
export const getMarketBriefing = () => marketFetch('/briefing');
export const getMacroBriefing = () => marketFetch('/macro-briefing');
export const getPreMarketBriefing = () => marketFetch('/pre-market-briefing');

export async function askMacroEconomist(query) {
  const url = `${BASE}/api/market/macro-ask`;
  const resp = await fetch(url, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });
  if (!resp.ok) {
    const detail = await resp.text().catch(() => '');
    throw new Error(`Macro ask failed (${resp.status}) ${detail.slice(0, 160)}`);
  }
  return resp.json();
}