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
