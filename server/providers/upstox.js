/**
 * Upstox Developer API — fundamentals / corporate actions.
 * Docs: https://upstox.com/developer/api-documentation/get-corporate-actions/
 *
 * Auth: Bearer access token from the Upstox developer dashboard (or OAuth).
 * Accepts common env aliases because operators often paste into UPSTOX_API.
 */

const UPSTOX_BASE = process.env.UPSTOX_API_BASE || 'https://api.upstox.com/v2';

async function ensureFetch() {
  if (typeof globalThis.fetch === 'function') return globalThis.fetch.bind(globalThis);
  const mod = await import('node-fetch');
  return mod.default;
}

function firstEnv(...keys) {
  for (const key of keys) {
    const value = String(process.env[key] || '').trim();
    if (value) return { key, value };
  }
  return { key: null, value: '' };
}

/** Access token used as Authorization: Bearer … */
export function resolveUpstoxAccessToken() {
  // Prefer explicit access-token names, then common misnames (UPSTOX_API).
  const hit = firstEnv(
    'UPSTOX_ACCESS_TOKEN',
    'UPSTOX_TOKEN',
    'UPSTOX_API',
    'UPSTOX_API_TOKEN',
    'UPSTOX_API_KEY' // only if someone pasted the daily token into API_KEY
  );
  if (!hit.value) return { token: '', source: null };

  // If UPSTOX_API / UPSTOX_API_KEY looks like a short client_id (not a token),
  // do not treat it as a Bearer token — corporate-actions needs the access token.
  if (
    (hit.key === 'UPSTOX_API' || hit.key === 'UPSTOX_API_KEY') &&
    hit.value.length < 40 &&
    !hit.value.includes('.')
  ) {
    return { token: '', source: hit.key, likely_client_id: true };
  }

  return { token: hit.value, source: hit.key, likely_client_id: false };
}

export function upstoxEnvPresence() {
  const keys = [
    'UPSTOX_ACCESS_TOKEN',
    'UPSTOX_TOKEN',
    'UPSTOX_API',
    'UPSTOX_API_TOKEN',
    'UPSTOX_API_KEY',
    'UPSTOX_API_SECRET',
    'UPSTOX_CLIENT_ID',
    'UPSTOX_CLIENT_SECRET',
    'UPSTOX_REDIRECT_URI',
  ];
  const present = {};
  for (const key of keys) {
    present[key] = Boolean(String(process.env[key] || '').trim());
  }
  return present;
}

export function isUpstoxConfigured() {
  const { token } = resolveUpstoxAccessToken();
  return Boolean(token);
}

async function upstoxGet(path) {
  const { token, source, likely_client_id } = resolveUpstoxAccessToken();
  if (!token) {
    if (likely_client_id) {
      throw new Error(
        `Upstox env ${source} looks like a client_id/API key, not an access token. ` +
          'Set UPSTOX_ACCESS_TOKEN to the Bearer token from the Upstox developer app (Generate token).'
      );
    }
    throw new Error(
      'Upstox auth missing: set UPSTOX_ACCESS_TOKEN (Bearer token). ' +
        'API key/secret alone cannot call corporate-actions.'
    );
  }

  const fetchFn = await ensureFetch();
  const url = `${UPSTOX_BASE}${path}`;
  const resp = await fetchFn(url, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
      Authorization: `Bearer ${token}`,
    },
  });

  const json = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    const msg =
      json?.errors?.[0]?.message ||
      json?.message ||
      json?.error ||
      `Upstox HTTP ${resp.status}`;
    const err = new Error(String(msg));
    err.status = resp.status;
    err.body = json;
    throw err;
  }
  return json;
}

/**
 * GET /fundamentals/{isin}/corporate-actions
 * @param {string} isin e.g. INE002A01018 (Reliance)
 */
export async function getCorporateActions(isin) {
  const clean = String(isin || '').trim().toUpperCase();
  if (!/^INE[A-Z0-9]{9}$/.test(clean) && !/^[A-Z]{2}[A-Z0-9]{9,12}$/.test(clean)) {
    throw new Error(`Invalid ISIN: ${isin}`);
  }
  return upstoxGet(`/fundamentals/${encodeURIComponent(clean)}/corporate-actions`);
}
