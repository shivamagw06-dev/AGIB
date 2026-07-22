import { API_ORIGIN } from '@/config';

const BASE = API_ORIGIN || '';

async function marketFetch(path) {
  const url = `${BASE}/api/market${path}`;
  const resp = await fetch(url, { credentials: 'include' });
  if (!resp.ok) throw new Error(`Market API error (${resp.status})`);
  return resp.json();
}

export const getMarketIntelligence = () => marketFetch('/intelligence');
export const getMarketTicker = () => marketFetch('/ticker');
export const getMarketPulse = () => marketFetch('/pulse');
export const getMarketDashboard = () => marketFetch('/dashboard');
