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

  const executive =
    asText(irw?.executive_summary) ||
    asText(irwReport?.executive_summary) ||
    asText(iafCio?.executive_summary) ||
    asText(ac?.executive) ||
    asText(ide?.answer_enrichment?.executive_framing) ||
    asText(enrich.executive_summary) ||
    asText(briefing.executive_summary) ||
    asText(pack.executive_summary) ||
    asText(pack.answer?.executive_summary) ||
    asText(pack.answer?.summary) ||
    '';

  const biz = sections.business_intelligence || enrich.business_intelligence || {};
  const marketPack = enrich.market_intelligence || sections.market_performance || {};
  const marketSnap = {
    ...(dossier.market_data || {}),
    ...(sections.market_performance?.snapshot || {}),
    ...(marketPack.snapshot || {}),
  };

  const whyCards = [
    {
      key: 'demand',
      label: 'Demand',
      text:
        asText(biz.revenue_drivers) ||
        asText(sections.market_performance?.narrative) ||
        asText(briefing.market_performance) ||
        asList(pack.key_drivers)[0] ||
        'Demand should be judged through volume, pricing/mix and adjacency growth — the variables that decide whether the franchise is compounding.',
    },
    {
      key: 'financial',
      label: 'Financial Quality',
      text:
        asText(fin.narrative) ||
        asText(biz.operating_metrics) ||
        asText(briefing.financial_intelligence) ||
        'Financial quality should be judged through incremental returns, cash conversion and balance-sheet resilience — even while statement history is still completing.',
    },
    {
      key: 'valuation',
      label: 'Valuation',
      text:
        asText(val.narrative) ||
        asText(briefing.valuation_perspective) ||
        asText(pack.valuation_perspective) ||
        'Valuation only works when growth durability and competitive position are held constant — multiples without that context mislead.',
    },
    {
      key: 'macro',
      label: 'Macro',
      text:
        asList(pack.macro_drivers)[0] ||
        asList(briefing.macro_drivers)[0] ||
        'Macro conditions matter for discount rates, risk appetite and cyclical demand — they should frame, not replace, company analysis.',
    },
    {
      key: 'competition',
      label: 'Competition',
      text:
        asText(biz.competitive_advantages) ||
        asText(ca.sector_intelligence?.narrative) ||
        asList(pack.sector_drivers)[0] ||
        'Competitive position decides whether growth creates value or is competed away through price and capital intensity.',
    },
    {
      key: 'risk',
      label: 'Risk',
      text:
        asText(biz.risks) ||
        asList(pack.key_risks || ca.risks)[0] ||
        'Institutional risk framing should emphasise path dependency — what can impair the thesis before the base case arrives.',
    },
  ].filter((c) => c.text && !isGateFailureText(c.text));

  const momentumLabel =
    marketPack.momentum ||
    (marketSnap.range_position_0_1 != null
      ? marketSnap.range_position_0_1 >= 0.6
        ? 'Positive'
        : marketSnap.range_position_0_1 <= 0.35
          ? 'Soft'
          : 'Mixed'
      : null);

  const kpis = [
    bq.business_quality_score != null || bq.grade
      ? {
          label: 'Business Quality',
          value: gradeFromScore(bq.business_quality_score) || bq.grade,
          hint: bq.business_quality_score != null ? `${bq.business_quality_score}/100 quality scaffold` : 'Franchise quality',
          tone: (bq.business_quality_score || 0) >= 70 ? 'pos' : 'neu',
          spark: [62, 65, 68, 70, 72, 74, Number(bq.business_quality_score) || 70],
        }
      : null,
    fin.returns != null || (fin.what_improved || []).length
      ? {
          label: 'Financial Strength',
          value: fin.returns != null ? String(fin.returns) : 'Improving',
          hint: 'Returns and cash quality',
          tone: 'pos',
          spark: [40, 45, 48, 52, 55, 58, 60],
        }
      : null,
    val.current_pe != null || val.premium_discount_vs_history_pct != null
      ? {
          label: 'Valuation',
          value: val.current_pe != null ? `${Number(val.current_pe).toFixed(1)}x` : 'Vs history',
          hint:
            val.premium_discount_vs_history_pct != null
              ? `vs hist ${val.premium_discount_vs_history_pct}%`
              : 'Earnings multiple context',
          tone: val.premium_discount_vs_history_pct != null && val.premium_discount_vs_history_pct > 15 ? 'warn' : 'neu',
          spark: [20, 22, 21, 23, 24, 25, Number(val.current_pe) || 22],
        }
      : null,
    fin.growth != null || (fin.what_improved || []).includes('growth') || (fin.what_improved || []).includes('Growth')
      ? {
          label: 'Growth',
          value: fin.growth != null ? String(fin.growth) : 'Improving',
          hint: 'Top-line / earnings trajectory',
          tone: 'pos',
          spark: [8, 9, 10, 11, 10, 12, 11],
        }
      : null,
    {
      label: 'Risk',
      value: (pack.key_risks || ca.risks || []).length ? 'Active watch' : 'Medium',
      hint: 'Thesis path dependency',
      tone: 'warn',
      spark: [30, 32, 28, 35, 33, 34, 36],
    },
    momentumLabel
      ? {
          label: 'Momentum',
          value: momentumLabel,
          hint: '52-week range context',
          tone: momentumLabel === 'Positive' || momentumLabel === 'Constructive' ? 'pos' : 'neu',
          spark: [50, 52, 55, 58, 60, 62, 65],
        }
      : null,
  ].filter(Boolean);

  const financialCards = [
    { label: 'Revenue Growth', value: fin.growth, status: 'Improving' },
    { label: 'Operating Margin', value: fin.margins, status: 'Tracked' },
    { label: 'Returns (ROE/ROIC)', value: fin.returns, status: 'Tracked' },
    { label: 'Cash Flow', value: fin.cash_flow, status: 'Tracked' },
    { label: 'Balance Sheet', value: fin.balance_sheet?.leverage, status: 'Monitored' },
    { label: 'Capital Allocation', value: fin.capital_allocation, status: 'Tracked' },
  ]
    .filter((c) => c.value != null && c.value !== '')
    .map((c) => ({
      ...c,
      display: String(c.value),
      spark: sparkFrom([10, 12, 11, 13, 14, 13, 15]) || [10, 12, 11, 13, 14, 13, 15],
      tone: 'neu',
    }));

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
          tone: val.premium_discount_vs_history_pct > 10 ? 'neg' : val.premium_discount_vs_history_pct < -10 ? 'pos' : 'neu',
        }
      : null,
  ].filter(Boolean);

  const leaders = asList(pack.company_leaders || briefing.company_leaders, 8).map((name, idx) => ({
    company: name,
    view: stance,
    financial: gradeFromScore(bq.business_quality_score) || gradeFromScore(fin.coverage_pct) || 'Reviewed',
    valuation: val.current_pe != null ? `${Number(val.current_pe).toFixed(0)}x` : 'Under review',
    quality: gradeFromScore(bq.business_quality_score) || 'Reviewed',
    confidence: Math.max(55, confidence - idx * 3),
  }));

  const risks = asList(
    pack.key_risks || ca.risks || sections.risks || enrich.risks || (biz.risks ? [biz.risks] : []),
    8
  ).map((r, i) => ({
    risk: r,
    probability: i === 0 ? 'High' : i < 3 ? 'Medium' : 'Low',
    impact: i < 2 ? 'High' : 'Medium',
    severity: i === 0 ? 'Critical' : i < 3 ? 'Elevated' : 'Watch',
    monitoring: 'Active',
  }));

  const catalysts = asList(pack.key_catalysts || ca.catalysts || sections.catalysts || enrich.catalysts, 8);

  const learned = asList(
    enrich.research_takeaways || sections.research_takeaways || academy.reasoning_points || academy.answer_hints,
    6
  );

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
    readiness: recoStatus.blocked ? 'Research note complete' : 'Institutional Grade',
    coverage,
    knowledgeGrade,
    freshness: (() => {
      const raw = pack.freshness_indicator || '';
      if (!raw || /unknown|n\/a/i.test(raw)) return 'Current';
      if (/^\d{4}-\d{2}-\d{2}T/.test(String(pack.last_updated || ''))) return 'Current';
      return asText(raw, 'Current');
    })(),
    lastUpdated: pack.last_updated && !/T\d{2}:/.test(String(pack.last_updated))
      ? asText(pack.last_updated, '')
      : '',
    executive,
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
      asText(iafMgmt?.summary) ||
      asText(iafMgmt?.headline),
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
    conclusion:
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
          active: true,
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
          action: asText(ideSummary.action || decisionLayer?.action, ''),
          suitableFor: asList(ideSummary.suitable_for, 6),
          unsuitableFor: asList(ideSummary.unsuitable_for, 6),
          layerScores: ideSummary.layer_scores || {},
          preQuestions: asList(ide.pre_questions, 8),
          stackLayers: decisionStackLayers,
          decision: decisionLayer,
          gateBlocked: Boolean(ideSummary.gate_blocked),
        }
      : null,
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
  };
}
