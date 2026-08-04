import { useCallback, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, RefreshCw, Search } from 'lucide-react';
import {
  getHvieBands,
  getHvieCompany,
  getHvieCoverage,
  getHvieHealth,
  getHviePercentiles,
  getHvieRegimes,
  getHvieRerating,
} from '@/lib/intelligenceApi';
import './valuationPolicy.css';

function Stat({ label, value, hint }) {
  return (
    <div className="vp-stat">
      <span className="label">{label}</span>
      <span className="value">{value ?? '—'}</span>
      {hint ? <span className="vp-muted" style={{ fontSize: '0.75rem' }}>{hint}</span> : null}
    </div>
  );
}

function fmt(n, d = 2) {
  if (n == null || Number.isNaN(Number(n))) return '—';
  return Number(n).toLocaleString(undefined, { maximumFractionDigits: d });
}

export default function HistoricalValuation() {
  const [symbol, setSymbol] = useState('INFY');
  const [metric, setMetric] = useState('pe');
  const [window, setWindow] = useState('10y');
  const [pack, setPack] = useState(null);
  const [extra, setExtra] = useState({});
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    const sym = String(symbol || '').trim().toUpperCase();
    if (!sym) return;
    setLoading(true);
    try {
      const [h, company, bands, pct, regimes, rerating, coverage] = await Promise.all([
        getHvieHealth(),
        getHvieCompany(sym, { metric, window }),
        getHvieBands(sym, { metric, window }),
        getHviePercentiles(sym, { metric }),
        getHvieRegimes(sym, { metric, window }),
        getHvieRerating(sym, { metric, window }),
        getHvieCoverage(sym, { metric }),
      ]);
      setHealth(h);
      setPack(company);
      setExtra({ bands, pct, regimes, rerating, coverage });
      setError(null);
    } catch (err) {
      setError(err.message || 'hvie_failed');
    } finally {
      setLoading(false);
    }
  }, [symbol, metric, window]);

  return (
    <div className="vp-root">
      <div className="vp-shell">
        <Link to="/admin" className="vp-back">
          <ArrowLeft size={14} /> Admin
        </Link>
        <p className="vp-kicker">Phase 8.3 · Historical Valuation Intelligence Engine</p>
        <h1 className="vp-title">Historical Valuation</h1>
        <p className="vp-sub">
          Reconstructed from historical prices and reported financials — never downloaded
          vendor PE/PB series. Gated by Phase 8.2A valuation policy. UI renders engine
          outputs only.
        </p>

        <div className="vp-filters">
          <input
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && load()}
            placeholder="Symbol"
          />
          <select value={metric} onChange={(e) => setMetric(e.target.value)}>
            <option value="pe">PE</option>
            <option value="pb">PB</option>
            <option value="ev_ebitda">EV/EBITDA</option>
            <option value="ev_sales">EV/Sales</option>
            <option value="dividend_yield">Dividend Yield</option>
          </select>
          <select value={window} onChange={(e) => setWindow(e.target.value)}>
            {['1y', '3y', '5y', '10y', '15y', '20y', 'max'].map((w) => (
              <option key={w} value={w}>{w}</option>
            ))}
          </select>
          <button type="button" onClick={load}>
            <Search size={14} style={{ marginRight: 6 }} />
            {loading ? 'Loading…' : 'Lookup'}
          </button>
          <button type="button" className="ghost" onClick={load}>
            <RefreshCw size={14} style={{ marginRight: 6 }} /> Refresh
          </button>
        </div>

        {error ? <div className="vp-error">{error}</div> : null}

        <div className="vp-stats">
          <Stat label="Engine" value={health?.version || '8.3'} hint="HVIE" />
          <Stat label="Current" value={fmt(pack?.current)} hint={pack?.metric?.toUpperCase()} />
          <Stat label={`${window} Median`} value={fmt(pack?.median)} />
          <Stat label="Percentile" value={pack?.historical_percentile != null ? `${fmt(pack.historical_percentile, 1)}%` : '—'} />
          <Stat label="Regime" value={pack?.regime || extra.regimes?.regime || '—'} />
          <Stat label="Premium" value={pack?.premium_to_median_pct != null ? `${fmt(pack.premium_to_median_pct, 1)}%` : '—'} />
          <Stat label="Confidence" value={pack?.confidence || '—'} />
          <Stat
            label="Coverage"
            value={pack?.coverage?.span_years != null ? `${fmt(pack.coverage.span_years, 1)}y` : '—'}
            hint={pack?.coverage?.observation_count ? `${pack.coverage.observation_count} obs` : undefined}
          />
        </div>

        {pack?.ok ? (
          <div className="vp-table-wrap" style={{ padding: '1rem', marginBottom: '1rem' }}>
            <p className="vp-kicker">{pack.symbol} · {pack.metric?.toUpperCase()} · {window}</p>
            <p className="vp-sub" style={{ margin: '0.5rem 0 0' }}>
              Policy: {pack.policy?.primary_model || '—'} ({pack.policy?.status || '—'}) ·
              Vendor historical ratios: {String(pack.vendor_historical_ratios)}
            </p>
            <p className="vp-muted" style={{ marginTop: '0.75rem' }}>
              {pack.coverage?.coverage_label || '—'}
            </p>
            {extra.bands?.ok ? (
              <p className="vp-muted" style={{ marginTop: '0.5rem' }}>
                Band: min {fmt(extra.bands.min)} → p25 {fmt(extra.bands.p25)} → median {fmt(extra.bands.median)} →
                p75 {fmt(extra.bands.p75)} → max {fmt(extra.bands.max)}
              </p>
            ) : null}
            {extra.rerating?.ok ? (
              <p className="vp-muted" style={{ marginTop: '0.5rem' }}>
                {extra.rerating.sentence}
                {extra.rerating.cheapest ? ` · Cheapest ${fmt(extra.rerating.cheapest.value)} on ${extra.rerating.cheapest.date}` : ''}
              </p>
            ) : null}
            {pack.data_sources?.length ? (
              <p className="vp-muted" style={{ marginTop: '0.75rem', fontSize: '0.8rem' }}>
                Sources: {pack.data_sources.join(' · ')}
              </p>
            ) : null}
          </div>
        ) : null}

        {extra.pct?.percentiles ? (
          <div className="vp-table-wrap">
            <table className="vp-table">
              <thead>
                <tr>
                  <th>Window</th>
                  <th>Current</th>
                  <th>Median</th>
                  <th>Percentile</th>
                  <th>Premium</th>
                  <th>Obs</th>
                  <th>Span</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(extra.pct.percentiles).map(([w, row]) => (
                  <tr key={w}>
                    <td>{w}</td>
                    <td>{fmt(row.current)}</td>
                    <td>{fmt(row.median)}</td>
                    <td>{row.current_percentile != null ? `${fmt(row.current_percentile, 1)}%` : '—'}</td>
                    <td>{row.premium_to_median_pct != null ? `${fmt(row.premium_to_median_pct, 1)}%` : '—'}</td>
                    <td>{row.observation_count ?? '—'}</td>
                    <td>{row.span_years != null ? `${fmt(row.span_years, 1)}y` : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="vp-muted">Enter a symbol and lookup to load historical valuation intelligence.</p>
        )}
      </div>
    </div>
  );
}
