/**
 * Upstox API health — probes corporate-actions for a known ISIN.
 * Never returns secrets; returns a short public-data sample on success.
 */

import {
  getCorporateActions,
  isUpstoxConfigured,
  resolveUpstoxAccessToken,
  upstoxEnvPresence,
} from '../providers/upstox.js';

const DEFAULT_ISIN = 'INE002A01018'; // Reliance Industries

function detailMap(event) {
  const out = {};
  for (const row of event?.event_details || []) {
    if (row?.name) out[String(row.name)] = row.value ?? null;
  }
  return out;
}

function sanitizeEvents(payload, limit = 5) {
  const rows = Array.isArray(payload?.data) ? payload.data : [];
  return {
    status: payload?.status || null,
    count: rows.length,
    sample: rows.slice(0, limit).map((ev) => {
      const details = detailMap(ev);
      return {
        name: ev?.name ?? null,
        expiry_date: ev?.expiry_date ?? null,
        amount: ev?.amount ?? null,
        ratio: ev?.ratio ?? null,
        announcement_date: details['Announcement date'] ?? null,
        ex_date: details['Ex dividend date'] || details['Ex-date'] || details['Ex date'] || null,
        record_date: details['Record date'] ?? null,
        details: details.Details || details.details || null,
      };
    }),
  };
}

export async function getUpstoxHealth(opts = {}) {
  const isin = String(opts.isin || DEFAULT_ISIN).trim().toUpperCase();
  const env = upstoxEnvPresence();
  const resolved = resolveUpstoxAccessToken();
  const configured = isUpstoxConfigured();

  const base = {
    provider: 'upstox',
    configured,
    authSource: resolved.source,
    likelyClientIdOnly: Boolean(resolved.likely_client_id),
    envPresent: env,
    isin,
    checkedAt: new Date().toISOString(),
    docs: 'https://upstox.com/developer/api-documentation/get-corporate-actions/',
  };

  if (!configured) {
    return {
      ...base,
      ok: false,
      message: resolved.likely_client_id
        ? `Env ${resolved.source} looks like client_id — also set UPSTOX_ACCESS_TOKEN (Bearer).`
        : 'Set UPSTOX_ACCESS_TOKEN on Render (finance-news-backend). Optional aliases: UPSTOX_TOKEN, UPSTOX_API (if value is the access token).',
      corporate_actions: null,
    };
  }

  try {
    const raw = await getCorporateActions(isin);
    const corporate_actions = sanitizeEvents(raw);
    return {
      ...base,
      ok: corporate_actions.status === 'success' || corporate_actions.count > 0,
      message:
        corporate_actions.count > 0
          ? `Pulled ${corporate_actions.count} corporate-action event(s) for ${isin}`
          : `Upstox returned success but zero events for ${isin}`,
      corporate_actions,
    };
  } catch (err) {
    return {
      ...base,
      ok: false,
      message: err?.message || 'Upstox corporate-actions failed',
      httpStatus: err?.status || null,
      corporate_actions: null,
    };
  }
}
