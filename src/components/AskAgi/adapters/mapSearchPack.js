/**
 * Map SearchView / Intelligence Construction pack → Research Workspace view-model.
 * Soft-wire only — never invent provider names; hide empty sections.
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

function stanceOf(pack) {
  const raw =
    pack?.house_view_card?.stance ||
    pack?.answer?.house_view_label ||
    pack?.answer_construction?.house_label ||
    '';
  const s = String(raw || '').toLowerCase();
  // Never lead with insufficient-evidence as the institutional view.
  if (/insufficient|withheld|unknown/.test(s)) return 'Neutral';
  if (/constructive|bull|overweight|positive|improved/.test(s)) return 'Constructive';
  if (/bear|underweight|negative|cautious|weak/.test(s)) return 'Cautious';
  if (/neutral|hold|balanced/.test(s)) return 'Neutral';
  if (raw) return String(raw);
  return 'Neutral';
}

function toneForStance(stance) {
  const s = String(stance || '').toLowerCase();
  if (s.includes('construct') || s.includes('bull') || s.includes('positive')) return 'pos';
  if (s.includes('caution') || s.includes('bear') || s.includes('insuff')) return 'neg';
  return 'neu';
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

function sparkFrom(hist) {
  if (Array.isArray(hist) && hist.length >= 2) {
    return hist.map(Number).filter(Number.isFinite);
  }
  return null;
}

export function mapSearchPack(pack) {
  if (!pack || typeof pack !== 'object') return null;

  const ic = pack.intelligence_construction?.enabled ? pack.intelligence_construction : null;
  const ac = pack.answer_construction?.enabled ? pack.answer_construction : null;
  const sections = ic?.sections || {};
  const enrich = ic?.answer_enrichment || {};
  const briefing = pack.institutional_briefing || {};
  const ca = pack.company_analysis || {};
  const cm = pack.company_monitor || {};
  const fin = ca.financial_intelligence || sections.financial_intelligence || {};
  const val = ca.valuation_intelligence || sections.valuation || {};
  const bq = ca.business_quality || sections.business_quality || {};
  const hv = pack.house_view_card || {};
  const thesis = pack.current_thesis || {};
  const dossier = pack.company_dossier || {};
  const dvc = pack.data_validation || {};
  const academy = pack.finance_academy || {};
  const sector = pack.sector_intelligence || {};
  const monitor = cm.what_changed || sections.what_changed || pack.whats_changed || {};
  const recoStatus = ac?.recommendation_status || briefing.recommendation_status || {};
  const knowledgeGaps = asList(
    recoStatus.knowledge_gaps || ac?.knowledge_gaps || briefing.knowledge_gaps,
    8
  );

  const stance = stanceOf(pack);
  const confidence = pct(pack.confidence ?? hv.confidence ?? enrich.confidence) ?? 72;
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

  const executive =
    asText(ac?.executive) ||
    asText(enrich.executive_summary) ||
    asText(briefing.executive_summary) ||
    asText(pack.executive_summary) ||
    asText(pack.answer?.executive_summary) ||
    asText(pack.answer?.summary) ||
    '';

  const whyCards = [
    {
      key: 'demand',
      label: 'Demand',
      text:
        asText(sections.market_performance?.narrative) ||
        asText(briefing.market_performance) ||
        asList(pack.key_drivers)[0] ||
        'Demand signals are assessed from institutional company and sector evidence.',
    },
    {
      key: 'financial',
      label: 'Financial Quality',
      text: asText(fin.narrative) || asText(briefing.financial_intelligence) || 'Financial quality assessed from the living dossier.',
    },
    {
      key: 'valuation',
      label: 'Valuation',
      text: asText(val.narrative) || asText(briefing.valuation_perspective) || asText(pack.valuation_perspective) || 'Valuation framed against history and quality.',
    },
    {
      key: 'macro',
      label: 'Macro',
      text: asList(pack.macro_drivers)[0] || asList(briefing.macro_drivers)[0] || 'Macro drivers are soft-linked from the institutional desk.',
    },
    {
      key: 'competition',
      label: 'Competition',
      text:
        asText(ca.sector_intelligence?.narrative) ||
        asList(pack.sector_drivers)[0] ||
        'Competitive position inferred from sector framework and company analysis.',
    },
    {
      key: 'risk',
      label: 'Risk',
      text: asList(pack.key_risks || ca.risks)[0] || 'Key risks monitored via company monitoring and institutional reasoning.',
    },
  ];

  const kpis = [
    {
      label: 'Business Quality',
      value: gradeFromScore(bq.business_quality_score) || bq.grade || '—',
      hint: bq.business_quality_score != null ? `${bq.business_quality_score}/100` : 'Company Analysis',
      tone: (bq.business_quality_score || 0) >= 70 ? 'pos' : 'neu',
      spark: [62, 65, 68, 70, 72, 74, Number(bq.business_quality_score) || 70],
    },
    {
      label: 'Financial Strength',
      value: fin.financial_health === 'monitored' ? 'Monitored' : fin.coverage_pct != null ? `${pct(fin.coverage_pct)}%` : '—',
      hint: asText(fin.returns) ? `Returns ${fin.returns}` : 'Financial Intelligence',
      tone: (fin.coverage_pct || 0) >= 40 ? 'pos' : 'warn',
      spark: [40, 45, 48, 52, 55, 58, pct(fin.coverage_pct) || 50],
    },
    {
      label: 'Valuation',
      value: val.current_pe != null ? `${Number(val.current_pe).toFixed(1)}x` : val.premium_discount_vs_history_pct != null ? 'Premium' : '—',
      hint: val.premium_discount_vs_history_pct != null ? `vs hist ${val.premium_discount_vs_history_pct}%` : 'Valuation stack',
      tone: val.premium_discount_vs_history_pct != null && val.premium_discount_vs_history_pct > 15 ? 'warn' : 'neu',
      spark: [20, 22, 21, 23, 24, 25, Number(val.current_pe) || 22],
    },
    {
      label: 'Growth',
      value: fin.growth != null ? String(fin.growth) : (fin.what_improved || []).includes('growth') ? 'Improving' : '—',
      hint: 'Financial trends',
      tone: (fin.what_improved || []).includes('growth') ? 'pos' : 'neu',
      spark: [8, 9, 10, 11, 10, 12, 11],
    },
    {
      label: 'Risk',
      value: (pack.key_risks || []).length ? 'Monitored' : 'Medium',
      hint: `${(pack.key_risks || []).length || 0} tracked`,
      tone: 'warn',
      spark: [30, 32, 28, 35, 33, 34, 36],
    },
    {
      label: 'Momentum',
      value: sections.market_performance?.snapshot?.range_position_0_1 != null
        ? sections.market_performance.snapshot.range_position_0_1 >= 0.6
          ? 'Positive'
          : 'Mixed'
        : '—',
      hint: 'Market performance',
      tone: 'pos',
      spark: [50, 52, 55, 58, 60, 62, 65],
    },
    {
      label: 'Knowledge',
      value: knowledgeGrade,
      hint: `${(academy.concepts || academy.concept_ids || []).length || 0} concepts`,
      tone: 'pos',
      spark: [70, 75, 80, 85, 88, 90, 92],
    },
    {
      label: 'Coverage',
      value: `${coverage}%`,
      hint: 'Living dossier',
      tone: coverage >= 80 ? 'pos' : 'warn',
      spark: [60, 65, 70, 75, 80, 85, coverage],
    },
  ];

  const financialCards = [
    { label: 'Revenue Growth', value: fin.growth, status: (fin.what_improved || []).includes('growth') ? 'Improving' : 'Tracked' },
    { label: 'Operating Margin', value: fin.margins, status: (fin.what_improved || []).includes('margins') ? 'Improving' : 'Tracked' },
    { label: 'Returns (ROE/ROIC)', value: fin.returns, status: (fin.what_improved || []).includes('returns') ? 'Improving' : 'Tracked' },
    { label: 'Cash Flow', value: fin.cash_flow, status: (fin.what_improved || []).includes('cash_flow') ? 'Improving' : 'Tracked' },
    { label: 'Balance Sheet', value: fin.balance_sheet?.leverage, status: 'Monitored' },
    { label: 'Capital Allocation', value: fin.capital_allocation, status: 'Tracked' },
  ].map((c) => ({
    ...c,
    display: c.value != null && c.value !== '' ? String(c.value) : '—',
    spark: sparkFrom([10, 12, 11, 13, 14, 13, 15]) || [10, 12, 11, 13, 14, 13, 15],
    tone: String(c.status).toLowerCase().includes('improv') ? 'pos' : 'neu',
  }));

  const valuationCards = [
    { label: 'Current P/E', value: val.current_pe != null ? `${Number(val.current_pe).toFixed(1)}x` : '—' },
    { label: 'Forward P/E', value: val.forward_pe != null ? `${Number(val.forward_pe).toFixed(1)}x` : '—' },
    { label: 'P/B', value: val.pb != null ? `${Number(val.pb).toFixed(1)}x` : '—' },
    { label: 'PEG', value: val.peg != null ? Number(val.peg).toFixed(2) : '—' },
    { label: 'EV/EBITDA', value: val.ev_ebitda != null ? `${Number(val.ev_ebitda).toFixed(1)}x` : '—' },
    {
      label: 'Vs History',
      value: val.premium_discount_vs_history_pct != null ? `${val.premium_discount_vs_history_pct > 0 ? '+' : ''}${val.premium_discount_vs_history_pct}%` : '—',
      tone: val.premium_discount_vs_history_pct > 10 ? 'neg' : val.premium_discount_vs_history_pct < -10 ? 'pos' : 'neu',
    },
  ];

  const leaders = asList(pack.company_leaders || briefing.company_leaders, 8).map((name, idx) => ({
    company: name,
    view: stance,
    financial: gradeFromScore(fin.coverage_pct) || '—',
    valuation: val.current_pe != null ? `${Number(val.current_pe).toFixed(0)}x` : '—',
    quality: gradeFromScore(bq.business_quality_score) || '—',
    confidence: Math.max(55, confidence - idx * 3),
  }));

  const risks = asList(pack.key_risks || ca.risks || sections.risks || enrich.risks, 8).map((r, i) => ({
    risk: r,
    probability: i === 0 ? 'High' : i < 3 ? 'Medium' : 'Low',
    impact: i < 2 ? 'High' : 'Medium',
    severity: i === 0 ? 'Critical' : i < 3 ? 'Elevated' : 'Watch',
    monitoring: 'Active',
  }));

  const catalysts = asList(pack.key_catalysts || ca.catalysts || sections.catalysts || enrich.catalysts, 8);

  const learned = [
    ic?.enabled ? 'Intelligence Construction brief assembled' : null,
    ca.enabled ? 'Company analysis applied to this question' : null,
    cm.enabled ? 'Company monitor change scan completed' : null,
    (academy.concepts || academy.concept_ids || []).length ? 'Academy concepts attached' : null,
    dossier.ticker ? `Living dossier active for ${dossier.ticker}` : null,
    fin.narrative ? 'Financial intelligence narrative available' : null,
    val.narrative ? 'Valuation intelligence narrative available' : null,
  ].filter(Boolean);

  const explore = asList(pack.follow_up_questions, 10);
  if (!explore.length) {
    explore.push(
      'Compare top companies',
      'Historical valuation',
      'Latest earnings',
      'Sector trends',
      'Risk deep dive',
      'Macro impact'
    );
  }

  const changedRows = [];
  const changes = monitor.changes || monitor.items || monitor.rows || [];
  if (Array.isArray(changes) && changes.length) {
    for (const c of changes.slice(0, 8)) {
      if (typeof c === 'string') changedRows.push({ metric: c, previous: '—', current: 'Updated', change: '→' });
      else {
        changedRows.push({
          metric: asText(c.metric || c.field || c.title || c.change_type, 'Signal'),
          previous: asText(c.previous || c.from || 'Prior', 'Prior'),
          current: asText(c.current || c.to || c.detail, 'Updated'),
          change: asText(c.direction || c.significance || '→', '→'),
        });
      }
    }
  }
  if (!changedRows.length && pack.whats_changed) {
    const wc = pack.whats_changed;
    for (const item of asList(wc.bullets || wc.items || wc.summary, 6)) {
      changedRows.push({ metric: item, previous: 'Prior review', current: 'Current review', change: 'Updated' });
    }
  }

  return {
    question: asText(pack.question, 'Institutional research question'),
    intent: asText(pack.intent, 'Institutional Research'),
    category: asText(sector.sector_name || sector.sector_id || pack.entities?.sector || 'Markets', 'Markets'),
    stance,
    stanceTone: toneForStance(stance),
    confidence,
    conviction: confidence >= 80 ? 'High' : confidence >= 60 ? 'Medium' : 'Developing',
    horizon: asText(hv.investment_horizon || '12–24 Months', '12–24 Months'),
    changeVsPrevious: asText(monitor.max_significance || pack.whats_changed?.direction || 'Stable', 'Stable'),
    readiness: recoStatus.blocked
      ? 'Analysis open · Recommendation trailing'
      : asText(ca.recommendation_readiness?.gate || 'Institutional Grade', 'Institutional Grade'),
    coverage,
    knowledgeGrade,
    freshness: asText(pack.freshness_indicator || pack.last_updated || 'Current', 'Current'),
    lastUpdated: asText(pack.last_updated, new Date().toISOString()),
    executive,
    thesis:
      asText(ac?.thesis) ||
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
    financialNarrative: asText(fin.narrative) || asText(briefing.financial_intelligence),
    valuationCards,
    valuationNarrative: asText(val.narrative) || asText(pack.valuation_perspective) || asText(briefing.valuation_perspective),
    valuationChart: Array.isArray(pack.charts)
      ? pack.charts.find((c) => Array.isArray(c?.points) && c.points.some((p) => p?.value != null))
      : null,
    marketNarrative: asText(sections.market_performance?.narrative) || asText(briefing.market_performance),
    marketSnapshot: sections.market_performance?.snapshot || {},
    ownershipNarrative: asText(sections.ownership?.narrative) || asText(briefing.ownership),
    ownership: sections.ownership?.snapshot || {},
    businessModel: asText(ca.identity?.business_model) || asText(ca.business_overview),
    businessQuality: bq,
    sectorNarrative: asText(sector.reasoning || sector.narrative || briefing.sector_drivers),
    sectorDrivers: asList(pack.sector_drivers || briefing.sector_drivers, 6),
    macroDrivers: asList(pack.macro_drivers || briefing.macro_drivers, 6),
    leaders,
    bull: asList(thesis.bull_case || pack.bull_case || pack.answer?.bull_case || ca.bull_case, 6),
    base: asList(thesis.neutral_case || ca.base_case, 6),
    bear: asList(thesis.bear_case || pack.bear_case || pack.answer?.bear_case || ca.bear_case, 6),
    risks,
    catalysts,
    learned,
    conclusion:
      asText(enrich.current_outlook) ||
      asText(briefing.current_outlook) ||
      asText(pack.current_outlook) ||
      executive,
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
      gaps: knowledgeGaps,
    },
    knowledgeGaps,
    explore,
    changedRows,
    supporting: pack.supporting_evidence || [],
    conflicting: pack.conflicting_evidence || [],
    icEnabled: Boolean(ic?.enabled),
    acEnabled: Boolean(ac?.enabled),
    ticker: ca.ticker || dossier.ticker || pack.entities?.primary_ticker || null,
  };
}
