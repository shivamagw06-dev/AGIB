/**
 * Institutional Ask fallback when the Python engine is cold/OOM.
 * Uses Node AGI intelligence + market snapshot only — never fabricates prices.
 */

import { getAgiIntelligence } from './intelligenceService.js';

function asText(v, fallback = '') {
  if (v == null) return fallback;
  if (typeof v === 'string') return v.trim();
  if (typeof v === 'object' && typeof v.text === 'string') return v.text.trim();
  return String(v);
}

export async function buildAskDeskFallback(question) {
  const q = String(question || '').trim();
  let intel = null;
  try {
    intel = await getAgiIntelligence();
  } catch {
    intel = null;
  }

  const summary =
    asText(intel?.summary) ||
    asText(intel?.outlook?.summary) ||
    'AGIB research desk is warming up. Below is the latest institutional market context from the live Node intelligence gateway.';

  const sectors = Array.isArray(intel?.sectors) ? intel.sectors.slice(0, 6) : [];
  const stocks = Array.isArray(intel?.stocksInFocus) ? intel.stocksInFocus.slice(0, 6) : [];
  const indices = Array.isArray(intel?.indexSentiments) ? intel.indexSentiments.slice(0, 8) : [];

  const why = [
    summary,
    indices[0]
      ? `${indices[0].label || 'Index'}: ${indices[0].sentiment || 'monitoring'} (${indices[0].strength || 'AGI model'}).`
      : 'Index sentiment models are syncing.',
    sectors[0]
      ? `Sector focus: ${sectors[0].name || sectors[0].label || 'leadership'} remains on the institutional watchlist.`
      : 'Sector leadership will refresh with the next market cycle.',
  ].filter(Boolean);

  return {
    ok: true,
    question: q,
    mode: 'node_desk_fallback',
    degraded: true,
    retryable: true,
    providers_queried: [],
    internet_used: false,
    fabricated: false,
    executive_summary: `On “${q}”: ${summary}`,
    answer: {
      executive_summary: `On “${q}”: ${summary}`,
      summary,
      why,
      house_view_label: asText(intel?.outlook?.bias) || 'Monitoring',
    },
    why,
    market_context: {
      breadth: intel?.breadth || null,
      outlook: intel?.outlook || null,
      index_sentiments: indices,
      sectors,
      stocks_in_focus: stocks,
      disclaimer: intel?.disclaimer || 'AGI proprietary analytics · Not raw exchange data',
    },
    evidence: [
      {
        source: 'agi_node_intelligence',
        title: 'Live market intelligence gateway',
        note: 'Served while the Python research desk restarts.',
      },
    ],
    note:
      'Research desk unavailable or restarting. This is an institutional Node fallback — retry Ask AGI in a moment for the full engine brief.',
    meta: {
      surface: 'ask_fallback',
      ui_version: 'ask-desk-fallback-v1',
      generated_at: new Date().toISOString(),
    },
  };
}
