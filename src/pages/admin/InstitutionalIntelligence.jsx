import { useCallback, useEffect, useState } from 'react';
import { Activity, AlertTriangle, RefreshCw, Trophy } from 'lucide-react';
import {
  getDecisionQualityDashboard,
  getDecisionQualityHall,
  getHistoricalDepthDashboard,
  getKnowledgeFactoryDailyHealth,
  getMacroIntelligenceDashboard,
  getSectorIntelligenceDashboard,
  runDecisionQuality,
  runHistoricalDepth,
  runMacroIntelligence,
  runSectorIntelligence,
} from '@/lib/intelligenceApi';
import { Button } from '@/components/ui/button';

function Stat({ label, value, hint }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="text-3xl font-bold mt-1 text-slate-900 tabular-nums">{value ?? '—'}</p>
      {hint ? <p className="text-xs text-slate-400 mt-1">{hint}</p> : null}
    </div>
  );
}

function pct(v) {
  if (v == null || Number.isNaN(Number(v))) return '—';
  const n = Number(v);
  return n <= 1 && n >= 0 ? `${Math.round(n * 1000) / 10}%` : `${Math.round(n * 10) / 10}`;
}

export default function InstitutionalIntelligence() {
  const [health, setHealth] = useState(null);
  const [hd, setHd] = useState(null);
  const [isi, setIsi] = useState(null);
  const [imi, setImi] = useState(null);
  const [idq, setIdq] = useState(null);
  const [hall, setHall] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [h, d, s, m, q, hallRes] = await Promise.all([
        getKnowledgeFactoryDailyHealth(),
        getHistoricalDepthDashboard(),
        getSectorIntelligenceDashboard(),
        getMacroIntelligenceDashboard(),
        getDecisionQualityDashboard(),
        getDecisionQualityHall(),
      ]);
      setHealth(h);
      setHd(d);
      setIsi(s);
      setImi(m);
      setIdq(q);
      setHall(hallRes);
    } catch (err) {
      setError(err?.message || 'Failed to load Institutional Intelligence');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const runAll = async () => {
    setBusy('run');
    setError('');
    try {
      await Promise.allSettled([
        runHistoricalDepth(),
        runSectorIntelligence(),
        runMacroIntelligence(),
        runDecisionQuality(),
      ]);
      await load();
    } catch (err) {
      setError(err?.message || 'Pipeline run failed');
    } finally {
      setBusy('');
    }
  };

  const dc = health?.decision_coverage || {};
  const idqKpi = idq?.kpi || {};
  const imiKpi = imi?.kpi || imi || {};
  const fame = hall?.hall_of_fame || [];
  const shame = hall?.hall_of_shame || [];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-[10px] uppercase tracking-[0.2em] text-slate-700 font-semibold">
            Track 1 · Universe Tiers · Infosys-class institutional depth
          </p>
          <h1 className="text-2xl font-bold text-slate-900 mt-1 flex items-center gap-2">
            <Activity className="h-6 w-6 text-slate-800" />
            Institutional Intelligence
          </h1>
          <p className="text-sm text-slate-500 mt-1 max-w-2xl">
            Institutional Decision Coverage across Nifty 500 with Historical Depth, Sector/Macro
            links, Evidence Packs, and Decision Quality. Phases 1–7 remain frozen.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={load} disabled={loading || !!busy}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button onClick={runAll} disabled={!!busy || loading}>
            {busy ? 'Running…' : 'Prime / Run pipelines'}
          </Button>
        </div>
      </div>

      {error ? (
        <div className="flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Stat label="Nifty 100 (Tier 1)" value={pct(dc.nifty_100)} hint="Institutional depth complete" />
        <Stat
          label="Nifty 500 Decision Coverage"
          value={pct(dc.nifty_500)}
          hint={dc.nifty_500_note || 'Tier 2'}
        />
        <Stat
          label="Institutional Decision Coverage"
          value={pct(dc.institutional_decision_coverage ?? health?.north_star?.value_pct)}
          hint={dc.institutional_decision_coverage_note || 'Infosys-class depth / 500'}
        />
        <Stat label="Evidence Quality" value={pct(health?.evidence_quality)} hint="Avg pack quality" />
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Stat
          label="Historical Depth ≥20y"
          value={pct(hd?.companies_gt_20y_pct)}
          hint={`Avg years ${hd?.average_history_years ?? '—'}`}
        />
        <Stat
          label="Sector Intelligence"
          value={pct(isi?.sector_coverage_pct)}
          hint={`Playbooks ${pct(isi?.playbook_coverage_pct)}`}
        />
        <Stat
          label="Macro Intelligence"
          value={imiKpi?.coverage != null ? Number(imiKpi.coverage).toFixed(2) : '—'}
          hint={imi?.status || 'IMI coverage 0–1'}
        />
        <Stat
          label="Decision Quality"
          value={idqKpi?.coverage != null ? Number(idqKpi.coverage).toFixed(1) : '—'}
          hint={idq?.status || 'IDQ north star'}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <h2 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
            <Trophy className="h-4 w-4 text-amber-600" />
            Hall of Fame
          </h2>
          <ul className="mt-3 space-y-2 text-sm text-slate-700">
            {fame.length === 0 ? <li className="text-slate-400">No classified wins yet — run IDQ.</li> : null}
            {fame.slice(0, 6).map((e) => (
              <li key={e.decision_id} className="border-b border-slate-100 pb-2">
                <span className="font-medium">{e.entity}</span>
                <span className="text-slate-400"> · {e.category}</span>
                <p className="text-xs text-slate-500">{e.why}</p>
              </li>
            ))}
          </ul>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <h2 className="text-sm font-semibold text-slate-800">Hall of Shame</h2>
          <ul className="mt-3 space-y-2 text-sm text-slate-700">
            {shame.length === 0 ? <li className="text-slate-400">No classified misses yet — run IDQ.</li> : null}
            {shame.slice(0, 6).map((e) => (
              <li key={e.decision_id} className="border-b border-slate-100 pb-2">
                <span className="font-medium">{e.entity}</span>
                <span className="text-slate-400"> · {e.category}</span>
                <p className="text-xs text-slate-500">{e.why}</p>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-5 text-sm text-slate-600">
        <p>
          Roadmap next:{' '}
          <span className="font-semibold text-slate-900">{health?.roadmap_next || '—'}</span>
        </p>
        <p className="mt-1 text-xs text-slate-400">
          Observability + Knowledge Factory enrichment only. Reasoning architecture frozen v1.0.
        </p>
      </div>
    </div>
  );
}
