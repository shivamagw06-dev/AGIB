/**
 * Institutional Ask fallback when the Python engine is cold/OOM.
 * Uses Node AGI intelligence + market snapshot only — never fabricates prices.
 * Shapes output with Response Constitution v1.0 section order when possible.
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
  const bias = asText(intel?.outlook?.bias) || 'Monitoring';

  // Honest unavailable posture — do NOT pretend the market blurb answers the research question.
  const directAnswer =
    `AGIB could not complete a research answer for “${q}” because the intelligence engine did not respond in time. ` +
    `This is not a finished company or macro brief. Retry Ask in a moment. ` +
    `While the desk recovers, live market context reads: ${summary}`;
  const why = [
    'Node gateway fallback: the Python research engine timed out, returned 5xx/HTML, or was unreachable.',
    'No company-level evidence pack was retrieved for this question on the fallback path.',
    indices[0]
      ? `${indices[0].label || 'Index'} currently reads ${indices[0].sentiment || 'mixed'} (${indices[0].strength || 'AGI model'}) — market context only.`
      : 'Index sentiment models are syncing; treat this as market context, not a research conclusion.',
    sectors[0]
      ? `Sector tape focus: ${sectors[0].name || sectors[0].label || 'leadership'} (not evidence for the asked question).`
      : 'Sector leadership will refresh with the next market cycle.',
  ].filter(Boolean);

  const bull = stocks[0]
    ? [`Names in focus such as ${stocks[0].name || stocks[0].symbol || 'leaders'} stay on the institutional watchlist because liquidity and attention are concentrated there.`]
    : ['A clearer risk-on tape would support cyclical and growth leadership if earnings hold up.'];
  const bear = [
    'Because the full company evidence pack is offline, any single-name conclusion would be too thin — investors should treat this as market context, not a finished thesis.',
  ];

  const bottomLine =
    `Bottom line: AGIB can share live market context while the research desk restarts, but confidence is limited until company-level evidence returns. ` +
    `Current desk bias reads ${bias}. Retry Ask AGI in a moment for the full constitution-shaped brief.`;

  const confidenceExplanation =
    'AGIB has limited confidence (45%) because this answer uses the Node market gateway while the Python research desk is unavailable.';

  const followUps = [
    'Retry the full research desk',
    'Market outlook tomorrow',
    'Which sectors are in focus?',
    'What is driving index sentiment?',
  ];

  const responseConstitution = {
    enabled: true,
    version: '1.0',
    programme: 'AGIB Response Constitution — Human First Institutional Research',
    section_order: [
      'direct_answer',
      'why_agib_thinks_this',
      'investment_thesis',
      'bull_vs_bear',
      'bottom_line',
      'supporting_intelligence',
      'suggested_follow_ups',
    ],
    direct_answer: directAnswer,
    why_agib_thinks_this: why,
    investment_thesis: {
      business: 'Company-level business detail will return when the research desk is warm.',
      growth: 'Near-term growth debate is being framed through live sector and index context only.',
      financial_quality: 'Financial statements are not available in this fallback path.',
      valuation: 'Valuation conclusions are withheld until the full engine reloads evidence.',
      risks: bear[0],
      catalysts: 'A successful desk restart and the next earnings/news cycle are the main checkpoints.',
    },
    bull_vs_bear: { bull_case: bull, bear_case: bear },
    bottom_line: bottomLine,
    supporting_intelligence: {
      layers: ['Market Intelligence', 'Sector Intelligence'],
      evidence_notes: why,
    },
    suggested_follow_ups: followUps,
    confidence: { score: 45, explanation: confidenceExplanation },
    voice: 'human_first_institutional_research',
    degraded: true,
  };

  return {
    ok: true,
    question: q,
    mode: 'node_desk_fallback',
    degraded: true,
    retryable: true,
    status: 'degraded',
    intent: 'unavailable',
    entities: { ticker: null, companies: [] },
    providers_queried: [],
    internet_used: false,
    fabricated: false,
    executive_summary: directAnswer,
    confidence: 45,
    ask_orchestration: {
      engine_reached: false,
      fallback: true,
      reason: 'node_desk_fallback',
    },
    answer: {
      executive_summary: directAnswer,
      summary,
      why,
      house_view_label: bias,
      bottom_line: bottomLine,
      confidence_explanation: confidenceExplanation,
      response_constitution: responseConstitution,
      answer_structure: 'response_constitution_v1',
    },
    why,
    bull_case: bull,
    bear_case: bear,
    follow_up_questions: followUps,
    answer_construction: {
      enabled: true,
      executive: directAnswer,
      why,
      bottom_line: bottomLine,
      confidence_explanation: confidenceExplanation,
      response_constitution: responseConstitution,
      answer_structure: 'response_constitution_v1',
    },
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
