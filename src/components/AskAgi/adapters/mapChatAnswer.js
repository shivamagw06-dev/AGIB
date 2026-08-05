/**
 * Project mapSearchPack → chat-first AGIB answer model.
 * Layered stack:
 * Response Constitution (shape) → Ask Intelligence Constitution → Playbook Framework (journey).
 */

import { mapSearchPack } from './mapSearchPack';
import {
  enrichJourneyMap,
  getResearchJourneyState,
  mergeResearchJourneyState,
} from '@/lib/researchJourney';

function asList(v, n = 8) {
  if (!Array.isArray(v)) return [];
  return v
    .map((x) => (typeof x === 'string' ? x : x?.text || x?.title || x?.label || x?.risk || ''))
    .filter(Boolean)
    .slice(0, n);
}

function impactFromLabel(label = '', text = '') {
  const blob = `${label} ${text}`.toLowerCase();
  if (/risk|bear|weak|pressure|concern|negative|impair|cautious/.test(blob)) return 'Watch';
  if (/neutral|mixed|watch|monitor|balanced/.test(blob)) return 'Balanced';
  if (/positive|bull|strong|growth|quality|catalyst|expand|constructive/.test(blob)) return 'Supportive';
  return 'Balanced';
}

function institutionalViewLabel(stance = '', recommendation = '') {
  const s = `${stance} ${recommendation}`.toLowerCase();
  if (/buy|overweight|constructive|bullish|accumulate/.test(s)) return 'Constructive';
  if (/sell|underweight|cautious|bearish|avoid|reduce/.test(s)) return 'Cautious';
  if (/monitor|hold|neutral|selective|watch|withheld|insufficient/.test(s)) return 'Monitoring';
  return stance || 'Monitoring';
}

function scoreTone(impact) {
  if (impact === 'Supportive' || impact === 'Positive') return 'pos';
  if (impact === 'Watch' || impact === 'Medium' || impact === 'Negative') return 'neg';
  return 'neu';
}

function explainConfidenceFallback(confidence, view) {
  const pct = Number(confidence);
  if (!Number.isFinite(pct)) {
    return 'AGIB confidence is still forming because coverage and valuation evidence are incomplete for a firmer view.';
  }
  if (pct >= 80) {
    return `AGIB has high confidence (${pct}%) because the business picture is relatively clear and the main risks are identifiable.`;
  }
  if (pct >= 60) {
    return `AGIB has moderate confidence (${pct}%) because the business fundamentals are readable, but future earnings and valuation still leave room for surprise.`;
  }
  if (pct >= 40) {
    return `AGIB has limited confidence (${pct}%) because some important evidence is still thin or conflicting — current view: ${view}.`;
  }
  return `AGIB has low confidence (${pct}%) because validated coverage is insufficient for a firm institutional view.`;
}

/**
 * @param {object|null} pack raw /api/ui/search pack
 */
export function mapChatAnswer(pack) {
  const vm = mapSearchPack(pack || {});
  if (!vm) return null;

  const rc = vm.responseConstitution || pack?.answer_construction?.response_constitution || null;
  const aic =
    vm.askIntelligenceConstitution ||
    pack?.answer_construction?.ask_intelligence_constitution ||
    pack?.answer?.ask_intelligence_constitution ||
    null;
  const aicSections = aic?.sections || {};
  const investmentContext = aicSections.investment_context || aic?.intent || null;
  const ipf =
    vm.institutionalPlaybookFramework ||
    pack?.answer_construction?.institutional_playbook_framework ||
    pack?.answer?.institutional_playbook_framework ||
    null;
  const playbook = ipf?.playbook || null;
  const ticker = vm.ticker;
  const playbookKey = playbook?.playbook_key || 'investment_assessment';

  let journeyState = vm.researchJourneyState || ipf?.research_journey_state || null;
  if (journeyState) {
    journeyState = mergeResearchJourneyState(ticker, playbookKey, journeyState);
  } else {
    journeyState = getResearchJourneyState(ticker, playbookKey);
  }
  const journeyRaw = vm.researchJourney || ipf?.research_journey || null;
  const researchJourney = enrichJourneyMap(journeyRaw, journeyState) || journeyRaw;

  const view = institutionalViewLabel(
    vm.stance || vm.institutionalView?.stance || '',
    vm.institutionalAnswer?.recommendation || vm.decisionEngine?.action || ''
  );

  const thesisSrc = rc?.investment_thesis || {};
  const thesisCards = [
    {
      id: 'business',
      title: 'Business',
      body:
        thesisSrc.business ||
        asList([vm.businessQuality, vm.businessModel, vm.whyCards?.find((c) => c.key === 'demand')?.text])[0] ||
        vm.why?.[0] ||
        'What the company does, why customers choose it, and whether that advantage can last.',
      impact: impactFromLabel('business', thesisSrc.business || vm.businessQuality || ''),
    },
    {
      id: 'growth',
      title: 'Growth',
      body:
        thesisSrc.growth ||
        asList([vm.whyCards?.find((c) => c.key === 'demand')?.text, vm.sectorNarrative, vm.macroNarrative])[0] ||
        'Where future growth could come from — and what could slow it down.',
      impact: impactFromLabel('growth', thesisSrc.growth || vm.sectorNarrative || ''),
    },
    {
      id: 'financial',
      title: 'Financial Quality',
      body:
        thesisSrc.financial_quality ||
        asList([vm.financialNarrative, vm.whyCards?.find((c) => c.key === 'financial')?.text])[0] ||
        'Whether the company is making real cash and whether its balance sheet can handle stress.',
      impact: impactFromLabel('financial', thesisSrc.financial_quality || vm.financialNarrative || ''),
    },
    {
      id: 'valuation',
      title: 'Valuation',
      body:
        thesisSrc.valuation ||
        asList([vm.valuationNarrative, vm.whyCards?.find((c) => c.key === 'valuation')?.text])[0] ||
        'Whether the share price already assumes strong future results — and compared with what.',
      impact: impactFromLabel('valuation', thesisSrc.valuation || vm.valuationNarrative || 'neutral'),
    },
    {
      id: 'risk',
      title: 'Risks',
      body:
        thesisSrc.risks ||
        asList([vm.risks?.[0]?.risk, vm.whyCards?.find((c) => c.key === 'risk')?.text])[0] ||
        'What could make this investment go wrong — and why those risks matter.',
      impact: 'Watch',
    },
    {
      id: 'catalysts',
      title: 'Catalysts',
      body:
        thesisSrc.catalysts ||
        asList(vm.catalysts)[0] ||
        asList(vm.bull)[0] ||
        'Upcoming events that could raise or reduce AGIB’s conviction — explained in plain English.',
      impact: 'Supportive',
    },
  ].map((c) => ({ ...c, tone: scoreTone(c.impact) }));

  const moreBullish = asList(
    [
      ...(rc?.bull_vs_bear?.bull_case || []),
      ...(vm.bull || []),
      ...(vm.catalysts || []),
    ],
    6
  );
  if (!moreBullish.length) {
    moreBullish.push(
      'Demand keeps compounding without needing ever-higher spending to win customers',
      'Cash generation improves so the company depends less on external capital'
    );
  }

  const moreBearish = asList(
    [
      ...(rc?.bull_vs_bear?.bear_case || []),
      ...(vm.bear || []),
      ...(vm.risks || []).map((r) => (typeof r === 'string' ? r : r.risk)),
    ],
    6
  );
  if (!moreBearish.length) {
    moreBearish.push(
      'Investors already expect a lot — so a small disappointment could pressure the share price',
      'Competition or regulation could slow growth faster than the business can adapt'
    );
  }

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

  const directAnswer =
    aicSections.executive_summary ||
    rc?.direct_answer ||
    vm.institutionalAnswer?.text ||
    vm.executive ||
    vm.conclusion ||
    'AGIB is assembling institutional intelligence for this question.';

  const researchConclusion =
    vm.researchConclusion ||
    pack?.answer?.research_conclusion ||
    aicSections.research_conclusion ||
    null;

  const questionsBeforeYouDecide = asList(
    vm.questionsBeforeYouDecide ||
      pack?.answer?.questions_before_you_decide ||
      aicSections.questions_before_you_decide ||
      researchConclusion?.key_questions_remaining,
    8
  );

  const institutionalThinkingFramework = aic?.institutional_thinking_framework || null;

  const followUps = asList(
    [
      ...(vm.suggestedNextResearch || []),
      ...questionsBeforeYouDecide,
      ...(rc?.suggested_follow_ups || []),
      ...(vm.explore || []),
      researchJourney?.next_step ? `Continue: ${researchJourney.next_step}` : null,
      `Why ${view}?`,
      vm.ticker ? `Compare ${vm.ticker} with peers` : 'Show peer comparison',
      'Explain the valuation in plain English',
      'Show financials',
      'Latest earnings',
      'What changed?',
      'Bull vs Bear case',
      'Show risks',
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

  const whyAgib = asList(rc?.why_agib_thinks_this?.length ? rc.why_agib_thinks_this : vm.why, 5);

  const bottomLine =
    rc?.bottom_line ||
    vm.bottomLine ||
    vm.conclusion ||
    directAnswer;

  const confidence = vm.confidence ?? rc?.confidence?.score ?? 72;
  const confidenceExplanation =
    rc?.confidence?.explanation ||
    vm.confidenceExplanation ||
    explainConfidenceFallback(confidence, view);

  return {
    question: vm.question,
    ticker: vm.ticker,
    company: vm.intelligenceLayer?.company || vm.ticker || rc?.company || null,
    intent: vm.intent,
    category: vm.category,
    directAnswer,
    whyAgib,
    bottomLine,
    horizon: vm.horizon || vm.institutionalAnswer?.horizon || '12–24 Months',
    confidence,
    confidenceExplanation,
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
    constitutionVersion: aic?.version || ipf?.version || rc?.version || '1.0',
    investmentContext,
    researchConclusion,
    questionsBeforeYouDecide,
    institutionalThinkingFramework,
    methodologyIntent: investmentContext?.primary_intent || aic?.intent?.primary_intent || null,
    realIntent: investmentContext?.real_intent || aic?.intent?.real_intent || null,
    playbook,
    researchJourney,
    researchJourneyState: journeyState,
    suggestedNextResearch: asList(vm.suggestedNextResearch || [], 6),
    deep: {
      thesis: vm.thesis,
      why: whyAgib,
      financialNarrative: vm.financialNarrative,
      valuationNarrative: vm.valuationNarrative,
      sectorNarrative: vm.sectorNarrative,
      macroNarrative: vm.macroNarrative,
      marketNarrative: vm.marketNarrative,
      bull: moreBullish,
      base: vm.base,
      bear: moreBearish,
      risks: vm.risks,
      catalysts: vm.catalysts,
      conclusion: bottomLine,
      whatChanged: vm.whatChanged,
      recommendationStatus: vm.recommendationStatus,
      readinessGate: vm.decisionEngine?.readinessGate || null,
      companyQuality10: vm.decisionEngine?.companyQuality10 ?? vm.recommendationStatus?.companyQuality10,
      marketOpportunity10:
        vm.decisionEngine?.marketOpportunity10 ?? vm.recommendationStatus?.marketOpportunity10,
      evidenceConfidence:
        vm.decisionEngine?.evidenceConfidence ?? vm.recommendationStatus?.evidenceConfidence,
      investmentThesisStatus:
        vm.decisionEngine?.investmentThesisStatus ||
        vm.recommendationStatus?.investmentThesisStatus ||
        '',
      askSlim: pack?.degradation?.ask_slim,
      degraded: Boolean(pack?.degraded || pack?.mode === 'node_desk_fallback'),
    },
  };
}
