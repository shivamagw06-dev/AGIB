import { useCallback, useEffect, useMemo, useState } from 'react';
import { AlertTriangle, Brain, RefreshCw, Search, Sprout } from 'lucide-react';
import {
  consultKc,
  getKcDashboard,
  getKfCoverage,
  getKfHealth,
  listKfCompanies,
  listKfMacros,
  listKfSectors,
  listKfThemes,
  populateKc,
  rebuildKf,
  seedKf,
} from '@/lib/intelligenceApi';
import { Button } from '@/components/ui/button';

function pct(value) {
  if (value == null || Number.isNaN(Number(value))) return '—';
  return `${Math.round(Number(value) * 100)}%`;
}

function MetricCard({ label, value, hint }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="text-3xl font-bold mt-1 text-slate-900">{value}</p>
      {hint ? <p className="text-xs text-slate-400 mt-1">{hint}</p> : null}
    </div>
  );
}

export default function KnowledgeFoundation() {
  const [health, setHealth] = useState(null);
  const [coverage, setCoverage] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [companies, setCompanies] = useState([]);
  const [sectors, setSectors] = useState([]);
  const [themes, setThemes] = useState([]);
  const [macros, setMacros] = useState([]);
  const [query, setQuery] = useState('Indian FMCG');
  const [hits, setHits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [h, c, dash, cos, secs, ths, macs] = await Promise.all([
        getKfHealth(),
        getKfCoverage(),
        getKcDashboard().catch(() => null),
        listKfCompanies(),
        listKfSectors(),
        listKfThemes(),
        listKfMacros(),
      ]);
      setHealth(h);
      setCoverage(c);
      setDashboard(dash);
      setCompanies(cos?.companies || []);
      setSectors(secs?.sectors || []);
      setThemes(ths?.themes || []);
      setMacros(macs?.macros || []);
    } catch (err) {
      setError(err?.message || 'Failed to load Knowledge Corpus');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const runSearch = async (e) => {
    e?.preventDefault?.();
    if (!query.trim()) return;
    setBusy('search');
    setError('');
    try {
      const result = await consultKc(query.trim(), 10);
      setHits(result?.hits || []);
    } catch (err) {
      setError(err?.message || 'Corpus consult failed');
    } finally {
      setBusy('');
    }
  };

  const runAction = async (action) => {
    setBusy(action);
    setError('');
    try {
      if (action === 'seed') await seedKf();
      if (action === 'rebuild') await rebuildKf();
      if (action === 'populate') await populateKc(true);
      await load();
    } catch (err) {
      setError(err?.message || `${action} failed`);
    } finally {
      setBusy('');
    }
  };

  const metrics = dashboard?.metrics || {};
  const executive = useMemo(
    () => [
      ['Nifty 50', pct(metrics.nifty_50_coverage), `${metrics.nifty_50_covered || 0}/${metrics.nifty_50_total || 0}`],
      ['Nifty Next 50', pct(metrics.nifty_next_50_coverage), `${metrics.nifty_next_50_covered || 0} covered`],
      ['Nifty 500 path', pct(metrics.nifty_500_path_coverage), `${metrics.nifty_500_path_covered || 0}/${metrics.nifty_500_path_total || 0}`],
      ['Companies', metrics.companies_covered ?? coverage?.companies_covered ?? 0, 'dossiers'],
      ['Sectors', metrics.sector_coverage ?? coverage?.sector_coverage ?? 0, 'living reports'],
      ['Themes', metrics.theme_coverage ?? coverage?.theme_coverage ?? 0, 'theme objects'],
      ['Macro', metrics.macro_coverage ?? coverage?.macro_coverage ?? 0, 'macro library'],
      ['Research notes', metrics.research_notes ?? coverage?.research_extracts ?? 0, 'structured'],
      ['Broker reports', metrics.broker_reports ?? 0, 'structured'],
      ['Predictions', metrics.predictions ?? coverage?.prediction_coverage ?? 0, 'memory'],
      ['Knowledge objects', metrics.knowledge_objects ?? 0, 'total'],
      ['Relationships', metrics.relationships ?? coverage?.relationship_count ?? 0, 'graph'],
      ['Freshness', pct(metrics.avg_freshness ?? coverage?.avg_freshness), 'avg'],
      ['Confidence', pct(metrics.avg_confidence ?? coverage?.avg_confidence), 'avg'],
      ['Quality', pct(metrics.avg_quality), 'overall'],
      ['Gaps open', metrics.gaps_open ?? 0, 'tasks'],
    ],
    [metrics, coverage]
  );

  const gaps = dashboard?.needs_attention || dashboard?.gaps || [];
  const learning = dashboard?.learning || {};
  const heatmap = metrics.coverage_heatmap || [];
  const recently = metrics.recently_updated || [];

  return (
    <div className="p-6 lg:p-8 max-w-7xl">
      <div className="flex flex-wrap items-start justify-between gap-4 mb-8">
        <div>
          <p className="text-[11px] uppercase tracking-[0.18em] text-orange-600 font-semibold">
            KCV1 · Knowledge Corpus · Architecture locked
          </p>
          <h1 className="text-2xl font-bold text-slate-900 mt-1">Institutional Knowledge Corpus</h1>
          <p className="text-slate-500 mt-1 max-w-2xl">
            Populate and compound the Knowledge Foundation. Knowledge objects are the primary source of truth;
            documents enrich them.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" disabled={!!busy || loading} onClick={() => runAction('seed')} className="border-slate-300">
            <Sprout size={16} className="mr-2" />
            {busy === 'seed' ? 'Seeding…' : 'Seed KF'}
          </Button>
          <Button variant="outline" disabled={!!busy || loading} onClick={() => runAction('rebuild')} className="border-slate-300">
            <RefreshCw size={16} className="mr-2" />
            {busy === 'rebuild' ? 'Rebuilding…' : 'Rebuild KF'}
          </Button>
          <Button disabled={!!busy || loading} onClick={() => runAction('populate')} className="bg-blue-700 hover:bg-blue-800">
            <Brain size={16} className="mr-2" />
            {busy === 'populate' ? 'Populating…' : 'Populate Corpus'}
          </Button>
        </div>
      </div>

      {error ? (
        <div className="mb-6 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}</div>
      ) : null}

      {loading ? (
        <p className="text-slate-400">Loading corpus dashboard…</p>
      ) : (
        <>
          <div className="mb-6 rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-600">
            <p className="font-semibold text-slate-900">
              KF {health?.status || 'unknown'} · Corpus {dashboard ? 'online' : 'pending populate'} ·{' '}
              {health?.architecture_status || 'v1.0.1 LOCKED'}
            </p>
            <p className="mt-1">
              Last populated: {metrics.last_populated_at || '—'} · Answer policy: knowledge corpus before documents.
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {executive.map(([label, value, hint]) => (
              <MetricCard key={label} label={label} value={value} hint={hint} />
            ))}
          </div>

          <div className="grid lg:grid-cols-2 gap-6 mb-8">
            <div className="bg-white rounded-xl border border-slate-200 p-5">
              <div className="flex items-center gap-2 mb-3">
                <AlertTriangle size={16} className="text-amber-600" />
                <h2 className="font-semibold text-slate-900">Needs attention</h2>
              </div>
              {gaps.length === 0 ? (
                <p className="text-sm text-slate-400">No critical gaps. Populate corpus after new research.</p>
              ) : (
                <ul className="space-y-3 max-h-80 overflow-y-auto">
                  {gaps.slice(0, 12).map((g) => (
                    <li key={g.task_id} className="text-sm border-b border-slate-100 pb-2">
                      <p className="font-medium text-slate-900">
                        <span className="text-xs uppercase tracking-wide text-amber-700 mr-2">{g.severity}</span>
                        {g.title}
                      </p>
                      <p className="text-slate-500 mt-0.5">{g.suggested_action || g.detail}</p>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="bg-white rounded-xl border border-slate-200 p-5">
              <h2 className="font-semibold text-slate-900 mb-3">What did AGI learn today?</h2>
              <ul className="space-y-2 text-sm text-slate-600 max-h-80 overflow-y-auto">
                {(learning.learned_today || ['No learning digest yet — populate corpus.']).map((item) => (
                  <li key={item} className="border-b border-slate-100 pb-2">
                    {item}
                  </li>
                ))}
              </ul>
              {(learning.companies_changed || []).length > 0 ? (
                <p className="text-xs text-slate-400 mt-3">
                  Companies changed: {(learning.companies_changed || []).slice(0, 8).join(', ')}
                </p>
              ) : null}
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-5 mb-8">
            <h2 className="font-semibold text-slate-900 mb-3">Nifty 50 coverage heatmap</h2>
            {heatmap.length === 0 ? (
              <p className="text-sm text-slate-400">Populate corpus to build sector heatmap.</p>
            ) : (
              <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {heatmap.map((row) => (
                  <div key={row.sector} className="rounded-lg border border-slate-100 px-3 py-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium text-slate-800">{row.sector}</span>
                      <span className="text-slate-500">{pct(row.coverage)}</span>
                    </div>
                    <div className="mt-2 h-2 rounded bg-slate-100 overflow-hidden">
                      <div
                        className="h-full bg-blue-600"
                        style={{ width: `${Math.round(Number(row.coverage || 0) * 100)}%` }}
                      />
                    </div>
                    <p className="text-xs text-slate-400 mt-1">
                      {row.covered}/{row.companies} · quality {pct(row.avg_quality)}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>

          <form onSubmit={runSearch} className="mb-8 bg-white rounded-xl border border-slate-200 p-5">
            <label className="text-sm font-semibold text-slate-900">Corpus-first consult</label>
            <div className="mt-3 flex flex-wrap gap-2">
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g. Indian FMCG, IT Services, Inflation"
                className="flex-1 min-w-[220px] rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
              <Button type="submit" disabled={busy === 'search'} className="bg-blue-700 hover:bg-blue-800">
                <Search size={16} className="mr-2" />
                {busy === 'search' ? 'Consulting…' : 'Consult corpus'}
              </Button>
            </div>
            {hits.length > 0 ? (
              <ul className="mt-4 divide-y divide-slate-100">
                {hits.map((hit) => (
                  <li key={`${hit.kind}-${hit.key}`} className="py-3 text-sm">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <p className="font-medium text-slate-900">
                        <span className="text-xs uppercase tracking-wide text-slate-400 mr-2">{hit.kind}</span>
                        {hit.label}
                      </p>
                      <p className="text-xs text-slate-500">
                        score {hit.score} · quality {pct(hit.quality)} · conf {pct(hit.confidence)}
                      </p>
                    </div>
                    {hit.summary ? <p className="text-slate-500 mt-1 line-clamp-2">{hit.summary}</p> : null}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-slate-400 mt-3">Consult verifies knowledge objects resolve before documents.</p>
            )}
          </form>

          <div className="grid lg:grid-cols-2 gap-6 mb-8">
            <CoverageTable
              title="Recently updated"
              columns={['Kind', 'Key', 'Conf', 'Fresh']}
              rows={recently.slice(0, 15).map((r) => [r.kind, r.key || r.label, pct(r.confidence), pct(r.freshness)])}
            />
            <CoverageTable
              title="Companies"
              columns={['Ticker', 'Name', 'Sector', 'Conf', 'Fresh']}
              rows={companies.slice(0, 40).map((c) => [c.ticker, c.name, c.sector || '—', pct(c.confidence), pct(c.freshness)])}
            />
            <CoverageTable
              title="Sectors"
              columns={['Sector', 'Companies', 'View', 'Conf']}
              rows={sectors.map((s) => [s.label, s.companies ?? 0, s.current_agi_view || 'Seeded', pct(s.confidence)])}
            />
            <CoverageTable
              title="Themes & Macro"
              columns={['Object', 'Type', 'Conf', 'Fresh']}
              rows={[
                ...themes.map((t) => [t.label, 'theme', pct(t.confidence), pct(t.freshness)]),
                ...macros.map((m) => [m.label, 'macro', pct(m.confidence), pct(m.freshness)]),
              ]}
            />
          </div>
        </>
      )}
    </div>
  );
}

function CoverageTable({ title, columns, rows }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
      <div className="px-5 py-4 border-b border-slate-100">
        <h2 className="font-semibold text-slate-900">{title}</h2>
      </div>
      {rows.length === 0 ? (
        <p className="p-6 text-sm text-slate-400">No objects yet. Populate the corpus.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-500 uppercase text-xs tracking-wide">
              <tr>
                {columns.map((col) => (
                  <th key={col} className="text-left px-4 py-3 font-medium">
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, idx) => (
                <tr key={`${title}-${idx}`} className="border-t border-slate-100">
                  {row.map((cell, cidx) => (
                    <td key={cidx} className="px-4 py-2.5 text-slate-700">
                      {cell}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
