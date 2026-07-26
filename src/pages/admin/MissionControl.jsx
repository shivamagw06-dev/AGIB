import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  AlertTriangle,
  Download,
  RefreshCw,
  Search,
  Shield,
} from 'lucide-react';
import {
  acknowledgeMissionControlAlert,
  getMissionControlDashboard,
  getMissionControlHealth,
  getMissionControlQualityGates,
  getMissionControlReport,
} from '@/lib/intelligenceApi';
import { Button } from '@/components/ui/button';
import '@/office/theme.css';

function statusColour(status) {
  const s = String(status || '').toLowerCase();
  if (s.includes('healthy') || s === 'ok' || s === 'green') return 'text-emerald-400';
  if (s.includes('warn') || s.includes('yellow') || s.includes('unknown') || s.includes('soft'))
    return 'text-amber-300';
  if (s.includes('critical') || s.includes('offline') || s.includes('red') || s.includes('fail'))
    return 'text-rose-400';
  return 'text-[var(--io-muted)]';
}

function Glass({ children, className = '' }) {
  return (
    <div
      className={`rounded-2xl border border-[var(--io-border)] bg-[rgba(255,255,255,0.03)] backdrop-blur-sm p-4 md:p-5 ${className}`}
    >
      {children}
    </div>
  );
}

function Kicker({ children }) {
  return <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-[var(--io-gold)]">{children}</p>;
}

function Stat({ label, value, hint, status }) {
  return (
    <Glass>
      <p className="text-[11px] uppercase tracking-wide text-[var(--io-caption)]">{label}</p>
      <p className={`mt-2 text-2xl font-semibold tabular-nums ${statusColour(status || value)}`}>
        {value ?? '—'}
      </p>
      {hint ? <p className="mt-1 text-[11px] text-[var(--io-muted)]">{hint}</p> : null}
    </Glass>
  );
}

export default function MissionControl() {
  const [health, setHealth] = useState(null);
  const [desk, setDesk] = useState(null);
  const [gates, setGates] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [query, setQuery] = useState('');
  const [selectedPlatform, setSelectedPlatform] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);

  const load = useCallback(async () => {
    setError('');
    try {
      const [h, d, g] = await Promise.all([
        getMissionControlHealth(),
        getMissionControlDashboard(),
        getMissionControlQualityGates(),
      ]);
      setHealth(h);
      setDesk(d);
      setGates(g);
    } catch (err) {
      setError(err?.message || 'Failed to load Mission Control');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const t = window.setInterval(load, 30_000);
    return () => window.clearInterval(t);
  }, [load]);

  const exportReport = async () => {
    try {
      const report = await getMissionControlReport();
      const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `agi-mission-control-report-${Date.now()}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err?.message || 'Export failed');
    }
  };

  const onAck = async (id) => {
    try {
      await acknowledgeMissionControlAlert(id);
      await load();
    } catch (err) {
      setError(err?.message || 'Acknowledge failed');
    }
  };

  const exec = desk?.executive_status || {};
  const platforms = desk?.platform_status || [];
  const engines = desk?.engine_status || [];
  const apis = desk?.api_status || [];
  const knowledge = desk?.knowledge_growth || {};
  const coverage = desk?.coverage_dashboard || {};
  const monitor = desk?.company_monitor || {};
  const pipeline = desk?.research_pipeline || {};
  const preds = desk?.prediction_intelligence || {};
  const dq = desk?.data_quality || {};
  const ca = desk?.company_analysis || {};
  const academy = desk?.academy || {};
  const cid = desk?.cid || {};
  const sys = desk?.system_health || {};
  const events = desk?.live_event_stream || [];
  const copilot = desk?.executive_copilot || {};
  const arch = desk?.architecture_map || {};
  const alerts = desk?.alerts_centre || [];
  const deploy = desk?.deployment_centre || {};
  const perf = desk?.performance_analytics || {};

  const filteredPlatforms = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return platforms;
    return platforms.filter((p) => JSON.stringify(p).toLowerCase().includes(q));
  }, [platforms, query]);

  return (
    <div className="agi-office -m-6 min-h-screen p-4 md:p-6">
      <div className="mx-auto max-w-[1400px] space-y-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <Kicker>Administrator only · Mission Control v1.0</Kicker>
            <h1 className="io-title mt-2 text-3xl flex items-center gap-2">
              <Shield className="h-7 w-7 text-[var(--io-gold)]" />
              AGI Mission Control
            </h1>
            <p className="mt-2 max-w-3xl text-sm text-[var(--io-muted)]">
              Read-only operations cockpit. Aggregates IOC, CMS, Academy, Company Analysis, Investment
              Office and providers. Never modifies research, House Views, or recommendations.
            </p>
            <p className="mt-2 text-[11px] text-[var(--io-caption)]">
              Timestamp {desk?.generated_at || '—'} · Auto-refresh 30s · Gates{' '}
              {gates?.passed ? 'PASS' : gates ? 'FAIL' : '—'} · {health?.version || ''}
            </p>
          </div>
          <div className="flex flex-wrap gap-2 items-center">
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--io-muted)]" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search platforms / APIs"
                className="w-56 rounded-xl border border-[var(--io-border)] bg-[rgba(255,255,255,0.03)] py-2 pl-9 pr-3 text-sm text-[var(--io-ink)] outline-none focus:border-[var(--io-gold)]"
              />
            </div>
            <Button variant="outline" onClick={load} disabled={loading} className="border-[var(--io-border)] text-[var(--io-ink)]">
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button variant="outline" onClick={exportReport} className="border-[var(--io-border)] text-[var(--io-ink)]">
              <Download className="h-4 w-4 mr-2" />
              Export report
            </Button>
          </div>
        </div>

        {error ? (
          <Glass className="border-amber-500/40 bg-amber-500/10 text-amber-100 flex gap-2 text-sm">
            <AlertTriangle className="h-4 w-4 mt-0.5" />
            <span>{error}</span>
          </Glass>
        ) : null}

        {/* SECTION 1 */}
        <section className="space-y-3">
          <Kicker>Section 1 · Executive Status</Kicker>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-6">
            <Stat label="AGI Status" value={exec.agi_status} status={exec.agi_status} />
            <Stat label="Research Grade" value={exec.research_grade} />
            <Stat label="Knowledge Grade" value={exec.knowledge_grade} />
            <Stat label="Data Grade" value={exec.data_grade} />
            <Stat label="Coverage" value={exec.coverage != null ? `${exec.coverage}%` : '—'} />
            <Stat label="Companies Monitored" value={exec.companies_monitored} />
            <Stat label="Companies Covered" value={exec.companies_covered} />
            <Stat label="Questions Today" value={exec.questions_answered_today ?? '—'} />
            <Stat label="Last Learning" value={exec.last_successful_learning || '—'} hint="Academy / ingest" />
            <Stat label="Last Health Check" value={(exec.last_health_check || '').slice(11, 19) || '—'} />
            <Stat label="Last Deployment" value={deploy.last_deployment || deploy.git_commit || '—'} />
            <Stat label="Branch" value={deploy.current_branch || '—'} />
          </div>
        </section>

        {/* SECTION 2 */}
        <section className="space-y-3">
          <Kicker>Section 2 · Platform Status</Kicker>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {filteredPlatforms.map((p) => (
              <button
                key={p.name}
                type="button"
                onClick={() => setSelectedPlatform(p)}
                className="text-left"
              >
                <Glass className="hover:border-[var(--io-gold)] transition">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-semibold text-[var(--io-ink)]">{p.name}</p>
                    <span className={`text-[11px] font-bold ${statusColour(p.current_status)}`}>
                      {p.current_status}
                    </span>
                  </div>
                  <p className="mt-2 text-[11px] text-[var(--io-muted)]">
                    Errors {p.error_count ?? 0} · Warnings {p.warnings ?? 0}
                    {p.knowledge_count != null ? ` · Knowledge ${p.knowledge_count}` : ''}
                  </p>
                  <p className="mt-1 text-[10px] text-[var(--io-caption)]">
                    {(p.dependencies || []).slice(0, 4).join(' · ') || '—'}
                  </p>
                </Glass>
              </button>
            ))}
          </div>
          {selectedPlatform ? (
            <Glass>
              <div className="flex justify-between gap-3">
                <h3 className="io-title text-xl">{selectedPlatform.name} diagnostics</h3>
                <button type="button" className="text-xs text-[var(--io-gold)]" onClick={() => setSelectedPlatform(null)}>
                  Close
                </button>
              </div>
              <pre className="mt-3 max-h-64 overflow-auto text-[11px] text-[var(--io-ink-soft)]">
                {JSON.stringify(selectedPlatform, null, 2)}
              </pre>
            </Glass>
          ) : null}
        </section>

        {/* SECTION 3 + 4 */}
        <section className="grid gap-4 lg:grid-cols-2">
          <div className="space-y-3">
            <Kicker>Section 3 · Engine Status</Kicker>
            <Glass>
              <ul className="space-y-2 max-h-80 overflow-auto">
                {engines.map((e) => (
                  <li key={e.name} className="flex items-center justify-between border-b border-[var(--io-border)] pb-2 text-sm">
                    <span className="font-medium text-[var(--io-ink)]">{e.name}</span>
                    <span className={statusColour(e.status)}>{e.status}</span>
                  </li>
                ))}
              </ul>
            </Glass>
          </div>
          <div className="space-y-3">
            <Kicker>Section 4 · API Status</Kicker>
            <Glass>
              <ul className="space-y-2 max-h-80 overflow-auto">
                {apis
                  .filter((p) => !query || JSON.stringify(p).toLowerCase().includes(query.toLowerCase()))
                  .slice(0, 24)
                  .map((p) => (
                    <li key={p.name} className="border-b border-[var(--io-border)] pb-2 text-sm">
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-medium text-[var(--io-ink)]">{p.name}</span>
                        <span className={statusColour(p.status)}>
                          {p.colour || p.status}
                        </span>
                      </div>
                      <p className="mt-1 text-[11px] text-[var(--io-muted)]">
                        {p.last_error ? `Last error: ${p.last_error}` : p.provider_confidence || '—'}
                        {p.circuit_state ? ` · circuit ${p.circuit_state}` : ''}
                      </p>
                    </li>
                  ))}
              </ul>
            </Glass>
          </div>
        </section>

        {/* SECTION 5 + 6 */}
        <section className="grid gap-4 lg:grid-cols-2">
          <div className="space-y-3">
            <Kicker>Section 5 · Knowledge Growth</Kicker>
            <div className="grid grid-cols-2 gap-3">
              <Stat label="Books Learned" value={knowledge.books_learned} />
              <Stat label="Concepts" value={knowledge.concepts_added} />
              <Stat label="Frameworks" value={knowledge.frameworks_added} />
              <Stat label="Formulas" value={knowledge.formulas_added} />
              <Stat label="Companies Updated" value={knowledge.companies_updated} />
              <Stat label="HV Reviews" value={knowledge.house_view_reviews} />
            </div>
          </div>
          <div className="space-y-3">
            <Kicker>Section 6 · Coverage</Kicker>
            <div className="grid grid-cols-2 gap-3">
              <Stat label="Overall" value={coverage.overall_coverage != null ? `${coverage.overall_coverage}%` : '—'} />
              <Stat label="Financial" value={coverage.financial_coverage != null ? `${coverage.financial_coverage}%` : '—'} />
              <Stat label="Academy" value={coverage.academy_coverage != null ? `${coverage.academy_coverage}%` : '—'} />
              <Stat label="Research" value={coverage.research_coverage ?? '—'} />
            </div>
            <Glass>
              <p className="text-[11px] uppercase text-[var(--io-caption)]">Below threshold (first)</p>
              <ul className="mt-2 space-y-1 text-sm max-h-40 overflow-auto">
                {(coverage.below_threshold || []).slice(0, 8).map((b, idx) => (
                  <li key={b.ticker || idx} className="text-[var(--io-ink-soft)]">
                    <span className="font-semibold text-[var(--io-ink)]">{b.ticker || '—'}</span> — {b.reason || 'coverage'}
                  </li>
                ))}
                {!(coverage.below_threshold || []).length ? (
                  <li className="text-[var(--io-muted)]">No below-threshold rows surfaced.</li>
                ) : null}
              </ul>
            </Glass>
          </div>
        </section>

        {/* SECTION 7 + 8 + 9 */}
        <section className="grid gap-4 lg:grid-cols-3">
          <div className="space-y-3">
            <Kicker>Section 7 · Company Monitor</Kicker>
            <div className="grid grid-cols-2 gap-3">
              <Stat label="Monitored" value={monitor.companies_monitored} />
              <Stat label="Critical" value={monitor.critical_alerts} status="Critical" />
              <Stat label="High" value={monitor.high_alerts} status="Warning" />
              <Stat label="Need Review" value={monitor.companies_needing_review} />
            </div>
            <Glass>
              <p className="text-[11px] uppercase text-[var(--io-caption)]">Latest changes</p>
              <ul className="mt-2 space-y-1 text-xs max-h-40 overflow-auto text-[var(--io-ink-soft)]">
                {(monitor.latest_company_changes || []).slice(0, 8).map((c, idx) => (
                  <li key={`${c.ticker}-${idx}`}>
                    {c.ticker}: {c.detail || c.change_type} ({c.significance})
                  </li>
                ))}
              </ul>
            </Glass>
          </div>
          <div className="space-y-3">
            <Kicker>Section 8 · Research Pipeline</Kicker>
            <Stat label="Queue" value={(pipeline.research_queue || []).length} />
            <Glass>
              <ul className="space-y-1 text-sm max-h-56 overflow-auto">
                {(pipeline.research_queue || []).slice(0, 8).map((t) => (
                  <li key={t.id || t.title}>
                    <span className="font-medium text-[var(--io-ink)]">{t.title}</span>
                    <p className="text-[11px] text-[var(--io-muted)]">
                      {t.priority} · {t.suggested_owner}
                    </p>
                  </li>
                ))}
              </ul>
            </Glass>
          </div>
          <div className="space-y-3">
            <Kicker>Section 9 · Predictions</Kicker>
            <Stat label="Due" value={(preds.predictions_due || []).length} />
            <Stat label="HV Reviews" value={(preds.house_view_reviews || []).length} />
            <Stat label="Accuracy" value={preds.prediction_accuracy ?? '—'} />
          </div>
        </section>

        {/* SECTION 10–13 */}
        <section className="grid gap-4 lg:grid-cols-2 xl:grid-cols-4">
          <Glass>
            <Kicker>Section 10 · Data Quality</Kicker>
            <ul className="mt-3 space-y-1 text-sm text-[var(--io-ink-soft)]">
              <li>Research: {dq.research_grade}</li>
              <li>Knowledge: {dq.knowledge_grade}</li>
              <li>Market data: {dq.market_data_grade}</li>
              <li>Academy: {dq.academy_grade}</li>
              <li>Sector: {String(dq.sector_intelligence_grade)}</li>
            </ul>
          </Glass>
          <Glass>
            <Kicker>Section 11 · Company Analysis</Kicker>
            <ul className="mt-3 space-y-1 text-sm text-[var(--io-ink-soft)]">
              <li>Analysed: {ca.companies_analysed ?? '—'}</li>
              <li>BQ complete: {ca.business_quality_complete ?? '—'}</li>
              <li>Reports: {(ca.latest_reports || []).length}</li>
            </ul>
          </Glass>
          <Glass>
            <Kicker>Section 12 · Academy</Kicker>
            <ul className="mt-3 space-y-1 text-sm text-[var(--io-ink-soft)]">
              <li>Books: {academy.books}</li>
              <li>Concepts: {academy.concepts}</li>
              <li>Frameworks: {academy.frameworks}</li>
              <li>Formulas: {academy.formulas}</li>
              <li>Graph edges: {academy.graph_relationships}</li>
            </ul>
          </Glass>
          <Glass>
            <Kicker>Section 13 · CID</Kicker>
            <ul className="mt-3 space-y-1 text-sm text-[var(--io-ink-soft)]">
              <li>Enabled: {String(cid.enabled)}</li>
              <li>Coverage: {cid.coverage}</li>
              <li>Dossiers: {cid.company_dossiers}</li>
            </ul>
          </Glass>
        </section>

        {/* SECTION 14 + 15 */}
        <section className="grid gap-4 lg:grid-cols-2">
          <div className="space-y-3">
            <Kicker>Section 14 · System Health (IOC)</Kicker>
            <Glass>
              <ul className="grid grid-cols-2 gap-2 text-sm">
                {[
                  ['FastAPI', sys.fastapi],
                  ['Frontend', sys.frontend],
                  ['Backend', sys.backend],
                  ['Database', sys.database],
                  ['Auth', sys.authentication],
                  ['Email', sys.email],
                  ['Scheduler', sys.scheduler],
                  ['Cache', sys.cache],
                ].map(([label, value]) => (
                  <li key={label} className="flex justify-between border-b border-[var(--io-border)] pb-1">
                    <span className="text-[var(--io-muted)]">{label}</span>
                    <span className={statusColour(value)}>{value || '—'}</span>
                  </li>
                ))}
              </ul>
              <p className="mt-3 text-[11px] text-[var(--io-caption)]">{sys.note}</p>
            </Glass>
          </div>
          <div className="space-y-3">
            <Kicker>Section 15 · Live Event Stream</Kicker>
            <Glass>
              <ul className="space-y-2 max-h-72 overflow-auto text-sm">
                {events.map((e, idx) => (
                  <li key={`${e.at}-${idx}`} className="border-b border-[var(--io-border)] pb-2">
                    <p className="text-[10px] font-bold uppercase text-[var(--io-gold)]">
                      {(e.at || '').slice(11, 19) || '—'} · {e.type}
                    </p>
                    <p className="text-[var(--io-ink-soft)]">{e.message}</p>
                  </li>
                ))}
                {!events.length ? <li className="text-[var(--io-muted)]">No events yet — run CMS / learning cycles.</li> : null}
              </ul>
            </Glass>
          </div>
        </section>

        {/* SECTION 16 + 17 */}
        <section className="grid gap-4 lg:grid-cols-2">
          <div className="space-y-3">
            <Kicker>Section 16 · Executive Copilot</Kicker>
            <Glass>
              <ul className="space-y-3">
                {(copilot.prompts || []).map((p) => (
                  <li key={p}>
                    <p className="text-xs font-semibold text-[var(--io-ink)]">{p}</p>
                    <p className="mt-1 text-[11px] text-[var(--io-muted)]">{copilot.answers?.[p]}</p>
                  </li>
                ))}
              </ul>
            </Glass>
          </div>
          <div className="space-y-3">
            <Kicker>Section 17 · Architecture Map</Kicker>
            <Glass>
              <div className="flex flex-wrap gap-2">
                {(arch.nodes || []).map((n) => (
                  <button
                    key={n.id}
                    type="button"
                    onClick={() => setSelectedNode(n)}
                    className={`rounded-full border px-3 py-1 text-[11px] font-semibold ${
                      n.colour === 'Green'
                        ? 'border-emerald-500/40 text-emerald-300'
                        : n.colour === 'Red'
                          ? 'border-rose-500/40 text-rose-300'
                          : 'border-amber-500/40 text-amber-200'
                    }`}
                  >
                    {n.label}
                  </button>
                ))}
              </div>
              {selectedNode ? (
                <pre className="mt-3 max-h-40 overflow-auto text-[11px] text-[var(--io-ink-soft)]">
                  {JSON.stringify(selectedNode, null, 2)}
                </pre>
              ) : (
                <p className="mt-3 text-[11px] text-[var(--io-caption)]">Click a node for diagnostics.</p>
              )}
            </Glass>
          </div>
        </section>

        {/* SECTION 18–20 */}
        <section className="grid gap-4 lg:grid-cols-3">
          <div className="space-y-3">
            <Kicker>Section 18 · Alerts Centre</Kicker>
            <Glass>
              <ul className="space-y-2 max-h-72 overflow-auto text-sm">
                {alerts.slice(0, 20).map((a) => (
                  <li key={a.id} className="border-b border-[var(--io-border)] pb-2">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="text-[10px] font-bold uppercase text-[var(--io-gold)]">{a.category}</p>
                        <p className="text-[var(--io-ink-soft)]">
                          {a.ticker ? `${a.ticker}: ` : ''}
                          {a.message}
                        </p>
                      </div>
                      {!a.acknowledged ? (
                        <button
                          type="button"
                          onClick={() => onAck(a.id)}
                          className="shrink-0 text-[10px] font-bold uppercase text-[var(--io-gold)]"
                        >
                          Ack
                        </button>
                      ) : (
                        <span className="text-[10px] text-[var(--io-caption)]">ACK</span>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </Glass>
          </div>
          <div className="space-y-3">
            <Kicker>Section 19 · Deployment</Kicker>
            <Glass className="text-sm text-[var(--io-ink-soft)] space-y-1">
              <p>Version: {deploy.current_version}</p>
              <p>Commit: {deploy.git_commit || '—'}</p>
              <p>Branch: {deploy.current_branch || '—'}</p>
              <p>Environment: {deploy.environment}</p>
              <p className="text-[11px] text-[var(--io-caption)]">{deploy.note}</p>
            </Glass>
          </div>
          <div className="space-y-3">
            <Kicker>Section 20 · Performance</Kicker>
            <Glass className="text-sm text-[var(--io-ink-soft)] space-y-1">
              <p>Daily learning: {perf.daily_learning ?? '—'}</p>
              <p>Daily research: {perf.daily_research ?? '—'}</p>
              <p>Ask AGI avg: {perf.average_ask_agi_response ?? '—'}</p>
              <p className="text-[11px] text-[var(--io-caption)]">{perf.note}</p>
            </Glass>
          </div>
        </section>
      </div>
    </div>
  );
}
