import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Pause, Play, RefreshCw } from 'lucide-react';
import {
  getHvieUniverseFailures,
  getHvieUniversePipeline,
  getHvieUniverseSector,
  getHvieUniverseStatus,
  postHvieUniverseResume,
  postHvieUniverseRun,
  postHvieUniverseStart,
  postHvieUniverseStop,
} from '@/lib/intelligenceApi';
import './valuationPolicy.css';

function fmt(n, d = 0) {
  if (n == null || Number.isNaN(Number(n))) return '—';
  return Number(n).toLocaleString(undefined, { maximumFractionDigits: d });
}

function Stat({ label, value, hint }) {
  return (
    <div className="vp-stat">
      <span className="label">{label}</span>
      <span className="value">{value ?? '—'}</span>
      {hint ? <span className="vp-muted" style={{ fontSize: '0.75rem' }}>{hint}</span> : null}
    </div>
  );
}

export default function HvieRuntime() {
  const [status, setStatus] = useState(null);
  const [pipeline, setPipeline] = useState(null);
  const [sectors, setSectors] = useState(null);
  const [failures, setFailures] = useState(null);
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState(null);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    try {
      const [st, pipe, sec, fail] = await Promise.all([
        getHvieUniverseStatus(),
        getHvieUniversePipeline(),
        getHvieUniverseSector(),
        getHvieUniverseFailures({ limit: 40 }),
      ]);
      setStatus(st);
      setPipeline(pipe);
      setSectors(sec);
      setFailures(fail);
      setError(null);
    } catch (err) {
      setError(err.message || 'hvie_universe_status_failed');
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 10000);
    return () => clearInterval(id);
  }, [refresh]);

  const act = async (label, fn) => {
    setBusy(true);
    setNote(null);
    try {
      const out = await fn();
      setNote(`${label}: ${out?.ok === false ? out.error || 'failed' : 'ok'}`);
      await refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const pipe = status?.pipeline || {};
  const thr = status?.throughput || pipeline?.throughput || {};
  const stages = pipeline?.stages || [];
  const queue = status?.queue || {};

  return (
    <div className="vp-page">
      <header className="vp-header">
        <Link to="/admin" className="vp-back"><ArrowLeft size={16} /> Admin</Link>
        <div>
          <div className="vp-eyebrow">Phase 8.3A</div>
          <h1>HVIE Universe Runtime</h1>
          <p className="vp-muted">
            Persisted full-universe bootstrap — reconstructs PE/PB/EV from prices + statements + corporate actions.
            Never downloads vendor historical multiples.
          </p>
        </div>
        <div className="vp-actions">
          <button type="button" disabled={busy} onClick={() => act('start', postHvieUniverseStart)}>
            <Play size={14} /> Start
          </button>
          <button type="button" disabled={busy} onClick={() => act('resume', postHvieUniverseResume)}>
            <RefreshCw size={14} /> Resume
          </button>
          <button type="button" disabled={busy} onClick={() => act('run', () => postHvieUniverseRun({ batch: 12 }))}>
            Run batch
          </button>
          <button type="button" disabled={busy} onClick={() => act('stop', postHvieUniverseStop)}>
            <Pause size={14} /> Stop
          </button>
        </div>
      </header>

      {error ? <p className="hint">Error — {error}</p> : null}
      {note ? <p className="hint">{note}</p> : null}

      <section className="vp-stats">
        <Stat label="Universe" value={fmt(pipe.universe)} />
        <Stat label="Eligible" value={fmt(pipe.eligible)} />
        <Stat label="Complete" value={fmt(pipe.complete)} />
        <Stat label="Pending" value={fmt(pipe.pending)} />
        <Stat label="Retry" value={fmt(pipe.retry)} />
        <Stat label="Failed" value={fmt(pipe.failed)} />
        <Stat label="Skipped" value={fmt(pipe.skipped)} hint="waiting on prices/statements" />
        <Stat
          label="Speed"
          value={thr.speed_per_hour != null ? `${fmt(thr.speed_per_hour, 1)}/h` : '—'}
        />
        <Stat
          label="ETA"
          value={thr.eta_hours != null ? `${fmt(thr.eta_hours, 1)} h` : '—'}
          hint={`remaining ${fmt(thr.remaining)}`}
        />
        <Stat label="Runtime" value={status?.runtime?.status || '—'} />
      </section>

      <section className="vp-card">
        <h2>HVIE Pipeline</h2>
        <p className="vp-muted">Stage completion across the classified universe — not a single percentage.</p>
        <ul className="vp-list">
          {stages.map((s) => (
            <li key={s.name}>
              <span>{s.name}</span>
              <strong>{fmt(s.count)}</strong>
            </li>
          ))}
        </ul>
      </section>

      <section className="vp-card">
        <h2>Bootstrap queue</h2>
        <ul className="vp-list">
          {Object.entries(queue).map(([k, v]) => (
            <li key={k}><span>{k}</span><strong>{fmt(v)}</strong></li>
          ))}
        </ul>
      </section>

      <section className="vp-card">
        <h2>Sector coverage</h2>
        <div className="vp-table-wrap">
          <table className="vp-table">
            <thead>
              <tr>
                <th>Sector</th>
                <th>Companies</th>
                <th>Complete</th>
                <th>Percentiles</th>
                <th>Coverage</th>
              </tr>
            </thead>
            <tbody>
              {(sectors?.rows || []).slice(0, 20).map((r) => (
                <tr key={r.sector}>
                  <td>{r.sector}</td>
                  <td>{fmt(r.companies)}</td>
                  <td>{fmt(r.complete)}</td>
                  <td>{fmt(r.percentiles)}</td>
                  <td>{fmt(r.coverage_pct, 1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="vp-card">
        <h2>Failures / retry / skipped</h2>
        <div className="vp-table-wrap">
          <table className="vp-table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Queue</th>
                <th>Lifecycle</th>
                <th>Reason</th>
                <th>Error</th>
              </tr>
            </thead>
            <tbody>
              {(failures?.rows || []).slice(0, 40).map((r) => (
                <tr key={`${r.symbol}-${r.queue_status}`}>
                  <td>{r.symbol}</td>
                  <td>{r.queue_status}</td>
                  <td>{r.lifecycle}</td>
                  <td>{r.reason || r.blocking_reason || '—'}</td>
                  <td>{r.last_error || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
