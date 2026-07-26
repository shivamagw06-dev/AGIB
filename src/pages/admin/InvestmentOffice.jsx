import { useCallback, useEffect, useState } from 'react';
import { Landmark, AlertTriangle, RefreshCw } from 'lucide-react';
import {
  getInvestmentOfficeDashboard,
  getInvestmentOfficeHealth,
  getInvestmentOfficeQualityGates,
} from '@/lib/intelligenceApi';
import { Button } from '@/components/ui/button';

function Stat({ label, value, hint }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="text-3xl font-bold mt-1 text-slate-900">{value ?? '—'}</p>
      {hint ? <p className="text-xs text-slate-400 mt-1">{hint}</p> : null}
    </div>
  );
}

export default function InvestmentOfficeAdmin() {
  const [health, setHealth] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [gates, setGates] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [h, d, g] = await Promise.all([
        getInvestmentOfficeHealth(),
        getInvestmentOfficeDashboard(),
        getInvestmentOfficeQualityGates(),
      ]);
      setHealth(h);
      setDashboard(d);
      setGates(g);
    } catch (err) {
      setError(err?.message || 'Failed to load Investment Office');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const attention = dashboard?.companies_requiring_attention || [];
  const queue = dashboard?.todays_research_queue || [];
  const knowledge = dashboard?.knowledge_growth || {};
  const coverage = dashboard?.coverage_dashboard || {};
  const preds = dashboard?.prediction_review || {};
  const risk = dashboard?.risk_centre || {};

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-[10px] uppercase tracking-[0.2em] text-amber-700 font-semibold">
            Investment Office v1.0 · Executive cockpit
          </p>
          <h1 className="text-2xl font-bold text-slate-900 mt-1 flex items-center gap-2">
            <Landmark className="h-6 w-6 text-amber-700" />
            Investment Office
          </h1>
          <p className="text-sm text-slate-500 mt-1 max-w-2xl">
            Aggregates CMS, Company Analysis, Academy, IOC and UI home into the daily CIO desk. Not an
            engine. Not a recommendation engine.
          </p>
        </div>
        <Button variant="outline" onClick={load} disabled={loading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh desk
        </Button>
      </div>

      {error ? (
        <div className="flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          <AlertTriangle className="h-4 w-4 mt-0.5" />
          <span>{error}</span>
        </div>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-6">
        <Stat label="Status" value={health?.status || '—'} hint={health?.version} />
        <Stat label="Attention" value={attention.length} hint="Companies ranked" />
        <Stat label="Research queue" value={queue.length} />
        <Stat label="Coverage" value={coverage.coverage_pct != null ? `${coverage.coverage_pct}%` : '—'} />
        <Stat label="HV reviews" value={(preds.house_view_reviews_required || []).length} />
        <Stat label="Gates" value={gates?.passed ? 'PASS' : gates ? 'FAIL' : '—'} />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <h2 className="text-lg font-semibold mb-3">Analyst queue</h2>
          <ul className="space-y-2 text-sm max-h-80 overflow-auto">
            {queue.map((t) => (
              <li key={t.id}>
                <span className="font-medium">{t.title}</span>
                <p className="text-slate-500">
                  {t.priority} · {t.estimated_effort} · {t.suggested_owner}
                </p>
              </li>
            ))}
          </ul>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <h2 className="text-lg font-semibold mb-3">Knowledge growth</h2>
          <ul className="space-y-2 text-sm">
            <li>Books learned: {knowledge.books_learned ?? '—'}</li>
            <li>Concepts: {knowledge.concepts_added ?? '—'}</li>
            <li>Frameworks: {knowledge.frameworks_added ?? '—'}</li>
            <li>Companies monitored: {knowledge.companies_updated ?? '—'}</li>
          </ul>
          <h3 className="text-sm font-semibold mt-4 mb-2">Prediction / reviews</h3>
          <p className="text-sm text-slate-600">
            House View reviews: {(preds.house_view_reviews_required || []).length}
          </p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <h2 className="text-lg font-semibold mb-3">System health (IOC)</h2>
          <p className="text-sm text-slate-600">
            Overall: {(dashboard?.system_health || {}).overall || '—'}
          </p>
          <p className="text-sm text-slate-500 mt-2">IOC integration only — no duplicate ops logic.</p>
          <h3 className="text-sm font-semibold mt-4 mb-2">Risk centre</h3>
          <p className="text-sm text-slate-600">
            Critical: {(risk.critical_alerts || []).length} · High: {(risk.high_alerts || []).length}
          </p>
        </div>
      </div>
    </div>
  );
}
