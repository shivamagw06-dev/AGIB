import { useEffect, useMemo, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  Activity,
  AlertTriangle,
  Bookmark,
  BookOpen,
  Building2,
  FileSpreadsheet,
  FileText,
  Home,
  Layers,
  LineChart,
  Moon,
  Search,
  Settings,
  Share2,
  Shield,
  Sparkles,
  Star,
  TrendingUp,
} from 'lucide-react';
import { Line, LineChart as RLineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { mapSearchPack } from '@/components/AskAgi/adapters/mapSearchPack';
import '@/components/AskAgi/researchWorkspace.css';

const NAV = [
  { to: '/', label: 'Home', icon: Home },
  { to: '/ask', label: 'Ask AGI', icon: Sparkles },
  { to: '/research', label: 'Research', icon: BookOpen },
  { to: '/markets', label: 'Markets', icon: LineChart },
  { to: '/company-updates', label: 'Companies', icon: Building2 },
  { to: '/sectors/it-services', label: 'Sectors', icon: Layers },
  { to: '/themes', label: 'Themes', icon: Activity },
  { to: '/portfolio', label: 'Portfolio', icon: TrendingUp },
  { to: '/workspace', label: 'Watchlists', icon: Star },
  { to: '/admin/academy', label: 'Academy', icon: BookOpen },
  { to: '/admin/knowledge', label: 'Knowledge', icon: Layers, admin: true },
  { to: '/admin/mission-control', label: 'Mission Control', icon: Shield, admin: true },
  { to: '/admin/system', label: 'System Health', icon: Activity, admin: true },
  { to: '/admin', label: 'Settings', icon: Settings, admin: true },
];

function Section({ id, kicker, title, children, className = '' }) {
  return (
    <section id={id} className={`rw-card scroll-mt-24 ${className}`}>
      {kicker ? <p className="rw-kicker">{kicker}</p> : null}
      {title ? <h2 className="rw-title">{title}</h2> : null}
      {children}
    </section>
  );
}

function Donut({ value = 0 }) {
  const v = Math.max(0, Math.min(100, Number(value) || 0));
  const r = 54;
  const c = 2 * Math.PI * r;
  const offset = c - (v / 100) * c;
  return (
    <div className="relative mx-auto h-[140px] w-[140px]">
      <svg viewBox="0 0 140 140" className="h-full w-full -rotate-90">
        <circle cx="70" cy="70" r={r} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="12" />
        <circle
          cx="70"
          cy="70"
          r={r}
          fill="none"
          stroke="var(--rw-pos)"
          strokeWidth="12"
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <p className="text-3xl font-bold tabular-nums">{v || '—'}</p>
        <p className="text-[10px] uppercase tracking-wide text-[var(--rw-caption)]">Confidence</p>
      </div>
    </div>
  );
}

function MetricGrid({ items }) {
  if (!items?.length) return null;
  return (
    <div className="rw-grid-3">
      {items.map((c) => (
        <div key={c.label} className={`rw-kpi tone-${c.tone || 'neu'}`}>
          <p className="label">{c.label}</p>
          <p className="value text-[18px]">{c.value}</p>
        </div>
      ))}
    </div>
  );
}

export default function ResearchWorkspace({
  pack,
  loading = false,
  error = null,
  question = '',
  onAsk,
  onSave,
  savedFlash = false,
}) {
  const navigate = useNavigate();
  const location = useLocation();
  const [draft, setDraft] = useState(question || '');
  const vm = useMemo(() => mapSearchPack(pack), [pack]);

  useEffect(() => {
    setDraft(question || '');
  }, [question]);

  const submit = (q) => {
    const next = String(q || draft || '').trim();
    if (!next) return;
    onAsk?.(next);
  };

  const isActive = (to) => {
    if (to === '/ask') return location.pathname === '/ask';
    if (to === '/') return location.pathname === '/';
    return location.pathname === to || location.pathname.startsWith(`${to}/`);
  };

  const exportJson = () => {
    if (!pack) return;
    const blob = new Blob([JSON.stringify(pack, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `agi-research-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const chartData = useMemo(() => {
    const points = vm?.valuationChart?.points;
    if (!Array.isArray(points)) return [];
    return points
      .map((p, i) => ({
        name: p.label || p.date || String(i + 1),
        value: Number(p.value),
      }))
      .filter((p) => Number.isFinite(p.value));
  }, [vm]);

  const ds = vm?.decisionScorecard;

  return (
    <div className="agi-research">
      <div className="rw-shell">
        <aside className="rw-sidebar">
          <div className="rw-brand">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[var(--rw-blue-soft)] text-[var(--rw-blue)] font-bold">
              AGI
            </div>
            <div>
              <strong>AGI</strong>
              <span>Intelligence Platform</span>
            </div>
          </div>

          <div>
            <p className="rw-nav-label">Intelligence Platform</p>
            <nav className="rw-nav space-y-0.5">
              {NAV.filter((n) => !n.admin).map((item) => {
                const Icon = item.icon;
                return (
                  <Link key={item.to} to={item.to} className={isActive(item.to) ? 'active' : ''}>
                    <Icon size={15} />
                    {item.label}
                  </Link>
                );
              })}
            </nav>
          </div>

          <div>
            <p className="rw-nav-label">Admin</p>
            <nav className="rw-nav space-y-0.5">
              {NAV.filter((n) => n.admin).map((item) => {
                const Icon = item.icon;
                return (
                  <Link key={item.to} to={item.to}>
                    <Icon size={15} />
                    {item.label}
                  </Link>
                );
              })}
            </nav>
          </div>

          <div className="rw-side-foot">
            <p>AGI Platform v2.0.0</p>
            <p className="ok mt-1">● All Systems Operational</p>
          </div>
        </aside>

        <div className="rw-main">
          <header className="rw-topbar">
            <div className="logo">AGI | ASK AGI</div>
            <form
              className="rw-search"
              onSubmit={(e) => {
                e.preventDefault();
                submit(draft);
              }}
            >
              <Search size={16} className="text-[var(--rw-caption)]" />
              <input
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                placeholder="Ask anything about markets, companies, sectors, macro..."
              />
            </form>
            <div className="rw-actions">
              <button type="button" className="rw-iconbtn" onClick={onSave} title="Save">
                <Bookmark size={15} />
                <span className="label">{savedFlash ? 'Saved' : 'Save'}</span>
              </button>
              <button type="button" className="rw-iconbtn" onClick={onSave} title="Bookmark">
                <Star size={15} />
                <span className="label">Bookmark</span>
              </button>
              <button type="button" className="rw-iconbtn" onClick={exportJson} title="Export">
                <FileText size={15} />
                <span className="label">PDF</span>
              </button>
              <button type="button" className="rw-iconbtn" onClick={exportJson} title="Export Excel">
                <FileSpreadsheet size={15} />
                <span className="label">Excel</span>
              </button>
              <button
                type="button"
                className="rw-iconbtn"
                title="Share"
                onClick={() => navigator.clipboard?.writeText(window.location.href)}
              >
                <Share2 size={15} />
                <span className="label">Share</span>
              </button>
              <button type="button" className="rw-iconbtn" title="Dark mode">
                <Moon size={15} />
              </button>
              <button type="button" className="rw-iconbtn rw-avatar" title="Profile">
                AD
              </button>
            </div>
          </header>

          <div className="rw-content">
            {!question && !loading && (
              <Section kicker="Ask AGI" title="Institutional Investment Research">
                <p className="rw-body">
                  Ask any institutional question. Answers open as a single research report — one purpose
                  per section, one coherent investment voice.
                </p>
                <div className="rw-explore mt-4">
                  {[
                    'How is the Indian IT Services sector doing?',
                    'Should I invest in HDFC Bank?',
                    'What changed in Indian banks this quarter?',
                    'Is Nifty IT expensive versus history?',
                  ].map((q) => (
                    <button key={q} type="button" onClick={() => submit(q)}>
                      {q}
                    </button>
                  ))}
                </div>
              </Section>
            )}

            {loading && (
              <div className="rw-loading" aria-busy="true">
                <div className="rw-skel h-28" />
                <div className="rw-skel h-40" />
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="rw-skel" />
                  <div className="rw-skel" />
                  <div className="rw-skel" />
                  <div className="rw-skel" />
                </div>
              </div>
            )}

            {error && !loading && (
              <Section kicker="Desk status" title="Temporarily unavailable">
                <p className="rw-body">
                  The research desk could not complete this briefing. Your question was preserved —
                  try again in a moment.
                </p>
              </Section>
            )}

            {vm && !loading && (
              <>
                <div className="rw-qhead">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <h1>{vm.question}</h1>
                    <button type="button" className="rw-iconbtn" onClick={onSave}>
                      <Star size={14} /> Follow
                    </button>
                  </div>
                  <div className="rw-chips">
                    <span className="rw-chip blue">{vm.intent}</span>
                    <span className="rw-chip blue">{vm.category}</span>
                    {vm.ticker ? <span className="rw-chip muted">{vm.ticker}</span> : null}
                  </div>
                  <p className="rw-meta">
                    Last research refresh: {vm.freshness}
                    {vm.ticker ? ` · Focus: ${vm.ticker}` : ''}
                  </p>
                </div>

                <div className="rw-grid-2">
                  <Section id="executive" kicker="01" title="Executive Summary">
                    <p className="rw-body">{vm.executive || 'Institutional summary assembling…'}</p>
                  </Section>
                  <Section id="view" kicker="02" title="Institutional View">
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <p className="rw-mini">Current View</p>
                        <p className={`rw-view-value tone-${vm.stanceTone}`}>{vm.stance}</p>
                      </div>
                      <div>
                        <p className="rw-mini">Conviction</p>
                        <p className="rw-view-value">
                          {vm.confidence != null ? `${vm.confidence}%` : '—'}
                        </p>
                        <p className="rw-mini">{vm.conviction}</p>
                      </div>
                      <div>
                        <p className="rw-mini">Time Horizon</p>
                        <p className="font-semibold">{vm.horizon}</p>
                      </div>
                      <div>
                        <p className="rw-mini">Change vs Previous</p>
                        <p className="font-semibold tone-pos">{vm.changeVsPrevious}</p>
                      </div>
                    </div>
                  </Section>
                </div>

                {ds ? (
                  <Section id="scorecard" kicker="03" title="Decision Scorecard">
                    <p className="rw-body mb-4">
                      Layered institutional scores only — detailed analysis lives in the sections below.
                    </p>
                    <div className="rw-decision-scorecard">
                      <div className="rw-decision-hero">
                        <p className="rw-mini">Overall Score</p>
                        <p className="rw-decision-score">
                          {ds.overallScore != null ? ds.overallScore : '—'}
                          <span>/100</span>
                        </p>
                        <p className="rw-decision-grade">
                          Grade {ds.investmentGrade || '—'}
                          {ds.confidence != null ? ` · Confidence ${ds.confidence}%` : ''}
                        </p>
                      </div>
                      <div className="rw-decision-metrics">
                        {[
                          ['Expected Return (12m)', ds.expectedReturn12m, '%'],
                          ['Bull', ds.bullCase, '%'],
                          ['Base', ds.baseCase, '%'],
                          ['Bear', ds.bearCase, '%'],
                          ['Prob. Weighted', ds.probabilityWeighted, '%'],
                          ['Risk / Reward', ds.riskReward, ''],
                        ].map(([label, value, suffix]) => (
                          <div key={label} className="rw-why-card">
                            <h4>{label}</h4>
                            <p className="tabular-nums text-[var(--rw-ink)] font-semibold">
                              {value == null || Number.isNaN(Number(value))
                                ? '—'
                                : `${Number(value) > 0 && suffix === '%' ? '+' : ''}${value}${suffix}`}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                    {ds.scoreChips?.length ? (
                      <div className="rw-score-chips mt-4">
                        {ds.scoreChips.map((chip) => (
                          <div key={chip.label} className="rw-score-chip">
                            <span>{chip.label}</span>
                            <strong>{chip.value}</strong>
                            <em>{chip.grade}</em>
                          </div>
                        ))}
                      </div>
                    ) : null}
                    {ds.confidenceRows?.length ? (
                      <div className="rw-donut-wrap mt-5">
                        <Donut value={ds.confidence || 0} />
                        <ul className="space-y-2 text-sm text-[var(--rw-soft)]">
                          {ds.confidenceRows.map((row) => (
                            <li
                              key={row.label}
                              className="flex justify-between border-b border-[var(--rw-border)] pb-1"
                            >
                              <span>{row.label}</span>
                              <span className="tabular-nums">{row.value}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    ) : null}
                  </Section>
                ) : null}

                <Section id="business" kicker="04" title="Business Intelligence">
                  <p className="rw-body">
                    {vm.business?.narrative ||
                      vm.business?.model ||
                      'Business quality is assessed through model, moat, management and competitive position.'}
                  </p>
                  <div className="mt-3 grid grid-cols-1 gap-2 md:grid-cols-2">
                    {[
                      ['Business model', vm.business?.model],
                      ['Industry', vm.business?.industry],
                      ['Competitive position', vm.business?.moat],
                      ['Revenue drivers', vm.business?.revenueDrivers],
                      ['Management', vm.business?.management],
                      ['Pricing power', vm.business?.pricingPower],
                    ]
                      .filter(([, text]) => text)
                      .map(([title, text]) => (
                        <div key={title} className="rw-why-card">
                          <h4>{title}</h4>
                          <p>{text}</p>
                        </div>
                      ))}
                  </div>
                  {vm.business?.qualityScore != null ? (
                    <p className="rw-mini mt-3">
                      Business quality {vm.business.qualityScore}/100
                      {vm.business.qualityGrade ? ` (${vm.business.qualityGrade})` : ''}
                    </p>
                  ) : null}
                </Section>

                <Section id="financials" kicker="05" title="Financial Intelligence">
                  {vm.financialNarrative ? <p className="rw-body mb-4">{vm.financialNarrative}</p> : null}
                  <MetricGrid items={vm.financialCards} />
                  {(vm.financialImproved?.length || vm.financialDeteriorated?.length) && (
                    <div className="rw-grid-2 mt-4">
                      {vm.financialImproved?.length ? (
                        <div>
                          <p className="rw-mini tone-pos">Improving</p>
                          <ul className="mt-1 space-y-1 text-sm text-[var(--rw-soft)]">
                            {vm.financialImproved.map((x) => (
                              <li key={x}>• {x}</li>
                            ))}
                          </ul>
                        </div>
                      ) : null}
                      {vm.financialDeteriorated?.length ? (
                        <div>
                          <p className="rw-mini tone-neg">Softening</p>
                          <ul className="mt-1 space-y-1 text-sm text-[var(--rw-soft)]">
                            {vm.financialDeteriorated.map((x) => (
                              <li key={x}>• {x}</li>
                            ))}
                          </ul>
                        </div>
                      ) : null}
                    </div>
                  )}
                  {!vm.financialCards?.length && !vm.financialNarrative ? (
                    <p className="rw-empty">Financial coverage is still completing for this name.</p>
                  ) : null}
                </Section>

                <Section id="valuation" kicker="06" title="Valuation Intelligence">
                  {vm.valuationNarrative ? <p className="rw-body mb-4">{vm.valuationNarrative}</p> : null}
                  <MetricGrid items={vm.valuationCards} />
                  {chartData.length >= 2 ? (
                    <div className="h-56 mt-4 rounded-xl border border-[var(--rw-border)] bg-[var(--rw-panel-2)] p-3">
                      <ResponsiveContainer width="100%" height="100%">
                        <RLineChart data={chartData}>
                          <XAxis dataKey="name" hide />
                          <YAxis stroke="var(--rw-caption)" fontSize={11} width={40} />
                          <Tooltip
                            contentStyle={{
                              background: '#151b27',
                              border: '1px solid rgba(255,255,255,0.1)',
                              borderRadius: 8,
                            }}
                          />
                          <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={2} dot={false} />
                        </RLineChart>
                      </ResponsiveContainer>
                    </div>
                  ) : null}
                  {!vm.valuationCards?.length && !vm.valuationNarrative ? (
                    <p className="rw-empty">Valuation multiples will populate as coverage completes.</p>
                  ) : null}
                </Section>

                <div className="rw-grid-2">
                  <Section id="market" kicker="07" title="Market Intelligence">
                    {vm.marketNarrative ? <p className="rw-body mb-3">{vm.marketNarrative}</p> : null}
                    <MetricGrid
                      items={(vm.marketCards || []).map((c) => ({
                        label: c.label,
                        value: String(c.value),
                      }))}
                    />
                    {!vm.marketCards?.length && !vm.marketNarrative ? (
                      <p className="rw-empty">Market snapshot pending.</p>
                    ) : null}
                  </Section>
                  <Section id="sector" kicker="08" title="Sector Intelligence">
                    <p className="rw-body">
                      {vm.sectorNarrative ||
                        'Industry structure shapes pricing power, capital intensity and return durability.'}
                    </p>
                    {vm.sectorDrivers?.length ? (
                      <ul className="mt-3 space-y-1 text-sm text-[var(--rw-muted)]">
                        {vm.sectorDrivers.map((d) => (
                          <li key={d}>• {d}</li>
                        ))}
                      </ul>
                    ) : null}
                  </Section>
                </div>

                <Section id="macro" kicker="09" title="Macro Intelligence">
                  {vm.macroDrivers?.length ? (
                    <ul className="space-y-2 text-sm text-[var(--rw-soft)]">
                      {vm.macroDrivers.map((d) => (
                        <li key={d} className="border-b border-[var(--rw-border)] pb-2">
                          {d}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="rw-body">
                      Macro conditions matter for discount rates, risk appetite and cyclical demand —
                      they frame the company debate rather than replace it.
                    </p>
                  )}
                </Section>

                <Section id="monitor" kicker="10" title="Company Monitor">
                  {vm.houseViewReview ? (
                    <p className="rw-mini tone-warn mb-3">Material changes — house-view review suggested.</p>
                  ) : null}
                  {vm.monitorHints?.length ? (
                    <ul className="mb-3 space-y-1 text-sm text-[var(--rw-soft)]">
                      {vm.monitorHints.map((h) => (
                        <li key={h}>• {h}</li>
                      ))}
                    </ul>
                  ) : null}
                  {vm.monitorRows?.length ? (
                    <div className="overflow-x-auto">
                      <table className="rw-table">
                        <thead>
                          <tr>
                            <th>Category</th>
                            <th>Metric</th>
                            <th>Previous</th>
                            <th>Current</th>
                            <th>Change</th>
                          </tr>
                        </thead>
                        <tbody>
                          {vm.monitorRows.map((r) => (
                            <tr key={`${r.category}-${r.metric}-${r.current}`}>
                              <td className="rw-mini">{r.category}</td>
                              <td className="font-semibold text-[var(--rw-ink)]">{r.metric}</td>
                              <td>{r.previous}</td>
                              <td>{r.current}</td>
                              <td className="tone-pos">{r.change}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="rw-empty">No material monitored changes since the prior review.</p>
                  )}
                </Section>

                <div className="rw-grid-2">
                  <Section id="risks" kicker="11" title="Risks & Catalysts">
                    <div className="mb-4">
                      <p className="rw-mini mb-2">Key Risks</p>
                      {vm.risks?.length ? (
                        <ul className="space-y-2 text-sm text-[var(--rw-soft)]">
                          {vm.risks.map((r) => (
                            <li key={r.risk} className="border-b border-[var(--rw-border)] pb-2">
                              {r.risk}
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className="rw-empty">Risk inventory still forming.</p>
                      )}
                    </div>
                    <div>
                      <p className="rw-mini mb-2">Key Catalysts</p>
                      {vm.catalysts?.length ? (
                        <ul className="space-y-2 text-sm text-[var(--rw-soft)]">
                          {vm.catalysts.map((c) => (
                            <li key={c} className="border-b border-[var(--rw-border)] pb-2">
                              {c}
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className="rw-empty">Catalyst calendar pending corporate events.</p>
                      )}
                    </div>
                  </Section>
                  <Section id="scenarios" kicker="12" title="Bull · Base · Bear">
                    <div className="space-y-3">
                      {[
                        {
                          key: 'bull',
                          title: 'Bull',
                          items: vm.bull,
                          ret: vm.scenarioReturns?.bull,
                        },
                        {
                          key: 'base',
                          title: 'Base',
                          items: vm.base,
                          ret: vm.scenarioReturns?.base,
                        },
                        {
                          key: 'bear',
                          title: 'Bear',
                          items: vm.bear,
                          ret: vm.scenarioReturns?.bear,
                        },
                      ].map((s) => (
                        <div key={s.key} className={`rw-scenario ${s.key}`}>
                          <div className="flex items-center justify-between">
                            <h3 className="font-bold">{s.title}</h3>
                            {s.ret != null ? (
                              <span className="rw-mini">
                                {Number(s.ret) > 0 ? '+' : ''}
                                {s.ret}%
                              </span>
                            ) : null}
                          </div>
                          <ul className="mt-2 space-y-1 text-sm text-[var(--rw-soft)]">
                            {(s.items?.length ? s.items : ['Scenario narrative pending richer evidence.']).map(
                              (item) => (
                                <li key={item}>• {item}</li>
                              )
                            )}
                          </ul>
                        </div>
                      ))}
                    </div>
                  </Section>
                </div>

                {vm.learned?.length ? (
                  <Section id="learned" kicker="13" title="Research & Learning">
                    <ul className="space-y-2 text-sm">
                      {vm.learned.map((item) => (
                        <li key={item} className="flex items-start gap-2 text-[var(--rw-soft)]">
                          <span className="tone-pos mt-0.5">✓</span>
                          {item}
                        </li>
                      ))}
                    </ul>
                  </Section>
                ) : null}

                <Section id="conclusion" kicker="14" title="Institutional Conclusion">
                  <p className="rw-body">{vm.conclusion}</p>
                  {(vm.suitableFor?.length || vm.unsuitableFor?.length || vm.decisionAction) && (
                    <div className="rw-decision-final mt-4">
                      {vm.decisionAction ? (
                        <>
                          <p className="rw-mini">Positioning</p>
                          <p className="rw-view-value text-[20px] mt-1">{vm.decisionAction}</p>
                        </>
                      ) : null}
                      <div className="rw-grid-2 mt-3">
                        {vm.suitableFor?.length ? (
                          <div>
                            <p className="rw-mini tone-pos">Suitable for</p>
                            <ul className="mt-1 space-y-1 text-sm text-[var(--rw-soft)]">
                              {vm.suitableFor.map((item) => (
                                <li key={item}>✔ {item}</li>
                              ))}
                            </ul>
                          </div>
                        ) : null}
                        {vm.unsuitableFor?.length ? (
                          <div>
                            <p className="rw-mini tone-neg">Not suitable for</p>
                            <ul className="mt-1 space-y-1 text-sm text-[var(--rw-soft)]">
                              {vm.unsuitableFor.map((item) => (
                                <li key={item}>✖ {item}</li>
                              ))}
                            </ul>
                          </div>
                        ) : null}
                      </div>
                    </div>
                  )}
                  <p className="rw-mini mt-3">
                    Institutional research context — not a brokerage order ticket.
                  </p>
                </Section>

                <Section id="recommendation-status" kicker="15" title="Recommendation Status">
                  <p
                    className={`rw-view-value text-[22px] tone-${
                      vm.recommendationStatus.blocked ? 'warn' : 'pos'
                    }`}
                  >
                    {vm.recommendationStatus.status}
                  </p>
                  <p className="rw-body mt-3">{vm.recommendationStatus.summary}</p>
                  {vm.recommendationStatus.detail ? (
                    <p className="rw-body mt-2">{vm.recommendationStatus.detail}</p>
                  ) : null}
                  {vm.recommendationStatus.coverage != null ? (
                    <p className="rw-mini mt-3">Evidence coverage {vm.recommendationStatus.coverage}%</p>
                  ) : null}
                  {vm.recommendationStatus.gaps?.length ? (
                    <div className="mt-4">
                      <p className="rw-mini mb-2">Current Knowledge Gaps</p>
                      <ul className="space-y-2 text-sm text-[var(--rw-soft)]">
                        {vm.recommendationStatus.gaps.map((g) => (
                          <li key={g} className="border-b border-[var(--rw-border)] pb-2">
                            {g}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                </Section>

                <Section id="explore" kicker="16" title="Explore Further">
                  <div className="rw-explore">
                    {vm.explore.map((q) => (
                      <button key={q} type="button" onClick={() => submit(q)}>
                        {q}
                      </button>
                    ))}
                  </div>
                </Section>

                <div className="rw-footer">
                  <div className="flex flex-wrap gap-3">
                    <Link to="/admin/mission-control">Mission Control</Link>
                    <Link to="/admin/knowledge">Knowledge</Link>
                    <Link to="/research">Research</Link>
                    <button
                      type="button"
                      className="bg-transparent border-0 text-inherit cursor-pointer p-0"
                      onClick={() => navigate('/markets')}
                    >
                      Markets
                    </button>
                  </div>
                  <div className="flex items-center gap-2">
                    <AlertTriangle size={12} className="opacity-50" />
                    <span>System Status: All Systems Operational</span>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
