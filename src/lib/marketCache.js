/** Client-side market intelligence cache — 30 min refresh window */
export const MARKET_REFRESH_MS = 30 * 60 * 1000;

// Versioned after adding the index-sentiment payload; prevents an old session
// cache from masking the newly deployed model fields for another refresh cycle.
const STORAGE_KEY = 'agi_market_intelligence_v2';
const STORAGE_TS_KEY = 'agi_market_intelligence_v2_ts';

export function readMarketCache() {
  try {
    const ts = Number(sessionStorage.getItem(STORAGE_TS_KEY));
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw || !ts || Date.now() - ts >= MARKET_REFRESH_MS) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function writeMarketCache(data) {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    sessionStorage.setItem(STORAGE_TS_KEY, String(Date.now()));
  } catch {
    /* quota / private mode */
  }
}

export function msUntilNextRefresh() {
  try {
    const ts = Number(sessionStorage.getItem(STORAGE_TS_KEY));
    if (!ts) return 0;
    const remaining = MARKET_REFRESH_MS - (Date.now() - ts);
    return remaining > 0 ? remaining : 0;
  } catch {
    return 0;
  }
}
