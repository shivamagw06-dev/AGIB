/**
 * Project mapSearchPack → chat-first AGIB answer model.
 * Direct answer first; deeper layers on demand.
 */

import { mapSearchPack } from './mapSearchPack';

function asList(v, n = 8) {
  if (!Array.isArray(v)) return [];
  return v.map((x) => (typeof x === 'string' ? x : x?.text || x?.title || x?.label || '')).filter(Boolean).slice(0, n);
}

function impactFromLabel(label = '', text = '') {
  const blob = `${label} ${text}`.toLowerCase();
  if (/risk|bear|weak|pressure|concern|negative|impair/.test(blob)) return 'Medium';
  if (/neutral|mixed|watch|monitor/.test(blob)) return 'Neutral';
  if (/positive|bull|strong|growth|quality|catalyst|expand/.test(blob)) return 'Positive';
  return 'Neutral';
}

function institutionalViewLabel(stance = '', recommendation = '') {
  const s = `${stance} ${recommendation}`.toLowerCase();
  if (/buy|overweight|constructive|bullish|accumulate/.test(s)) return 'Constructive';
  if (/sell|underweight|cautious|bearish|avoid|reduce/.test(s)) return 'Cautious';
  if (/monitor|hold|neutral|selective|watch/.test(s)) return 'Monitoring';
  return stance || 'Monitoring';
}

function scoreTone(impact) {
  if (impact === 'Positive') return 'pos';
  if (impact === 'Medium' || impact === 'Negative') return 'neg';
  return 'neu';
}

/**
 * @param {object|null} pack raw /api/ui/search pack
 */
export function mapChatAnswer(pack) {
  const vm = mapSearchPack(pack || {});
  if (!vm) return null;

  const view = institutionalViewLabel(
    vm.stance || vm.institutionalView?.stance || '',
    vm.institutionalAnswer?.recommendation || vm.decisionEngine?.action || ''
  );

  const thesisCards = [
    {
      id: 'business',
      title: 'Business Quality',
      body:
        asList([vm.businessQuality, vm.businessModel, vm.whyCards?.find((c) => c.key === 'demand')?.text])[0] ||
        vm.why?.[0] ||
        'Business quality is assessed through franchise durability, incremental returns and competitive position.',
      impact: impactFromLabel('business', vm.businessQuality || ''),
    },
    {
      id: 'growth',
      title: 'Growth Outlook',
      body:
        asList([vm.whyCards?.find((c) => c.key === 'demand')?.text, vm.sectorNarrative, vm.macroNarrative])[0] ||
        'Growth should be judged through volume, pricing/mix and adjacency — not headline revenue alone.',
      impact: impactFromLabel('growth', vm.sectorNarrative || ''),
    },
    {
      id: 'financial',
      title: 'Financial Quality',
      body:
        asList([vm.financialNarrative, vm.whyCards?.find((c) => c.key === 'financial')?.text])[0] ||
        'Financial quality emphasises cash conversion, incremental returns and balance-sheet resilience.',
      impact: impactFromLabel('financial', vm.financialNarrative || ''),
    },
    {
      id: 'valuation',
      title: 'Valuation',
      body:
        asList([vm.valuationNarrative, vm.whyCards?.find((c) => c.key === 'valuation')?.text])[0] ||
        'Valuation only works when growth durability and competitive position are held constant.',
      impact: impactFromLabel('valuation', vm.valuationNarrative || 'neutral'),
    },
    {
      id: 'competition',
      title: 'Competition',
      body:
        asList([vm.whyCards?.find((c) => c.key === 'competition')?.text, vm.sectorDrivers?.[0]])[0] ||
        'Competitive position decides whether growth creates value or is competed away.',
      impact: impactFromLabel('competition', ''),
    },
    {
      id: 'risk',
      title: 'Risk',
      body:
        asList([vm.risks?.[0]?.risk, vm.whyCards?.find((c) => c.key === 'risk')?.text])[0] ||
        'Institutional risk framing emphasises what can impair the thesis before the base case arrives.',
      impact: 'Medium',
    },
    {
      id: 'catalysts',
      title: 'Catalysts',
      body:
        asList(vm.catalysts)[0] ||
        asList(vm.bull)[0] ||
        'Catalysts are the observable events that would raise or reduce conviction.',
      impact: 'Positive',
    },
  ].map((c) => ({ ...c, tone: scoreTone(c.impact) }));

  const moreBullish = asList(
    [
      ...(vm.bull || []),
      ...(vm.catalysts || []),
      'Margin expansion',
      'Cash generation',
      'Lower valuation',
      'Better execution',
      'Stronger guidance',
    ],
    6
  );

  const moreBearish = asList(
    [
      ...(vm.bear || []),
      ...(vm.risks || []).map((r) => (typeof r === 'string' ? r : r.risk)),
      'Margin pressure',
      'Weak demand',
      'Regulatory risk',
      'Competition',
      'Capital allocation concerns',
    ],
    6
  );

  const intelligenceChips = [
    { id: 'company', label: 'Company Intelligence', section: 'business' },
    { id: 'research', label: 'Research Intelligence', section: 'thesis' },
    { id: 'financial', label: 'Financial Intelligence', section: 'financial' },
    { id: 'sector', label: 'Sector Intelligence', section: 'sector' },
    { id: 'market', label: 'Market Intelligence', section: 'market' },
    { id: 'macro', label: 'Macro Intelligence', section: 'macro' },
    { id: 'historical', label: 'Historical Intelligence', section: 'changed' },
    { id: 'forecast', label: 'Forecast Intelligence', section: 'scenarios' },
  ];

  const scores = {
    business: vm.kpis?.find((k) => /business|quality/i.test(k.label))?.value || null,
    financial: vm.kpis?.find((k) => /financial|cash|roe/i.test(k.label))?.value || null,
    growth: vm.kpis?.find((k) => /growth|momentum/i.test(k.label))?.value || null,
    valuation: vm.kpis?.find((k) => /valuation|multiple/i.test(k.label))?.value || null,
    risk: vm.risks?.[0]?.severity || vm.risks?.[0]?.impact || 'Watch',
    conviction: vm.conviction || view,
  };

  const followUps = asList(
    [
      ...(vm.explore || []),
      `Why ${view}?`,
      vm.ticker ? `Compare ${vm.ticker} with peers` : 'Show peer comparison',
      'Show valuation',
      'Show financials',
      'Latest earnings',
      'What changed?',
      'Bull vs Bear case',
      'Show risks',
      'Portfolio impact',
    ],
    10
  );

  const recentResearch = asList(
    [
      ...(vm.supporting || []).map((s) => s.title || s.source || s),
      'Internal AGIB',
      'Exchange Filing',
    ],
    4
  );

  const directAnswer =
    vm.institutionalAnswer?.text ||
    vm.executive ||
    vm.conclusion ||
    'AGIB is assembling institutional intelligence for this question.';

  return {
    question: vm.question,
    ticker: vm.ticker,
    company: vm.intelligenceLayer?.company || vm.ticker || null,
    intent: vm.intent,
    category: vm.category,
    directAnswer,
    horizon: vm.horizon || vm.institutionalAnswer?.horizon || '12–24 Months',
    confidence: vm.confidence ?? 72,
    institutionalView: view,
    stanceTone: vm.stanceTone || (view === 'Constructive' ? 'pos' : view === 'Cautious' ? 'neg' : 'neu'),
    thesisCards,
    moreBullish,
    moreBearish,
    intelligenceChips,
    scores,
    followUps,
    recentResearch,
    freshness: vm.freshness,
    lastUpdated: vm.lastUpdated,
    // deep layers for progressive disclosure
    deep: {
      thesis: vm.thesis,
      why: vm.why,
      financialNarrative: vm.financialNarrative,
      valuationNarrative: vm.valuationNarrative,
      sectorNarrative: vm.sectorNarrative,
      macroNarrative: vm.macroNarrative,
      marketNarrative: vm.marketNarrative,
      bull: vm.bull,
      base: vm.base,
      bear: vm.bear,
      risks: vm.risks,
      catalysts: vm.catalysts,
      conclusion: vm.conclusion,
      whatChanged: vm.whatChanged,
      recommendationStatus: vm.recommendationStatus,
      askSlim: pack?.degradation?.ask_slim,
      degraded: Boolean(pack?.degraded || pack?.mode === 'node_desk_fallback'),
    },
  };
}
