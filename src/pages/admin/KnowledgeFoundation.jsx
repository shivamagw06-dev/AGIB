import { useCallback, useEffect, useMemo, useState } from 'react';
import { Brain, RefreshCw, Search, Sprout } from 'lucide-react';
import {
  getKfCoverage,
  getKfHealth,
  listKfCompanies,
  listKfMacros,
  listKfPredictions,
  listKfSectors,
  listKfThemes,
  rebuildKf,
  searchKf,
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
  const [companies, setCompanies] = useState([]);
  const [sectors, setSectors] = useState([]);
  const [themes, setThemes] = useState([]);
  const [macros, setMacros] = useState([]);
  const [predictions, setPredictions] = useState([]);
  const [query, setQuery] = useState('Indian FMCG');
  const [hits, setHits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [h, c, cos, secs, ths, macs, preds] = await Promise.all([
        getKfHealth(),
        getKfCoverage(),
        listKfCompanies(),
        listKfSectors(),
        listKfThemes(),
        listKfMacros(),
        listKfPredictions().catch(() => ({ predictions: [] })),
      ]);
      setHealth(h);
      setCoverage(c);
      setCompanies(cos?.companies || []);
      setSectors(secs?.sectors || []);
      setThemes(ths?.themes || []);
      setMacros(macs?.macros || []);
      setPredictions(preds?.predictions || []);
    } catch (err) {
      setError(err?.message || 'Failed to load Knowledge Foundation');
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
      const result = await searchKf(query.trim(), 10);
      setHits(result?.hits || []);
    } catch (err) {
      setError(err?.message || 'Search failed');
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
      await load();
    } catch (err) {
      setError(err?.message || `${action} failed`);
    } finally {
      setBusy('');
    }
  };

  const metrics = useMemo(() => {
    const c = coverage || {};
    return [
      ['Companies', c.companies_covered ?? 0, `seeded ${c.companies_seeded ?? 0}`],
      ['Sectors', c.sector_coverage ?? 0, `seeded ${c.sectors_seeded ?? 0}`],
      ['Themes', c.theme_coverage ?? 0, `seeded ${c.themes_seeded ?? 0}`],
      ['Macro', c.macro_coverage ?? 0, `seeded ${c.macros_seeded ?? 0}`],
      ['Research extracts', c.research_extracts ?? 0, 'Phase 5'],
      ['Predictions', c.prediction_coverage ?? 0, 'Phase 6'],
      ['Avg confidence', pct(c.avg_confidence), 'quality'],
      ['Avg freshness', pct(c.avg_freshness), 'recency'],
      ['Relationships', c.relationship_count ?? 0, 'graph links'],
      ['Dupes reduced', c.duplicate_reductions ?? 0, 'merge savings'],
    ];
  }, [coverage]);

  return (
    <div className="p-6 lg:p-8 max-w-7xl">
      <div className="flex flex-wrap items-start justify-between gap-4 mb-8">
        <div>
          <p className="text-[11px] uppercase tracking-[0.18em] text-orange-600 font-semibold">KF1 · Locked architecture</p>
          <h1 className="text-2xl font-bold text-slate-900 mt-1">Knowledge Foundation</h1>
          <p className="text-slate-500 mt-1 max-w-2xl">
            Institutional knowledge objects for companies, sectors, themes and macro — searched before documents.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            disabled={!!busy || loading}
            onClick={() => runAction('seed')}
            className="border-slate-300"
          >
            <Sprout size={16} className="mr-2" />
            {busy === 'seed' ? 'Seeding…' : 'Seed'}
          </Button>
          <Button
            variant="outline"
            disabled={!!busy || loading}
            onClick={() => runAction('rebuild')}
            className="border-slate-300"
          >
            <RefreshCw size={16} className="mr-2" />
            {busy === 'rebuild' ? 'Rebuilding…' : 'Rebuild from KIP'}
          </Button>
          <Button disabled={!!busy || loading} onClick={load} className="bg-blue-700 hover:bg-blue-800">
            <Brain size={16} className="mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {error ? (
        <div className="mb-6 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
          {error}
        </div>
      ) : null}

      {loading ? (
        <p className="text-slate-400">Loading knowledge coverage…</p>
      ) : (
        <>
          <div className="mb-6 rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-600">
            <p className="font-semibold text-slate-900">
              Status: {health?.status || 'unknown'} · {health?.version || 'kf-v1'}
            </p>
            <p className="mt-1">
              Architecture {health?.architecture_status || 'v1.0.1 LOCKED'}. Priority: knowledge objects before PDFs.
              Last updated: {coverage?.last_updated || '—'}
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
            {metrics.map(([label, value, hint]) => (
              <MetricCard key={label} label={label} value={value} hint={hint} />
            ))}
          </div>

          <form onSubmit={runSearch} className="mb-8 bg-white rounded-xl border border-slate-200 p-5">
            <label className="text-sm font-semibold text-slate-900">Knowledge-first search</label>
            <div className="mt-3 flex flex-wrap gap-2">
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g. Indian FMCG, IT Services, Inflation"
                className="flex-1 min-w-[220px] rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
              <Button type="submit" disabled={busy === 'search'} className="bg-blue-700 hover:bg-blue-800">
                <Search size={16} className="mr-2" />
                {busy === 'search' ? 'Searching…' : 'Search objects'}
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
                        score {hit.score} · conf {pct(hit.confidence)} · fresh {pct(hit.freshness)}
                      </p>
                    </div>
                    {hit.summary ? <p className="text-slate-500 mt-1 line-clamp-2">{hit.summary}</p> : null}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-slate-400 mt-3">Run a search to verify knowledge objects resolve before documents.</p>
            )}
          </form>

          <div className="grid lg:grid-cols-2 gap-6">
            <CoverageTable
              title="Companies"
              columns={['Ticker', 'Name', 'Sector', 'Conf', 'Fresh']}
              rows={companies.slice(0, 40).map((c) => [
                c.ticker,
                c.name,
                c.sector || '—',
                pct(c.confidence),
                pct(c.freshness),
              ])}
            />
            <CoverageTable
              title="Sectors"
              columns={['Sector', 'Companies', 'View', 'Conf', 'Fresh']}
              rows={sectors.map((s) => [
                s.label,
                s.companies ?? 0,
                s.current_agi_view || 'Seeded',
                pct(s.confidence),
                pct(s.freshness),
              ])}
            />
            <CoverageTable
              title="Themes"
              columns={['Theme', 'Companies', 'Conf', 'Fresh']}
              rows={themes.map((t) => [t.label, t.companies ?? 0, pct(t.confidence), pct(t.freshness)])}
            />
            <CoverageTable
              title="Macro"
              columns={['Topic', 'Conf', 'Fresh']}
              rows={macros.map((m) => [m.label, pct(m.confidence), pct(m.freshness)])}
            />
          </div>

          {predictions.length > 0 ? (
            <div className="mt-6">
              <CoverageTable
                title="Prediction memory"
                columns={['Prediction', 'Company', 'Status', 'Conf']}
                rows={predictions.slice(0, 20).map((p) => [
                  p.prediction || p.prediction_id,
                  p.company || '—',
                  p.status || 'open',
                  pct(p.confidence),
                ])}
              />
            </div>
          ) : null}
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
        <p className="p-6 text-sm text-slate-400">No objects yet. Seed the foundation.</p>
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
