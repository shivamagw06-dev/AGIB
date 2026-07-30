/**
 * Map SearchView → Institutional Research Workspace view-model.
 *
 * Ownership rules (presentation soft-wire):
 * each section has one primary owner. Secondary sources fill gaps only.
 * Never expose architecture names to the user.
 */

function isGateFailureText(value) {
  const s = String(value || '').toLowerCase();
  if (!s) return false;
  return (
    s.includes('recommendation withheld') ||
    s.includes('insufficient evidence') ||
    s.includes('insufficient company evidence') ||
    s.includes('missing:') ||
    /^(cid|ecp)\s+coverage/i.test(String(value || '')) ||
    /\b(financial_statements|market_data|valuation_metrics|shares_outstanding)\b/i.test(String(value || ''))
  );
}

function asText(value, fallback = '') {
  if (value == null) return fallback;
  if (typeof value === 'object') {
    return asText(value.thesis || value.summary || value.snippet || value.title || value.stance, fallback);
  }
  const text = String(value).replace(/&amp;/g, '&').replace(/\s+/g, ' ').trim();
  if (!text || text.startsWith('{') || /document_id|provider_id|yahoo|finnhub|indianapi/i.test(text)) {
    return fallback;
  }
  if (isGateFailureText(text)) return fallback;
  return text;
}

function asList(value, limit = 8) {
  if (!Array.isArray(value)) return [];
  return value.map((v) => asText(v)).filter(Boolean).slice(0, limit);
}

function pct(value) {
  if (value == null || Number.isNaN(Number(value))) return null;
  const n = Number(value);
  return n <= 1 ? Math.round(n * 100) : Math.round(n);
}

function gradeFromScore(score) {
  if (score == null) return null;
  const n = Number(score);
  if (Number.isNaN(n)) return null;
  const v = n <= 1 ? n * 100 : n;
  if (v >= 90) return 'A+';
  if (v >= 80) return 'A';
  if (v >= 70) return 'B+';
  if (v >= 60) return 'B';
  if (v >= 50) return 'C';
  return 'D';
}

function toneForStance(stance) {
  const s = String(stance || '').toLowerCase();
  if (s.includes('construct') || s.includes('bull') || s.includes('positive')) return 'pos';
  if (s.includes('caution') || s.includes('bear') || s.includes('insuff')) return 'neg';
  return 'neu';
}

function stanceOf(pack, ac) {
  const raw =
    pack?.house_view_card?.stance ||
    pack?.answer?.house_view_label ||
    ac?.house_label ||
    '';
  const s = String(raw || '').toLowerCase();
  if (/insufficient|withheld|unknown/.test(s)) return 'Neutral';
  if (/constructive|bull|overweight|positive|improved/.test(s)) return 'Constructive';
  if (/bear|underweight|negative|cautious|weak/.test(s)) return 'Cautious';
  if (/neutral|hold|balanced/.test(s)) return 'Neutral';
  if (raw) return String(raw);
  return 'Neutral';
}

function fmtMetric(value) {
  if (value == null || value === '') return null;
  if (typeof value === 'number') {
    if (Math.abs(value) <= 1.5) return `${(value * 100).toFixed(1)}%`;
    return Number.isInteger(value) ? String(value) : value.toFixed(1);
  }
  return String(value);
}

function humaniseChangeType(type) {
  const t = String(type || '').toLowerCase();
  if (!t) return 'Signal';
  if (t.includes('financial') || t.includes('margin') || t.includes('revenue') || t.includes('roe')) {
    return 'Financial';
  }
  if (t.includes('valuation') || t.includes('pe') || t.includes('multiple')) return 'Valuation';
  if (t.includes('management') || t.includes('promoter') || t.includes('governance')) {
    return 'Management';
  }
  if (t.includes('ownership') || t.includes('fii') || t.includes('dii') || t.includes('holder')) {
    return 'Ownership';
  }
  if (t.includes('earn') || t.includes('result') || t.includes('guidance')) return 'Earnings';
  if (t.includes('house') || t.includes('view') || t.includes('stance')) return 'House View';
  if (t.includes('predict') || t.includes('forecast') || t.includes('accuracy')) {
    return 'Prediction Accuracy';
  }
  if (t.includes('market') || t.includes('price') || t.includes('volume')) return 'Market';
  return t.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function academyLessons(academy, ca) {
  const out = [];
  const push = (v) => {
    const t = asText(v);
    if (t && !isGateFailureText(t) && !out.includes(t) && !/^[a-z]+(?:_[a-z0-9]+)+$/.test(t)) {
      out.push(t);
    }
  };
  for (const hint of academy?.answer_hints || academy?.reasoning_points || []) push(hint);
  const applied = ca?.academy_application?.applied_concepts || academy?.applied_concepts || [];
  for (const c of applied) {
    if (typeof c === 'string') {
      // Never surface snake_case concept ids — skip unless already prose
      if (!/^[a-z]+(?:_[a-z0-9]+)+$/.test(c)) push(c);
      continue;
    }
    if (c && typeof c === 'object') {
      push(c.application || c.why_it_matters || c.what_it_is || c.definition || c.investment_implication);
    }
  }
  return out.slice(0, 6);
}

function buildMonitorRows(cm, pack) {
  const rows = [];
  const summary = cm?.what_changed || {};
  const changes = summary.changes || summary.items || summary.rows || cm?.changes || [];
  if (Array.isArray(changes)) {
    for (const c of changes.slice(0, 12)) {
      if (typeof c === 'string') {
        rows.push({
          category: 'Signal',
          metric: asText(c, 'Update'),
          previous: 'Prior',
          current: 'Updated',
          change: '→',
        });
        continue;
      }
      const type = c.change_type || c.type || c.category || c.metric || c.field;
      rows.push({
        category: humaniseChangeType(type),
        metric: asText(c.metric || c.field || c.title || type, 'Signal'),
        previous: asText(c.previous || c.from || c.prior || 'Prior', 'Prior'),
        current: asText(c.current || c.to || c.detail || c.value || 'Updated', 'Updated'),
        change: asText(c.direction || c.significance || c.delta || '→', '→'),
      });
    }
  }
  if (!rows.length && pack?.whats_changed) {
    const wc = pack.whats_changed;
    for (const item of asList(wc.bullets || wc.items || wc.summary, 6)) {
      rows.push({
        category: 'Signal',
        metric: item,
        previous: 'Prior review',
        current: 'Current review',
        change: 'Updated',
      });
    }
  }
  // Soft group order: Financial → Valuation → Earnings → Ownership → Management → House View → rest
  const order = [
    'Financial',
    'Valuation',
    'Earnings',
    'Ownership',
    'Management',
    'House View',
    'Prediction Accuracy',
    'Market',
    'Signal',
  ];
  rows.sort((a, b) => order.indexOf(a.category) - order.indexOf(b.category));
  return rows;
}

export function mapSearchPack(pack) {
  if (!pack || typeof pack !== 'object') return null;

  const ios = pack.investment_office_os && typeof pack.investment_office_os === 'object'
    ? pack.investment_office_os
    : null;
  const iosThesis = ios?.investment_thesis || {};
  const iosDecision = ios?.decision_office || {};
  const iosPortfolio = ios?.portfolio_office || {};
  const iosMonitoring = ios?.monitoring_office || {};
  const iosLearning = ios?.learning_office || {};
  const investmentOfficeOs =
    ios &&
    (iosThesis.thesis_id ||
      iosDecision.decision_id ||
      iosPortfolio.idea_id ||
      iosMonitoring.portfolio_idea ||
      iosLearning.learning_id)
      ? {
          release: asText(ios.release, 'AGI v4.0'),
          thesisId: asText(iosThesis.thesis_id, ''),
          decisionId: asText(iosDecision.decision_id, ''),
          decision: asText(iosDecision.decision, ''),
          decisionStatus: asText(iosDecision.status, ''),
          ideaId: asText(iosPortfolio.idea_id, ''),
          relativeRank: iosPortfolio.relative_rank ?? null,
          expectedRole: asText(iosPortfolio.expected_role, ''),
          monitoringEvents: iosMonitoring.n_events ?? null,
          requiresReview: iosMonitoring.requires_review ?? null,
          learningId: asText(iosLearning.learning_id, ''),
          learningOutcome: asText(iosLearning.outcome, ''),
          learningCategory: asText(iosLearning.category, ''),
          positions: false,
          orders: false,
        }
      : null;

  const ic = pack.intelligence_construction?.enabled ? pack.intelligence_construction : null;
  const ac = pack.answer_construction?.enabled ? pack.answer_construction : null;
  const ide = pack.decision_engine?.active ? pack.decision_engine : null;
  const ideSummary = ide?.summary || {};
  const briefing = pack.institutional_briefing || {};
  const ca = pack.company_analysis || {};
  const cm = pack.company_monitor || {};
  const dossier = pack.company_dossier || {};
  const sector = pack.sector_intelligence || {};
  const academy = pack.finance_academy || {};
  const hv = pack.house_view_card || {};
  const thesis = pack.current_thesis || {};
  const recoStatus = ac?.recommendation_status || briefing.recommendation_status || {};
  const enrich = ic?.answer_enrichment || {};
  const sections = ic?.sections || {};

  // Primary owners
  const fin = ca.financial_intelligence || {}; // Financial Intelligence layer (via CA assemble)
  const val = ca.valuation_intelligence || {};
  const bq = ca.business_quality || {};
  const identity = ca.identity || {};

  const stance = stanceOf(pack, ac);
  const confidence = pct(ideSummary.confidence_pct ?? pack.confidence ?? hv.confidence) ?? null;
  const coverage = pct(
    recoStatus.coverage_pct || dossier.coverage_pct || ca.recommendation_readiness?.overall || fin.coverage_pct
  );
  const ail = pack.intelligence_layer?.enabled ? pack.intelligence_layer : null;
  const ailThesis = ail?.thesis || {};
  const ailForecast = ail?.forecast || {};
  const ailDossier = ail?.dossier || {};
  const iaf =
    pack.institutional_analysts?.enabled
      ? pack.institutional_analysts
      : ac?.institutional_analysts?.enabled
        ? ac.institutional_analysts
        : null;
  const iafBiz = iaf?.business_intelligence || iaf?.analyst_opinions?.business || null;
  const iafFin = iaf?.financial_intelligence || iaf?.analyst_opinions?.financial || null;
  const iafVal = iaf?.valuation_intelligence || iaf?.analyst_opinions?.valuation || null;
  const iafMkt = iaf?.market_intelligence || iaf?.analyst_opinions?.market || null;
  const iafSec = iaf?.sector_intelligence_opinion || iaf?.analyst_opinions?.sector || null;
  const iafMacro = iaf?.macro_intelligence || iaf?.analyst_opinions?.macro || null;
  const iafRisk = iaf?.risk_intelligence || iaf?.analyst_opinions?.risk || null;
  const iafMgmt = iaf?.management_intelligence || iaf?.analyst_opinions?.management || null;
  const iafOwn = iaf?.ownership_intelligence || iaf?.analyst_opinions?.ownership || null;
  const stack =
    pack.institutional_stack?.enabled
      ? pack.institutional_stack
      : iaf?.institutional_stack?.enabled
        ? iaf.institutional_stack
        : ca.institutional_stack?.enabled
          ? ca.institutional_stack
          : null;
  const stackSummary = stack?.summary || {};
  const stackMii = stack?.layers?.management_intelligence || {};
  const stackFdi = stack?.layers?.filing_diff || {};
  const stackFil = stack?.layers?.filing_intelligence || {};
  const stackPil = stack?.layers?.peer_intelligence || {};
  const iafCommittee = iaf?.institutional_view || iaf?.committee || null;
  const iafCio = iaf?.cio || null;
  const irw =
    pack.research_writer?.enabled
      ? pack.research_writer
      : ac?.research_writer?.enabled
        ? ac.research_writer
        : iaf?.research_writer?.enabled
          ? iaf.research_writer
          : null;
  const ir =
    ac?.institutional_reasoning?.enabled !== false &&
    (ac?.institutional_reasoning || pack.institutional_reasoning)
      ? ac?.institutional_reasoning || pack.institutional_reasoning
      : null;
  const irOwns = Boolean(ir?.owns_executive && (ir?.executive || ir?.answer));
  const reasoningPattern = ac?.reasoning_pattern || (irOwns ? { enabled: true, source: ir?.reasoning_source } : null);
  const cxr =
    ac?.contradiction_reasoning?.enabled
      ? ac.contradiction_reasoning
      : pack.contradiction_reasoning?.enabled
        ? pack.contradiction_reasoning
        : null;
  const ecr = ac?.ecr || ir?.ecr || pack.ecr || null;
  const novelty = ac?.novelty || ir?.novelty || {};
  const books =
    (pack.academy_books?.enabled && pack.academy_books) ||
    (ac?.academy_books?.enabled && ac.academy_books) ||
    (irw?.academy_books?.enabled && irw.academy_books) ||
    null;
  const irwReport = irw?.institutional_report || ac?.institutional_report || iaf?.institutional_report || null;
  const ide = pack.decision_engine?.active ? pack.decision_engine : null;
  const ideSummary = ide?.summary || {};
  const ideLayers = Array.isArray(ide?.layers)
    ? ide.layers
        .filter((layer) => layer && layer.id)
        .map((layer, idx) => ({
          id: String(layer.id),
          index: idx + 1,
          title: asText(layer.title, String(layer.id).replace(/_/g, ' ')),
          question: asText(layer.question, ''),
          score: layer.score == null ? null : Number(layer.score),
          grade: asText(layer.grade, gradeFromScore(layer.score) || ''),
          weight: layer.weight == null ? null : Number(layer.weight),
          status: asText(layer.status, 'partial'),
          reasoning: asText(layer.reasoning, ''),
          evidence: asList(layer.evidence, 5),
          isDecision: String(layer.id) === 'decision',
          positive: asList(layer.positive, 6),
          negative: asList(layer.negative, 6),
          bull: layer.bull || null,
          base: layer.base || null,
          bear: layer.bear || null,
          probabilityWeighted:
            layer.probability_weighted_return_pct ??
            ideSummary.probability_weighted_return_pct ??
            null,
          riskReward: layer.risk_reward ?? ideSummary.risk_reward ?? null,
          suitableFor: asList(layer.suitable_for || ideSummary.suitable_for, 6),
          unsuitableFor: asList(layer.unsuitable_for || ideSummary.unsuitable_for, 6),
          action: asText(layer.action || ideSummary.action, ''),
          strengths: asList(layer.strengths, 5),
          weaknesses: asList(layer.weaknesses, 5),
          evidence_quality_score:
            layer.evidence_quality_score == null ? null : Number(layer.evidence_quality_score),
          company_quality_score:
            layer.company_quality_score == null ? null : Number(layer.company_quality_score),
        }))
    : [];
  const decisionStackLayers = ideLayers.filter((l) => !l.isDecision);
  const decisionLayer = ideLayers.find((l) => l.isDecision) || null;

  const stance = stanceOf(pack);
  const confidence =
    pct(
      ideSummary.confidence_pct ??
        pack.confidence ??
        hv.confidence ??
        enrich.confidence
    ) ?? 72;
  const coverage =
    pct(
      recoStatus.coverage_pct ||
        dossier.coverage_pct ||
        ca.recommendation_readiness?.overall ||
        fin.coverage_pct ||
        dvc.coverage_pct
    ) ?? 80;
  const knowledgeGrade =
    dvc.knowledge_grade ||
    dvc.research_grade ||
    gradeFromScore(bq.business_quality_score) ||
    (coverage >= 90 ? 'A+' : coverage >= 75 ? 'A' : 'B');

  const institutionalAnswer =
    ac?.institutional_answer?.enabled
      ? ac.institutional_answer
      : pack.answer?.institutional_answer?.enabled
        ? pack.answer.institutional_answer
        : null;

  // Prefer AGIB reasoning executive when it owns the answer; editorial is rewrite-only.
  const reasoningExecutive = irOwns
    ? asText(ir?.executive || ir?.answer)
    : asText(cxr?.executive);
  const editorialExecutive =
    asText(ac?.editorial?.rewritten_summary) ||
    asText(ac?.editorial?.executive) ||
    asText(pack.editorial?.rewritten_summary) ||
    asText(pack.editorial?.executive) ||
    '';
  const executive =
    reasoningExecutive ||
    editorialExecutive ||
    asText(ac?.executive) ||
    asText(institutionalAnswer?.text) ||
    asText(irw?.executive_summary) ||
    asText(irwReport?.executive_summary) ||
    asText(iafCio?.executive_summary) ||
    asText(ide?.answer_enrichment?.executive_framing) ||
    asText(enrich.executive_summary) ||
    asText(briefing.executive_summary) ||
    asText(briefing.what_is_happening) ||
    asText(pack.executive_summary) ||
    asText(pack.answer?.executive_summary) ||
    asText(pack.answer?.summary) ||
    '';

  // Business Intelligence — Company Analysis primary
  const business = {
    model:
      asText(identity.business_model) ||
      asText(ca.business_overview) ||
      asText(sections.business_intelligence?.business_model),
    industry:
      asText(identity.industry) ||
      asText(identity.sector) ||
      asText(sector.sector_name),
    moat:
      asText(bq.moat) ||
      asText(bq.competitive_advantage) ||
      asText(bq.competitive_position) ||
      asText(sections.business_intelligence?.competitive_advantages),
    revenueDrivers:
      asText(sections.business_intelligence?.revenue_drivers) ||
      asList(ca.catalysts, 2).join(' ') ||
      '',
    management:
      asText(bq.dimensions?.management_quality) ||
      asText(bq.scores?.management) ||
      asText((bq.dimensions || {}).management) ||
      '',
    pricingPower: asText(bq.dimensions?.pricing_power || bq.scores?.pricing_power),
    qualityScore: bq.business_quality_score ?? null,
    qualityGrade: asText(bq.grade, gradeFromScore(bq.business_quality_score) || ''),
    narrative:
      asText(ca.investment_thesis) ||
      asText(sections.business_intelligence?.narrative) ||
      asText(ca.business_overview),
  };

  // Financial Intelligence — FI metrics primary (not repeated elsewhere)
  const financialCards = [
    { label: 'Revenue Growth', value: fmtMetric(fin.growth) },
    { label: 'Operating Margin', value: fmtMetric(fin.margins) },
    { label: 'Returns (ROE/ROIC)', value: fmtMetric(fin.returns) },
    { label: 'Cash Flow', value: fmtMetric(fin.cash_flow) },
    { label: 'Balance Sheet', value: fmtMetric(fin.balance_sheet?.leverage) },
    { label: 'Capital Allocation', value: fmtMetric(fin.capital_allocation) },
  ].filter((c) => c.value != null);

  // Valuation — valuation intelligence primary
  const valuationCards = [
    val.current_pe != null ? { label: 'Current P/E', value: `${Number(val.current_pe).toFixed(1)}x` } : null,
    val.forward_pe != null ? { label: 'Forward P/E', value: `${Number(val.forward_pe).toFixed(1)}x` } : null,
    val.pb != null ? { label: 'P/B', value: `${Number(val.pb).toFixed(1)}x` } : null,
    val.peg != null ? { label: 'PEG', value: Number(val.peg).toFixed(2) } : null,
    val.ev_ebitda != null ? { label: 'EV/EBITDA', value: `${Number(val.ev_ebitda).toFixed(1)}x` } : null,
    val.premium_discount_vs_history_pct != null
      ? {
          label: 'Vs History',
          value: `${val.premium_discount_vs_history_pct > 0 ? '+' : ''}${val.premium_discount_vs_history_pct}%`,
          tone:
            val.premium_discount_vs_history_pct > 10
              ? 'neg'
              : val.premium_discount_vs_history_pct < -10
                ? 'pos'
                : 'neu',
        }
      : null,
  ].filter(Boolean);

  // Market Intelligence — market pack / dossier market data
  const marketPack =
    (Array.isArray(pack.market_intelligence) ? null : pack.market_intelligence) ||
    enrich.market_intelligence ||
    sections.market_performance ||
    {};
  const marketSnap = {
    ...(dossier.market_data || {}),
    ...(marketPack.snapshot || {}),
  };
  const marketCards = Array.isArray(marketPack.cards)
    ? marketPack.cards
    : [
        marketSnap.current_price != null ? { label: 'Price', value: marketSnap.current_price } : null,
        marketSnap.market_cap != null ? { label: 'Market Cap', value: marketSnap.market_cap } : null,
        marketSnap.volume != null ? { label: 'Volume', value: marketSnap.volume } : null,
        marketSnap.fifty_two_week_high != null
          ? { label: '52W High', value: marketSnap.fifty_two_week_high }
          : null,
        marketSnap.fifty_two_week_low != null
          ? { label: '52W Low', value: marketSnap.fifty_two_week_low }
          : null,
        marketPack.momentum || marketSnap.range_position_0_1 != null
          ? {
              label: 'Momentum',
              value:
                marketPack.momentum ||
                (marketSnap.range_position_0_1 >= 0.6
                  ? 'Positive'
                  : marketSnap.range_position_0_1 <= 0.35
                    ? 'Soft'
                    : 'Mixed'),
            }
          : null,
      ].filter(Boolean);

  // Decision Scorecard — IDE scores only
  const layerScores = ideSummary.layer_scores || {};
  const scoreChips = [
    ['Business', layerScores.company_quality ?? business.qualityScore],
    ['Financial', layerScores.financial_quality],
    ['Management', layerScores.management],
    ['Valuation', layerScores.valuation],
    ['Macro', layerScores.macro],
    ['Industry', layerScores.industry],
    ['Risk', layerScores.risk],
  ]
    .filter(([, v]) => v != null && !Number.isNaN(Number(v)))
    .map(([label, value]) => ({
      label,
      value: Math.round(Number(value)),
      grade: gradeFromScore(value),
    }));

  const confidenceBreakdown = ideSummary.confidence_breakdown || {};
  const confidenceRows = [
    ['Business', confidenceBreakdown.business],
    ['Financial', confidenceBreakdown.financial],
    ['Management', confidenceBreakdown.management],
    ['Valuation', confidenceBreakdown.valuation],
    ['Macro', confidenceBreakdown.macro],
    ['Industry', confidenceBreakdown.industry],
    ['Risk', confidenceBreakdown.risk],
  ]
    .filter(([, v]) => v != null)
    .map(([label, value]) => ({ label, value: Math.round(Number(value)) }));

  const learned = asList(
    [
      ...(enrich.research_takeaways || []),
      ...(sections.research_takeaways || []),
      ...(academy.reasoning_points || []),
      ...(academy.answer_hints || []),
      ...(books?.logic_hints || []),
      ...(books?.frameworks || []).map((f) => (f ? `Framework: ${f}` : '')),
    ],
    8
  );

  const explore = asList(pack.follow_up_questions, 10);
  if (!explore.length) {
    explore.push(
      'Compare peers on valuation',
      'What changed this quarter?',
      'Historical valuation range',
      'Sector demand outlook',
      'Key risks deep dive'
    );
  }

  return {
    question: asText(pack.question, 'Institutional research question'),
    intent: asText(pack.intent, 'Institutional Research'),
    category: asText(sector.sector_name || sector.sector_id || pack.entities?.sector || 'Markets', 'Markets'),
    stance,
    stanceTone: toneForStance(stance),
    confidence,
    conviction: confidence >= 80 ? 'High' : confidence >= 60 ? 'Medium' : 'Developing',
    horizon: asText(
      institutionalAnswer?.horizon || hv.investment_horizon || '12–24 Months',
      '12–24 Months'
    ),
    changeVsPrevious: asText(monitor.max_significance || pack.whats_changed?.direction || 'Stable', 'Stable'),
    readiness: recoStatus.blocked ? 'Research note complete' : 'Institutional Grade',
    coverage,
    knowledgeGrade,
    freshness: (() => {
      const raw = pack.freshness_indicator || '';
      if (!raw || /unknown|n\/a/i.test(raw)) return 'Current';
      return asText(raw, 'Current');
    })(),

    // 1. Executive Summary
    executive,
    institutionalAnswer: institutionalAnswer
      ? {
          recommendation: asText(institutionalAnswer.recommendation, ''),
          conviction: asText(institutionalAnswer.conviction, ''),
          reason: asText(institutionalAnswer.reason, ''),
          risk: asText(institutionalAnswer.risk, ''),
          horizon: asText(institutionalAnswer.horizon, ''),
          text: asText(institutionalAnswer.text, ''),
          evidenceInsufficient: Boolean(institutionalAnswer.evidence_insufficient),
          structured: institutionalAnswer.structured || null,
          wordCount: institutionalAnswer.word_count || null,
        }
      : null,
    thesis:
      asText(irw?.investment_thesis) ||
      asText(iafCio?.investment_thesis) ||
      asText(ac?.thesis) ||
      asText(biz.long_term_growth) ||
      asText(thesis.summary) ||
      asText(pack.answer?.investment_thesis) ||
      asText(ca.investment_thesis) ||
      executive,
    why: asList(ac?.why || enrich.why_bullets || pack.why || pack.answer?.why, 12).filter(
      (w) => !isGateFailureText(w)
    ),
    whyCards,
    kpis,
    financialCards,
    financialNarrative:
      asText(irw?.financial_intelligence) ||
      asText(iaf?.written_financial_intelligence) ||
      asText(iafFin?.summary) ||
      asText(iafFin?.headline) ||
      asText(fin.narrative) ||
      asText(biz.operating_metrics) ||
      asText(briefing.financial_intelligence) ||
      'Financial quality should be judged through incremental returns, cash conversion and balance-sheet resilience.',
    valuationCards,
    valuationNarrative:
      asText(irw?.valuation_intelligence) ||
      asText(iaf?.written_valuation_intelligence) ||
      asText(iafVal?.summary) ||
      asText(iafVal?.headline) ||
      asText(val.narrative) ||
      asText(pack.valuation_perspective) ||
      asText(briefing.valuation_perspective) ||
      'Valuation should be framed against growth durability and competitive position — multiples alone are incomplete.',
    valuationChart: Array.isArray(pack.charts)
      ? pack.charts.find((c) => Array.isArray(c?.points) && c.points.some((p) => p?.value != null))
      : null,
    marketNarrative:
      asText(irw?.market_intelligence) ||
      asText(iaf?.written_market_intelligence) ||
      asText(iafMkt?.summary) ||
      asText(iafMkt?.headline) ||
      asText(marketPack.narrative) ||
      asText(sections.market_performance?.narrative) ||
      asText(briefing.market_performance),
    marketSnapshot: marketSnap,
    marketCards: Array.isArray(marketPack.cards) ? marketPack.cards : [],
    ownershipNarrative:
      asText(irw?.ownership) ||
      asText(iaf?.written_ownership) ||
      asText(iafOwn?.summary) ||
      asText(iafOwn?.headline) ||
      asText(sections.ownership?.narrative) ||
      asText(briefing.ownership),
    ownership: sections.ownership?.snapshot || iafOwn?.sections || {},
    businessModel:
      asText(irw?.business_intelligence) ||
      asText(iaf?.written_business_intelligence) ||
      asText(iafBiz?.sections?.business_model) ||
      asText(iafBiz?.summary) ||
      asText(iafBiz?.headline) ||
      asText(biz.business_model) ||
      asText(ca.identity?.business_model) ||
      asText(ca.business_overview),
    businessIntelligence: biz,
    businessQuality: bq,
    sectorNarrative:
      asText(irw?.sector_intelligence) ||
      asText(iaf?.written_sector_intelligence) ||
      asText(iafSec?.summary) ||
      asText(iafSec?.headline) ||
      asText(biz.industry_structure) ||
      asText(sector.reasoning || sector.narrative) ||
      asText(sections.sector_intelligence?.narrative),
    sectorDrivers: asList(
      iafSec?.sections?.sector_kpis || pack.sector_drivers || briefing.sector_drivers,
      6
    ),
    macroDrivers: asList(
      iafMacro?.sections?.drivers || pack.macro_drivers || briefing.macro_drivers,
      6
    ),
    macroNarrative:
      asText(irw?.macro_intelligence) ||
      asText(iaf?.written_macro_intelligence) ||
      asText(iafMacro?.summary) ||
      asText(iafMacro?.headline) ||
      asText(briefing.macro_outlook),
    managementNarrative:
      asText(irw?.management) ||
      asText(iaf?.written_management) ||
      asText(stackMii?.cio_brief) ||
      asText(iafMgmt?.summary) ||
      asText(iafMgmt?.headline) ||
      (stackSummary.management_dna
        ? `Management DNA: ${stackSummary.management_dna}` +
          (stackSummary.management_confidence != null
            ? ` · trust score ${stackSummary.management_confidence}`
            : '')
        : ''),
    institutionalStack: stack
      ? {
          enabled: true,
          ticker: stack.ticker || pack.ticker || null,
          summary: stackSummary,
          managementDna: stackSummary.management_dna || stackMii.dna || null,
          managementConfidence:
            stackSummary.management_confidence ?? stackMii.confidence ?? null,
          accountingBehaviour:
            stackSummary.accounting_behaviour || stack?.layers?.accounting_intelligence?.behaviour || null,
          accountingQuality:
            stackSummary.accounting_quality_score ??
            stack?.layers?.accounting_intelligence?.accounting_quality_score ??
            null,
          accountingConfidence:
            stackSummary.accounting_confidence ??
            stack?.layers?.accounting_intelligence?.confidence ??
            null,
          manipulationRisk:
            stackSummary.manipulation_risk ||
            stack?.layers?.accounting_intelligence?.manipulation_risk ||
            null,
          portfolioId: stackSummary.portfolio_id || stack?.layers?.portfolio_intelligence?.portfolio_id || null,
          portfolioGrade:
            stackSummary.portfolio_grade || stack?.layers?.portfolio_intelligence?.health_grade || null,
          portfolioQuality:
            stackSummary.portfolio_quality ??
            stack?.layers?.portfolio_intelligence?.portfolio_quality ??
            null,
          portfolioNetEffect:
            stackSummary.portfolio_net_effect ||
            stack?.layers?.portfolio_intelligence?.impact?.net_portfolio_effect ||
            null,
          portfolioFit:
            stackSummary.portfolio_fit ||
            stack?.layers?.portfolio_intelligence?.suitability?.portfolio_fit ||
            null,
          causalConfidence:
            stackSummary.causal_confidence ??
            stack?.layers?.causal_intelligence?.confidence ??
            pack.causal_intelligence?.confidence ??
            null,
          causalUpstream:
            stackSummary.causal_upstream ||
            stack?.layers?.causal_intelligence?.upstream_drivers ||
            pack.causal_intelligence?.upstream_drivers ||
            null,
          causalWhy:
            stackSummary.causal_why ||
            (Array.isArray(stack?.layers?.causal_intelligence?.why)
              ? stack.layers.causal_intelligence.why[0]
              : stack?.layers?.causal_intelligence?.why) ||
            (Array.isArray(pack.causal_intelligence?.why)
              ? pack.causal_intelligence.why[0]
              : pack.causal_intelligence?.why) ||
            null,
          forecastMostLikely:
            stackSummary.forecast_most_likely ||
            stack?.layers?.forecast_intelligence?.most_likely ||
            pack.forecast_intelligence?.most_likely ||
            null,
          forecastConfidence:
            stackSummary.forecast_confidence ??
            stack?.layers?.forecast_intelligence?.confidence ??
            pack.forecast_intelligence?.confidence ??
            null,
          forecastDistribution:
            stackSummary.forecast_distribution ||
            stack?.layers?.forecast_intelligence?.distribution ||
            pack.forecast_intelligence?.distribution ||
            null,
          forecastSummary:
            stackSummary.forecast_summary ||
            stack?.layers?.forecast_intelligence?.executive_forecast ||
            pack.forecast_intelligence?.executive_forecast ||
            null,
          knowledgeCanonicalId:
            stackSummary.knowledge_canonical_id ||
            stack?.layers?.knowledge_graph?.canonical_id ||
            pack.knowledge_graph?.canonical_id ||
            null,
          knowledgeRelationshipCount:
            stackSummary.knowledge_relationship_count ??
            stack?.layers?.knowledge_graph?.relationship_count ??
            pack.knowledge_graph?.relationship_count ??
            null,
          knowledgeConfidence:
            stackSummary.knowledge_confidence ??
            stack?.layers?.knowledge_graph?.confidence ??
            pack.knowledge_graph?.confidence ??
            null,
          knowledgeSummary:
            stackSummary.knowledge_summary ||
            stack?.layers?.knowledge_graph?.summary ||
            pack.knowledge_graph?.summary ||
            null,
          memoryLessonCount:
            stackSummary.memory_lesson_count ??
            stack?.layers?.institutional_memory?.lesson_count ??
            pack.institutional_memory?.lesson_count ??
            null,
          memoryMistakeCount:
            stackSummary.memory_mistake_count ??
            stack?.layers?.institutional_memory?.mistake_count ??
            pack.institutional_memory?.mistake_count ??
            null,
          memoryThinkingImproved:
            stackSummary.memory_thinking_improved ??
            stack?.layers?.institutional_memory?.thinking_improved ??
            pack.institutional_memory?.thinking_improved ??
            null,
          memorySummary:
            stackSummary.memory_summary ||
            stack?.layers?.institutional_memory?.summary ||
            pack.institutional_memory?.summary ||
            null,
          simulationScenarioId:
            stackSummary.simulation_scenario_id ||
            stack?.layers?.simulation_lab?.scenario_id ||
            pack.simulation_lab?.scenario_id ||
            null,
          simulationExpectedReturn:
            stackSummary.simulation_expected_return ??
            stack?.layers?.simulation_lab?.expected_return ??
            pack.simulation_lab?.expected_return ??
            null,
          simulationConfidence:
            stackSummary.simulation_confidence ??
            stack?.layers?.simulation_lab?.confidence ??
            pack.simulation_lab?.confidence ??
            null,
          simulationSummary:
            stackSummary.simulation_summary ||
            stack?.layers?.simulation_lab?.summary ||
            pack.simulation_lab?.summary ||
            null,
          decisionStatus:
            stackSummary.decision_status ||
            stack?.layers?.decision_engine_v2?.recommendation_status ||
            pack.decision_engine_v2?.recommendation_status ||
            null,
          decisionConfidence:
            stackSummary.decision_confidence ??
            stack?.layers?.decision_engine_v2?.confidence ??
            pack.decision_engine_v2?.confidence ??
            null,
          decisionAuditId:
            stackSummary.decision_audit_id ||
            stack?.layers?.decision_engine_v2?.audit_id ||
            pack.decision_engine_v2?.audit_id ||
            null,
          decisionSummary:
            stackSummary.decision_summary ||
            stack?.layers?.decision_engine_v2?.summary ||
            pack.decision_engine_v2?.summary ||
            null,
          filingFound: stackSummary.filing_found ?? stackFil.found ?? null,
          materialChangeSignal: stackSummary.material_change_signal ?? Boolean(stackFdi.enabled),
          peerEnabled: stackSummary.peer_enabled ?? Boolean(stackPil.enabled),
          pipeline: stack.pipeline || [],
          openConcerns: asList(
            [
              ...(stackMii.open_concerns || []),
              ...(stack?.layers?.accounting_intelligence?.open_concerns || []),
            ],
            6
          ),
        }
      : null,
    institutionalView: iafCommittee
      ? {
          summary:
            asText(irw?.institutional_view) ||
            asText(iaf?.written_institutional_view) ||
            asText(iafCommittee.committee_summary, ''),
          consensus: iafCommittee.consensus || {},
          stage1: iafCommittee.stage_1_consensus || {},
          stage2: Array.isArray(iafCommittee.stage_2_conflicts)
            ? iafCommittee.stage_2_conflicts
            : [],
          stage3: asList(iafCommittee.stage_3_missing_evidence, 6),
          challenges: Array.isArray(iafCommittee.stage_3_challenges || iafCommittee.challenges)
            ? (iafCommittee.stage_3_challenges || iafCommittee.challenges).slice(0, 4)
            : [],
          agreements: asList(iafCommittee.agreements, 4),
          disagreements: asList(iafCommittee.disagreements, 4),
          readiness: asText(
            iafCommittee.recommendation_readiness_label ||
              iaf?.committee_decision?.recommendation_readiness ||
              iafCommittee.recommendation_readiness,
            ''
          ),
          confidence: iafCommittee.confidence ?? iaf?.committee_decision?.confidence ?? null,
          stance: asText(
            iafCommittee.committee_stance ||
              iaf?.committee_decision?.committee_position ||
              iaf?.disagreement_matrix?.committee_stance,
            ''
          ),
          conviction: asText(
            iafCommittee.conviction || iaf?.committee_vote?.conviction || '',
            ''
          ),
          voteTally: asText(iafCommittee.vote_tally || iaf?.committee_vote?.tally || '', ''),
          reason: asText(iafCommittee.committee_reason || iaf?.disagreement_matrix?.reason, ''),
          disagreementMatrix: iaf?.disagreement_matrix || iafCommittee.disagreement_matrix || null,
          minutes: iaf?.committee_minutes || iafCommittee.minutes || null,
          minority: asList(
            (iaf?.minority_opinions || iafCommittee.minority_opinions || []).map((m) =>
              typeof m === 'string' ? m : m?.view
            ),
            3
          ),
          decision: iaf?.committee_decision || iafCommittee.decision || null,
          timeline: Array.isArray(iaf?.committee_timeline || iafCommittee.timeline)
            ? (iaf?.committee_timeline || iafCommittee.timeline).slice(-6)
            : [],
        }
      : null,
    whatChanged: asList(iaf?.what_changed || iafCio?.what_changed || pack.whats_changed?.bullets, 6),
    leaders,
    bull: asList(
      iafCio?.bull_case || ac?.bull || thesis.bull_case || pack.bull_case || pack.answer?.bull_case || ca.bull_case,
      6
    ),
    base: asList(iafCio?.base_case || ac?.base || thesis.neutral_case || ca.base_case, 6),
    bear: asList(
      iafCio?.bear_case || ac?.bear || thesis.bear_case || pack.bear_case || pack.answer?.bear_case || ca.bear_case,
      6
    ),
    risks: (() => {
      const iafRiskLines = iafRisk?.sections?.business_risks || iafCio?.key_risks;
      if (iafRiskLines) {
        return asList(iafRiskLines, 8).map((r, i) => ({
          risk: r,
          probability: i === 0 ? 'High' : i < 3 ? 'Medium' : 'Low',
          impact: i < 2 ? 'High' : 'Medium',
          severity: i === 0 ? 'Critical' : i < 3 ? 'Elevated' : 'Watch',
          monitoring: 'Active',
        }));
      }
      return risks;
    })(),
    catalysts: asList(iafCio?.key_catalysts || catalysts, 8),
    learned,
    responseConstitution:
      ac?.response_constitution?.enabled
        ? ac.response_constitution
        : pack.answer?.response_constitution?.enabled
          ? pack.answer.response_constitution
          : null,
    bottomLine:
      asText(ac?.bottom_line) ||
      asText(ac?.response_constitution?.bottom_line) ||
      asText(pack.answer?.bottom_line) ||
      asText(pack.answer?.response_constitution?.bottom_line) ||
      '',
    confidenceExplanation:
      asText(ac?.confidence_explanation) ||
      asText(ac?.response_constitution?.confidence?.explanation) ||
      asText(pack.answer?.confidence_explanation) ||
      asText(pack.answer?.response_constitution?.confidence?.explanation) ||
      '',
    conclusion:
      asText(ac?.bottom_line) ||
      asText(ac?.response_constitution?.bottom_line) ||
      asText(irw?.institutional_conclusion) ||
      asText(iafCio?.institutional_conclusion) ||
      asText(ac?.decision_conclusion) ||
      asText(decisionLayer?.reasoning) ||
      asText(ide?.decision?.reasoning) ||
      asText(enrich.current_outlook) ||
      asText(biz.long_term_growth) ||
      asText(briefing.current_outlook) ||
      asText(pack.current_outlook) ||
      executive,
    decisionEngine: ide
      ? {
          overallScore: ideSummary.overall_score ?? ide.overall_score ?? null,
          investmentGrade: asText(
            ideSummary.investment_grade || ide.investment_grade,
            gradeFromScore(ideSummary.overall_score ?? ide.overall_score) || ''
          ),
          confidence: pct(ideSummary.confidence_pct) ?? confidence,
          institutionalReadiness: pct(
            ideSummary.institutional_readiness_pct ??
              ide?.institutional_readiness_gate?.institutional_readiness_pct ??
              ide?.institutional_readiness_gate?.overall_coverage_pct
          ),
          recommendationReadiness: pct(
            ideSummary.recommendation_readiness_pct ??
              ide?.institutional_readiness_gate?.recommendation_readiness_pct ??
              ideSummary.evidence_confidence_pct ??
              ide?.institutional_readiness_gate?.evidence_confidence_pct
          ),
          evidenceConfidence: pct(
            ideSummary.recommendation_readiness_pct ??
              ideSummary.evidence_confidence_pct ??
              ide?.institutional_readiness_gate?.recommendation_readiness_pct ??
              ide?.institutional_readiness_gate?.evidence_confidence_pct
          ),
          analyticalConfidence: asText(
            ideSummary.analytical_confidence ||
              ide?.institutional_readiness_gate?.analytical_confidence_display ||
              ide?.institutional_readiness_gate?.analytical_confidence?.display,
            ''
          ),
          analyticalConfidenceExplanation: asText(
            ideSummary.analytical_confidence_explanation ||
              ide?.institutional_readiness_gate?.analytical_confidence_explanation ||
              ide?.institutional_readiness_gate?.analytical_confidence?.explanation,
            ''
          ),
          decisionLine: asText(
            ideSummary.decision_line || ide?.institutional_readiness_gate?.decision_line,
            ''
          ),
          companyQuality10:
            ideSummary.company_quality_10 ??
            ide?.institutional_readiness_gate?.company_quality_10 ??
            null,
          marketOpportunity10:
            ideSummary.market_opportunity_10 ??
            ide?.institutional_readiness_gate?.market_opportunity_10 ??
            null,
          investmentThesisStatus: asText(
            ideSummary.investment_thesis_status || decisionLayer?.investment_thesis_status,
            ''
          ),
          notANegativeView: Boolean(
            ideSummary.not_a_negative_view ?? decisionLayer?.not_a_negative_view
          ),
          expectedReturn12m: ideSummary.expected_return_12m_pct ?? null,
          bullCase: ideSummary.bull_case_pct ?? null,
          baseCase: ideSummary.base_case_pct ?? null,
          bearCase: ideSummary.bear_case_pct ?? null,
          probabilityWeighted: ideSummary.probability_weighted_return_pct ?? null,
          riskReward: ideSummary.risk_reward ?? null,
          scoreChips,
          confidenceRows,
          gateBlocked: Boolean(ideSummary.gate_blocked),
          readinessGate: ide.institutional_readiness_gate || null,
        }
      : null,

    // 4. Business Intelligence — CA
    business,

    // 5. Financial Intelligence
    financialNarrative: asText(fin.narrative) || '',
    financialCards,
    financialImproved: asList(fin.what_improved, 4).map((x) => String(x).replace(/_/g, ' ')),
    financialDeteriorated: asList(fin.what_deteriorated, 4).map((x) => String(x).replace(/_/g, ' ')),
    financialMonitor: asList(fin.what_deserves_monitoring, 5),

    // 6. Valuation Intelligence
    valuationNarrative: asText(val.narrative) || '',
    valuationCards,
    valuationChart: Array.isArray(pack.charts)
      ? pack.charts.find((c) => Array.isArray(c?.points) && c.points.some((p) => p?.value != null))
      : null,

    // 7. Market Intelligence
    marketNarrative: asText(marketPack.narrative) || '',
    marketCards,
    marketSnapshot: marketSnap,

    // 8. Sector Intelligence — SIF
    sectorNarrative:
      asText(sector.reasoning) ||
      asText(sector.narrative) ||
      asText((ca.sector_intelligence || {}).narrative) ||
      '',
    sectorDrivers: asList(sector.priority_metrics || pack.sector_drivers || briefing.sector_drivers, 6).map((d) =>
      String(d).replace(/_/g, ' ')
    ),

    // 9. Macro Intelligence — IRP
    macroDrivers: asList(pack.macro_drivers || briefing.macro_drivers, 6),

    // 10. Company Monitor — CMS
    monitorRows: buildMonitorRows(cm, pack),
    monitorHints: asList(cm.ask_agi_hints || cm.what_changed?.narrative, 5),
    houseViewReview: Boolean(cm.house_view_review),

    // 11. Risks & Catalysts — CA
    risks,
    catalysts,

    // 12. Bull / Base / Bear — IRP
    bull,
    base,
    bear,
    scenarioReturns: ide
      ? {
          bull: ideSummary.bull_case_pct,
          base: ideSummary.base_case_pct,
          bear: ideSummary.bear_case_pct,
        }
      : null,

    // 13. Research & Learning — Academy
    learned: academyLessons(academy, ca),

    // 14. Institutional Conclusion — IC + IRP
    conclusion,
    suitableFor: asList(ideSummary.suitable_for, 6),
    unsuitableFor: asList(ideSummary.unsuitable_for, 6),
    decisionAction: asText(ideSummary.action, ''),

    // 15. Recommendation Status — Gate / ECP
    recommendationStatus: {
      blocked: Boolean(recoStatus.blocked),
      status: asText(recoStatus.status, recoStatus.blocked ? 'Withheld' : 'Open'),
      summary: asText(
        recoStatus.summary,
        recoStatus.blocked
          ? 'Investment thesis INCONCLUSIVE — evidence insufficient, not a negative company view.'
          : 'Evidence coverage supports institutional analysis — not an automatic trade instruction.'
      ),
      detail: asText(recoStatus.detail, ''),
      gaps: knowledgeGaps,
      institutionalReadiness: pct(recoStatus.institutional_readiness_pct ?? recoStatus.coverage_pct),
      recommendationReadiness: pct(
        recoStatus.recommendation_readiness_pct ?? recoStatus.evidence_confidence_pct
      ),
      evidenceConfidence: pct(
        recoStatus.recommendation_readiness_pct ?? recoStatus.evidence_confidence_pct
      ),
      analyticalConfidence: asText(recoStatus.analytical_confidence, ''),
      analyticalConfidenceExplanation: asText(recoStatus.analytical_confidence_explanation, ''),
      requiredConfidence: pct(recoStatus.required_confidence_pct) ?? 80,
      companyQuality10: recoStatus.company_quality_10 ?? null,
      marketOpportunity10: recoStatus.market_opportunity_10 ?? null,
      coverage: recoStatus.coverage || null,
      checklist: Array.isArray(recoStatus.checklist) ? recoStatus.checklist : [],
      diagnosticCards: Array.isArray(recoStatus.diagnostic_cards)
        ? recoStatus.diagnostic_cards
        : Array.isArray(recoStatus.checklist)
          ? recoStatus.checklist
          : [],
      reasonBullets: asList(recoStatus.reason_bullets, 8),
      freshness: recoStatus.freshness || {},
      decisionLine: asText(recoStatus.decision_line, ''),
      additionalEvidenceRequired: asList(recoStatus.additional_evidence_required, 8),
      investmentThesisStatus: asText(recoStatus.investment_thesis_status, ''),
      notANegativeView: Boolean(recoStatus.not_a_negative_view),
      readinessBand: asText(recoStatus.readiness_band || recoStatus.readiness_label, ''),
      gateSummary: recoStatus.gate_summary || {},
    },

    explore,
    changedRows,
    supporting: pack.supporting_evidence || [],
    conflicting: pack.conflicting_evidence || [],
    icEnabled: Boolean(ic?.enabled),
    acEnabled: Boolean(ac?.enabled),
    editorialEnabled: Boolean(ac?.editorial?.enabled || pack.editorial?.enabled),
    editorialProvider: asText(ac?.editorial?.provider || pack.editorial?.provider, ''),
    editorialFallback: Boolean(ac?.editorial?.fallback || pack.editorial?.fallback),
    reasoningEnabled: Boolean(ir?.enabled || irOwns || reasoningPattern?.enabled),
    reasoningOwnsExecutive: irOwns || Boolean(cxr?.executive),
    reasoningSource: asText(
      ir?.reasoning_source || reasoningPattern?.source || (cxr?.enabled ? 'contradiction_reasoning' : ''),
      ''
    ),
    reasoningFamily: asText(
      ir?.reasoning_family?.family_label ||
        ir?.reasoning_family?.family_id ||
        ir?.family_id ||
        reasoningPattern?.family_id,
      ''
    ),
    reasoningMode: asText(ir?.adversarial_mode || ir?.habit_id || reasoningPattern?.pattern_id, ''),
    noveltyBand: asText(novelty?.band || novelty?.novelty_band, ''),
    noveltyScore: novelty?.novelty_score ?? novelty?.score ?? null,
    ecrScore: ecr?.ecr ?? ecr?.score ?? ac?.evidence_to_conclusion_ratio ?? null,
    contradictionEnabled: Boolean(cxr?.enabled),
    booksEnabled: Boolean(books?.enabled),
    bookFrameworks: asList(books?.frameworks || academy.book_frameworks, 6),
    ideEnabled: Boolean(ide?.active),
    iafEnabled: Boolean(iaf?.enabled),
    irwEnabled: Boolean(irw?.enabled),
    reportType: asText(irw?.report_type || irwReport?.report_type, ''),
    reportTables: Array.isArray(irw?.tables) ? irw.tables : Array.isArray(iaf?.report_tables) ? iaf.report_tables : [],
    chartRecommendations: Array.isArray(irw?.chart_recommendations)
      ? irw.chart_recommendations
      : Array.isArray(iaf?.chart_recommendations)
        ? iaf.chart_recommendations
        : [],
    sectionOwners: iaf?.section_owners || ac?.section_owners || {},
    publicOwnerLabels: iaf?.public_owner_labels || {},
    analystOpinions: iaf?.analyst_opinions || null,
    intelligenceLayer: ail
      ? {
          enabled: true,
          ticker: asText(ail.ticker || ailDossier.ticker, ''),
          company: asText(ail.company || ailDossier.company, ''),
          dossierVersion: ailDossier.version ?? null,
          hints: asList(ail.ask_agi_hints, 4),
          thesis: {
            bull: ailThesis.bull?.probability ?? null,
            base: ailThesis.base?.probability ?? null,
            bear: ailThesis.bear?.probability ?? null,
            explanation: asList(ailThesis.explanation, 4),
          },
          forecastConfidence: ailForecast.confidence ?? ail.prediction_confidence ?? null,
          forecastId: asText(ailForecast.prediction_id, ''),
          scenario: ailForecast.scenario || {},
          distributions: Array.isArray(ailForecast.distributions)
            ? ailForecast.distributions.slice(0, 8).map((d) => ({
                metric: asText(d.metric, ''),
                unit: asText(d.unit, ''),
                p10: d.p10 ?? null,
                p50: d.p50 ?? null,
                p90: d.p90 ?? null,
              }))
            : [],
          events: asList(ail.events, 6).map((e) =>
            typeof e === 'string'
              ? e
              : asText(e.category || e.title || e.new_value, '')
          ),
          supportingEvidenceIds: asList(ail.supporting_evidence_ids, 8),
          contradictoryEvidenceIds: asList(ail.contradictory_evidence_ids, 8),
          graphCount: ail.knowledge_graph?.count ?? (ail.knowledge_graph?.relationships || []).length,
          auditId: asText(ail.audit_trail?.audit_id, ''),
        }
      : null,
    ticker: ca.ticker || dossier.ticker || ail?.ticker || pack.entities?.primary_ticker || null,
    investmentOfficeOs,
  };
}
