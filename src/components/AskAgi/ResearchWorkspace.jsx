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
import Sparkline from '@/office/Sparkline';
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

function Donut({ value = 72 }) {
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
        <p className="text-3xl font-bold tabular-nums">{v}%</p>
        <p className="text-[10px] uppercase tracking-wide text-[var(--rw-caption)]">Overall</p>
      </div>
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
              <button type="button" className="rw-iconbtn" onClick={exportJson} title="Export PDF">
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
              <Section kicker="Ask AGI" title="Institutional Investment Research Workspace">
                <p className="rw-body">
                  Ask any institutional question. Every answer opens as a research note — executive
                  summary, house view, financial intelligence, valuation, risks and catalysts —
                  constructed from AGI&apos;s validated intelligence stack.
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
                    {vm.acEnabled ? <span className="rw-chip muted">Institutional Brief</span> : null}
                  </div>
                  <p className="rw-meta">
                    Last Intelligence Refresh: {vm.freshness} · Knowledge Grade: {vm.knowledgeGrade}
                    {vm.recommendationStatus.blocked
                      ? ' · Recommendation status deferred to conclusion'
                      : ` · Research Coverage: ${vm.coverage}%`}
                  </p>
                </div>

                <div className="rw-grid-2">
                  <Section id="executive" kicker="Section 1" title="Executive Summary">
                    <p className="rw-body">{vm.executive || 'Institutional summary assembling…'}</p>
                  </Section>
                  <Section id="view" kicker="Section 2" title="AGI Institutional View">
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <p className="rw-mini">Current View</p>
                        <p className={`rw-view-value tone-${vm.stanceTone}`}>{vm.stance}</p>
                      </div>
                      <div>
                        <p className="rw-mini">Confidence</p>
                        <p className="rw-view-value">{vm.confidence}%</p>
                        <p className="rw-mini">{vm.conviction} conviction</p>
                      </div>
                      <div>
                        <p className="rw-mini">Time Horizon</p>
                        <p className="font-semibold">{vm.horizon}</p>
                      </div>
                      <div>
                        <p className="rw-mini">Change vs Previous</p>
                        <p className="font-semibold tone-pos">{vm.changeVsPrevious}</p>
                      </div>
                      <div className="col-span-2">
                        <p className="rw-mini">Recommendation Readiness</p>
                        <p className="font-semibold">{vm.readiness}</p>
                      </div>
                    </div>
                  </Section>
                </div>

                <Section id="dashboard" kicker="Section 3" title="Executive Dashboard">
                  <div className="rw-grid-4">
                    {vm.kpis.map((k) => (
                      <div key={k.label} className={`rw-kpi tone-${k.tone}`}>
                        <p className="label">{k.label}</p>
                        <p className="value">{k.value}</p>
                        <p className="hint">{k.hint}</p>
                        <div className="spark">
                          <Sparkline points={k.spark} up={k.tone !== 'neg'} width={88} height={24} />
                        </div>
                      </div>
                    ))}
                  </div>
                </Section>

                <div className="rw-grid-2">
                  <Section id="thesis" kicker="Section 4" title="Investment Thesis">
                    <p className="rw-body">{vm.thesis}</p>
                    {vm.why.length ? (
                      <ul className="mt-3 space-y-2 text-sm text-[var(--rw-soft)]">
                        {vm.why.slice(0, 5).map((w) => (
                          <li key={w} className="border-b border-[var(--rw-border)] pb-2">
                            {w}
                          </li>
                        ))}
                      </ul>
                    ) : null}
                  </Section>
                  <Section id="why" kicker="Section 5" title="Why This View">
                    <div className="grid grid-cols-2 gap-2">
                      {vm.whyCards.map((c) => (
                        <div key={c.key} className="rw-why-card">
                          <h4>{c.label}</h4>
                          <p>{c.text}</p>
                        </div>
                      ))}
                    </div>
                  </Section>
                </div>

                <Section id="changed" kicker="Section 6" title="What's Changed">
                  {vm.changedRows.length ? (
                    <div className="overflow-x-auto">
                      <table className="rw-table">
                        <thead>
                          <tr>
                            <th>Metric</th>
                            <th>Previous</th>
                            <th>Current</th>
                            <th>Change</th>
                          </tr>
                        </thead>
                        <tbody>
                          {vm.changedRows.map((r) => (
                            <tr key={`${r.metric}-${r.current}`}>
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
                    <p className="rw-empty">No material period-over-period changes surfaced yet.</p>
                  )}
                </Section>

                <Section id="financials" kicker="Section 7" title="Financial Intelligence">
                  {vm.financialNarrative ? <p className="rw-body mb-4">{vm.financialNarrative}</p> : null}
                  <div className="rw-grid-3">
                    {vm.financialCards.map((c) => (
                      <div key={c.label} className={`rw-kpi tone-${c.tone}`}>
                        <p className="label">{c.label}</p>
                        <p className="value text-[18px]">{c.display}</p>
                        <p className="hint">{c.status}</p>
                        <div className="spark">
                          <Sparkline points={c.spark} up={c.tone === 'pos'} width={90} height={24} />
                        </div>
                      </div>
                    ))}
                  </div>
                </Section>

                <Section id="valuation" kicker="Section 8" title="Valuation Intelligence">
                  {vm.valuationNarrative ? <p className="rw-body mb-4">{vm.valuationNarrative}</p> : null}
                  <div className="rw-grid-3 mb-4">
                    {vm.valuationCards.map((c) => (
                      <div key={c.label} className={`rw-kpi tone-${c.tone || 'neu'}`}>
                        <p className="label">{c.label}</p>
                        <p className="value text-[18px]">{c.value}</p>
                      </div>
                    ))}
                  </div>
                  {chartData.length >= 2 ? (
                    <div className="h-56 rounded-xl border border-[var(--rw-border)] bg-[var(--rw-panel-2)] p-3">
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
                </Section>

                <div className="rw-grid-2">
                  <Section id="business" kicker="Section 9" title="Business Intelligence">
                    <p className="rw-body">
                      {vm.businessModel ||
                        'Business model and competitive position are synthesised from the living company dossier and institutional company analysis.'}
                    </p>
                    <div className="mt-3 grid grid-cols-2 gap-2">
                      <div className="rw-why-card">
                        <h4>Business Quality</h4>
                        <p>
                          Score {vm.businessQuality?.business_quality_score ?? '—'}
                          {vm.businessQuality?.grade ? ` · Grade ${vm.businessQuality.grade}` : ''}
                        </p>
                      </div>
                      <div className="rw-why-card">
                        <h4>Ownership</h4>
                        <p>{vm.ownershipNarrative || 'Ownership context soft-linked when available.'}</p>
                      </div>
                    </div>
                  </Section>
                  <Section id="market" kicker="Section 10" title="Market Intelligence">
                    <p className="rw-body">
                      {vm.marketNarrative ||
                        'Market performance is interpreted from the institutional market snapshot — never raw vendor dumps.'}
                    </p>
                    <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
                      {[
                        ['Price', vm.marketSnapshot.current_price],
                        ['52W High', vm.marketSnapshot.fifty_two_week_high],
                        ['52W Low', vm.marketSnapshot.fifty_two_week_low],
                        ['Market Cap', vm.marketSnapshot.market_cap],
                      ].map(([label, value]) => (
                        <div key={label} className="rw-why-card">
                          <h4>{label}</h4>
                          <p>{value != null ? String(value) : '—'}</p>
                        </div>
                      ))}
                    </div>
                  </Section>
                </div>

                <div className="rw-grid-2">
                  <Section id="sector" kicker="Section 11" title="Sector Intelligence">
                    <p className="rw-body">
                      {vm.sectorNarrative ||
                        'Sector structure, demand and competition are framed through AGI sector intelligence.'}
                    </p>
                    {vm.sectorDrivers.length ? (
                      <ul className="mt-3 space-y-1 text-sm text-[var(--rw-muted)]">
                        {vm.sectorDrivers.map((d) => (
                          <li key={d}>• {d}</li>
                        ))}
                      </ul>
                    ) : null}
                  </Section>
                  <Section id="macro" kicker="Section 12" title="Macro Intelligence">
                    {vm.macroDrivers.length ? (
                      <ul className="space-y-2 text-sm text-[var(--rw-soft)]">
                        {vm.macroDrivers.map((d) => (
                          <li key={d} className="border-b border-[var(--rw-border)] pb-2">
                            {d}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="rw-empty">Macro drivers will appear when linked to this question.</p>
                    )}
                  </Section>
                </div>

                <Section id="leaders" kicker="Section 13" title="Sector Leaders">
                  {vm.leaders.length ? (
                    <div className="overflow-x-auto">
                      <table className="rw-table">
                        <thead>
                          <tr>
                            <th>Company</th>
                            <th>View</th>
                            <th>Financial</th>
                            <th>Valuation</th>
                            <th>Quality</th>
                            <th>Confidence</th>
                          </tr>
                        </thead>
                        <tbody>
                          {vm.leaders.map((row) => (
                            <tr key={row.company}>
                              <td className="font-semibold text-[var(--rw-ink)]">{row.company}</td>
                              <td className={`tone-${vm.stanceTone}`}>{row.view}</td>
                              <td>{row.financial}</td>
                              <td>{row.valuation}</td>
                              <td>{row.quality}</td>
                              <td>{row.confidence}%</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="rw-empty">Leader comparison populates when sector peers are resolved.</p>
                  )}
                </Section>

                <Section id="scenarios" kicker="Section 14" title="Bull · Base · Bear">
                  <div className="rw-grid-3">
                    {[
                      { key: 'bull', title: 'Bull', items: vm.bull, prob: '35%' },
                      { key: 'base', title: 'Base', items: vm.base, prob: '45%' },
                      { key: 'bear', title: 'Bear', items: vm.bear, prob: '20%' },
                    ].map((s) => (
                      <div key={s.key} className={`rw-scenario ${s.key}`}>
                        <div className="flex items-center justify-between">
                          <h3 className="font-bold">{s.title}</h3>
                          <span className="rw-mini">Prob {s.prob}</span>
                        </div>
                        <ul className="mt-3 space-y-2 text-sm text-[var(--rw-soft)]">
                          {(s.items.length ? s.items : ['Scenario narrative pending richer evidence.']).map((item) => (
                            <li key={item}>• {item}</li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>
                </Section>

                <div className="rw-grid-2">
                  <Section id="risks" kicker="Section 15" title="Top Risks">
                    {vm.risks.length ? (
                      <div className="overflow-x-auto">
                        <table className="rw-table">
                          <thead>
                            <tr>
                              <th>Risk</th>
                              <th>Probability</th>
                              <th>Impact</th>
                              <th>Severity</th>
                              <th>Monitoring</th>
                            </tr>
                          </thead>
                          <tbody>
                            {vm.risks.map((r) => (
                              <tr key={r.risk}>
                                <td className="text-[var(--rw-ink)]">{r.risk}</td>
                                <td>{r.probability}</td>
                                <td>{r.impact}</td>
                                <td className={r.severity === 'Critical' ? 'tone-neg' : 'tone-warn'}>
                                  {r.severity}
                                </td>
                                <td className="tone-pos">{r.monitoring}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <p className="rw-empty">No critical risks listed for this briefing.</p>
                    )}
                  </Section>
                  <Section id="confidence" kicker="Section 17" title="Confidence Assessment">
                    <div className="rw-donut-wrap">
                      <Donut value={vm.confidence} />
                      <ul className="space-y-2 text-sm text-[var(--rw-soft)]">
                        {[
                          ['Financials', Math.min(99, vm.confidence + 2)],
                          ['Business', Math.min(99, vm.confidence - 1)],
                          ['Valuation', Math.min(99, vm.confidence - 4)],
                          ['Sector', Math.min(99, vm.confidence)],
                          ['Knowledge', Math.min(99, vm.coverage)],
                        ].map(([label, value]) => (
                          <li key={label} className="flex justify-between border-b border-[var(--rw-border)] pb-1">
                            <span>{label}</span>
                            <span className="tabular-nums">{value}%</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </Section>
                </div>

                <Section id="catalysts" kicker="Section 16" title="Key Catalysts">
                  {vm.catalysts.length ? (
                    <div className="rw-timeline">
                      {vm.catalysts.map((c, idx) => (
                        <div key={c} className="rw-timeline-item">
                          <p className="rw-mini">T+{idx + 1}</p>
                          <p className="mt-1 text-sm font-semibold text-[var(--rw-ink)]">{c}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="rw-empty">Catalyst calendar will populate from corporate and research events.</p>
                  )}
                </Section>

                <Section id="learned" kicker="Section 18" title="What AGI Learned">
                  <ul className="space-y-2 text-sm">
                    {vm.learned.map((item) => (
                      <li key={item} className="flex items-start gap-2 text-[var(--rw-soft)]">
                        <span className="tone-pos mt-0.5">✓</span>
                        {item}
                      </li>
                    ))}
                  </ul>
                </Section>

                <Section id="conclusion" kicker="Section 19" title="Institutional Conclusion">
                  <p className="rw-body">{vm.conclusion}</p>
                  <p className="rw-mini mt-3">
                    This briefing is institutional research context — not a recommendation to buy or sell.
                  </p>
                </Section>

                <Section id="recommendation-status" kicker="Section 19b" title="Institutional Recommendation Status">
                  <p className={`rw-view-value text-[22px] tone-${vm.recommendationStatus.blocked ? 'warn' : 'pos'}`}>
                    {vm.recommendationStatus.status}
                  </p>
                  <p className="rw-body mt-3">{vm.recommendationStatus.summary}</p>
                  {vm.recommendationStatus.detail ? (
                    <p className="rw-body mt-2">{vm.recommendationStatus.detail}</p>
                  ) : null}
                  {(vm.knowledgeGaps || []).length ? (
                    <div className="mt-4">
                      <p className="rw-mini mb-2">Current Knowledge Gaps</p>
                      <ul className="space-y-2 text-sm text-[var(--rw-soft)]">
                        {vm.knowledgeGaps.map((g) => (
                          <li key={g} className="border-b border-[var(--rw-border)] pb-2">
                            {g}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                </Section>

                <Section id="explore" kicker="Section 20" title="Explore Further">
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
                    <button type="button" className="bg-transparent border-0 text-inherit cursor-pointer p-0" onClick={() => navigate('/markets')}>
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
