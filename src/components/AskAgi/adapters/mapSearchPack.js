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

  // Executive Summary — IRP + IC (+ ACV3 framing). Not IDE scores.
  const executive =
    asText(ac?.executive) ||
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

  // Risks & Catalysts — CA primary
  const risks = asList(ca.risks || pack.key_risks || [], 8).map((r) => ({ risk: r }));
  const catalysts = asList(ca.catalysts || pack.key_catalysts || [], 8);

  // Bull/Base/Bear — IRP thesis primary
  const bull = asList(thesis.bull_case || pack.bull_case || pack.answer?.bull_case || ca.bull_case, 6);
  const base = asList(thesis.neutral_case || briefing.base_case || ca.base_case, 6);
  const bear = asList(thesis.bear_case || pack.bear_case || pack.answer?.bear_case || ca.bear_case, 6);

  // Conclusion — IC + IRP (not IDE essay)
  const conclusion =
    asText(enrich.current_outlook) ||
    asText(briefing.current_outlook) ||
    asText(pack.current_outlook) ||
    asText(ac?.thesis) ||
    asText(ca.investment_thesis) ||
    executive;

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
    ticker: ca.ticker || dossier.ticker || pack.entities?.primary_ticker || null,
    freshness: (() => {
      const raw = pack.freshness_indicator || '';
      if (!raw || /unknown|n\/a/i.test(raw)) return 'Current';
      return asText(raw, 'Current');
    })(),

    // 1. Executive Summary
    executive,

    // 2. Institutional View — IRP / house view
    stance,
    stanceTone: toneForStance(stance),
    confidence,
    conviction: confidence == null ? 'Developing' : confidence >= 80 ? 'High' : confidence >= 60 ? 'Medium' : 'Developing',
    horizon: asText(hv.investment_horizon || '12–24 Months', '12–24 Months'),
    changeVsPrevious: asText(
      cm?.what_changed?.max_significance || pack.whats_changed?.direction || 'Stable',
      'Stable'
    ),
    readiness: recoStatus.blocked ? 'Research note complete' : 'Institutional Grade',

    // 3. Decision Scorecard — IDE scores only
    decisionScorecard: ide
      ? {
          overallScore: ideSummary.overall_score ?? ide.overall_score ?? null,
          investmentGrade: asText(
            ideSummary.investment_grade || ide.investment_grade,
            gradeFromScore(ideSummary.overall_score ?? ide.overall_score) || ''
          ),
          confidence: pct(ideSummary.confidence_pct) ?? confidence,
          expectedReturn12m: ideSummary.expected_return_12m_pct ?? null,
          bullCase: ideSummary.bull_case_pct ?? null,
          baseCase: ideSummary.base_case_pct ?? null,
          bearCase: ideSummary.bear_case_pct ?? null,
          probabilityWeighted: ideSummary.probability_weighted_return_pct ?? null,
          riskReward: ideSummary.risk_reward ?? null,
          scoreChips,
          confidenceRows,
          gateBlocked: Boolean(ideSummary.gate_blocked),
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
          ? 'Institutional recommendation is withheld until validated evidence coverage clears the bar.'
          : 'Evidence coverage supports institutional analysis — not an automatic trade instruction.'
      ),
      detail: asText(recoStatus.detail, ''),
      gaps: asList(recoStatus.knowledge_gaps || ac?.knowledge_gaps, 8),
      coverage,
    },

    explore,
    ideEnabled: Boolean(ide?.active),
    acEnabled: Boolean(ac?.enabled),
  };
}
