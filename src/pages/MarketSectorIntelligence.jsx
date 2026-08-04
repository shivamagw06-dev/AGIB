import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Activity, ArrowLeft, RefreshCw, TrendingUp } from 'lucide-react';
import { getMiDashboard, getMiSector } from '@/lib/intelligenceApi';
import useMarketIntelligence from '@/hooks/useMarketIntelligence';
import './marketSectorIntelligence.css';

const HEATMAP_CLASS = {
  dark_green: 'msi-heat-dark-green',
  light_green: 'msi-heat-light-green',
  grey: 'msi-heat-grey',
  orange: 'msi-heat-orange',
  dark_red: 'msi-heat-dark-red',
};

function fmt(v, d = 2) {
  if (v == null || v === '') return '—';
  if (typeof v === 'number') return Number.isInteger(v) ? String(v) : v.toFixed(d);
  return String(v);
}

function Stat({ label, value, hint }) {
  return (
    <div className="msi-stat">
      <span className="k">{label}</span>
      <span className="v">{value}</span>
      {hint ? <span className="h">{hint}</span> : null}
    </div>
  );
}

function Section({ title, subtitle, children }) {
  return (
    <section className="msi-section">
      <header>
        <h2>{title}</h2>
        {subtitle ? <p>{subtitle}</p> : null}
      </header>
      {children}
    </section>
  );
}

export default function MarketSectorIntelligence() {
  const { indexSentiments = [], pulse, loading: pulseLoading } = useMarketIntelligence();
  const [pack, setPack] = useState(null);
  const [sectorPack, setSectorPack] = useState(null);
  const [selectedSector, setSelectedSector] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getMiDashboard();
      setPack(data);
      if (!data?.ok) setError(data?.error || 'Dashboard unavailable');
    } catch (err) {
      setError(err?.message || 'Failed to load market intelligence');
      setPack(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const openSector = async (sector) => {
    setSelectedSector(sector);
    setSectorPack(null);
    try {
      const data = await getMiSector(sector);
      setSectorPack(data);
    } catch {
      setSectorPack(null);
    }
  };

  const overview = pack?.overview || {};
  const breadth = pack?.breadth || {};
  const flows = pack?.flows || {};
  const heatmap = pack?.sector_heatmap || [];
  const sectors = pack?.sectors || [];
  const opps = pack?.opportunities?.cards || [];
  const priorities = pack?.research_priorities || [];

  return (
    <div className="msi-root">
      <header className="msi-header">
        <Link to="/market-intelligence" className="msi-back"><ArrowLeft size={14} /> Market desk</Link>
        <div className="msi-head-row">
          <div>
            <p className="msi-kicker"><Activity size={14} /> AGI Market & Sector Intelligence</p>
            <h1>Institutional market overview</h1>
            <p>Warehouse → Unified Valuation Engine → Market Intelligence Engine. No buy/sell — research priorities only.</p>
          </div>
          <button type="button" className="msi-btn" onClick={load} disabled={loading}>
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
      </header>

      <main className="msi-body">
        {error ? <div className="msi-error">{error}</div> : null}
        {loading ? <p className="msi-hint">Loading market intelligence…</p> : null}

        {pack?.ok ? (
          <>
            <Section
              title="Market overview"
              subtitle={`Valuation as of ${overview.valuation_date || '—'} · ${overview.companies || 0} companies · PE coverage ${overview.coverage?.pct != null ? overview.coverage.pct : '—'}%`}
            >
              <div className="msi-index-row">
                {(indexSentiments.length ? indexSentiments : pulse?.indices || []).length ? (
                  (indexSentiments.length ? indexSentiments : pulse?.indices || []).slice(0, 5).map((idx) => (
                    <Stat
                      key={idx.name || idx.symbol}
                      label={idx.name || idx.symbol}
                      value={idx.value ?? idx.ltp ?? '—'}
                      hint={idx.sentiment || idx.change_pct != null ? `${fmt(idx.change_pct)}%` : 'Live gateway'}
                    />
                  ))
                ) : (
                  <p className="msi-hint">Index quotes unavailable from live gateway for this session.</p>
                )}
              </div>
              <div className="msi-grid">
                <Stat label="Median P/E" value={fmt(overview.averages?.pe)} />
                <Stat label="Median P/B" value={fmt(overview.averages?.pb)} />
                <Stat label="Median EV/EBITDA" value={fmt(overview.averages?.ev_ebitda)} />
                <Stat label="Median Div Yield" value={`${fmt(overview.averages?.dividend_yield)}%`} />
                <Stat label="Breadth" value={breadth.heatmap || '—'} hint={`${breadth.advancing || 0}↑ ${breadth.declining || 0}↓`} />
                <Stat label="Sentiment" value={breadth.sentiment || '—'} />
              </div>
              {pack.summary ? <blockquote className="msi-summary">{pack.summary}</blockquote> : null}
            </Section>

            <Section title="Sector valuation heatmap" subtitle="Historical valuation percentile · click a sector">
              <div className="msi-heatmap">
                {heatmap.map((s) => (
                  <button
                    type="button"
                    key={s.sector}
                    className={`msi-heat-cell ${HEATMAP_CLASS[s.heatmap_band] || 'msi-heat-grey'} ${selectedSector === s.sector ? 'on' : ''}`}
                    onClick={() => openSector(s.sector)}
                  >
                    <strong>{s.sector}</strong>
                    <span>{fmt(s.historical_percentile, 0)}%ile</span>
                    <span className="tag">{s.opportunity}</span>
                  </button>
                ))}
              </div>
            </Section>

            {selectedSector && sectorPack?.ok ? (
              <Section title={`${selectedSector} intelligence`} subtitle={sectorPack.agi_sector_intelligence}>
                <p className="msi-hint">{sectorPack.lens?.rationale || sectorPack.lens?.primary_metric_label}</p>
                <div className="msi-grid sm">
                  <Stat label="Companies" value={fmt(sectorPack.companies, 0)} />
                  <Stat label="Primary metric" value={sectorPack.valuation?.primary_metric_label || '—'} />
                  <Stat label="Median" value={fmt(sectorPack.valuation?.current)} />
                </div>
              </Section>
            ) : null}

            <Section
              title="Sector intelligence"
              subtitle={
                sectors.some((s) => (s.upstox_coverage_pct || 0) > 0)
                  ? 'Primary metric · current · Upstox sector benchmark · premium · opportunity'
                  : 'Primary metric · current · sector benchmark awaits Upstox ISIN key-ratios (Upstox column is 0%)'
              }
            >
              <div className="msi-table-wrap">
                <table className="msi-table">
                  <thead>
                    <tr>
                      <th>Sector</th>
                      <th>Metric</th>
                      <th>Current</th>
                      <th>Sector</th>
                      <th>Premium</th>
                      <th>Hist %ile</th>
                      <th>Opportunity</th>
                      <th>Upstox</th>
                      <th>Cos</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sectors.map((s) => (
                      <tr key={s.sector} onClick={() => openSector(s.sector)} className="click">
                        <td><strong>{s.sector}</strong></td>
                        <td>{s.primary_metric_label}</td>
                        <td>{fmt(s.current)}</td>
                        <td>
                          {(s.upstox_coverage_pct || 0) > 0
                            ? fmt(s.sector_benchmark ?? s.historical_median)
                            : '—'}
                        </td>
                        <td>
                          {(s.upstox_coverage_pct || 0) > 0 && s.premium_pct != null
                            ? `${fmt(s.premium_pct, 1)}%`
                            : '—'}
                        </td>
                        <td>{fmt(s.historical_percentile, 0)}</td>
                        <td>{s.opportunity}</td>
                        <td>{s.upstox_coverage_pct != null ? `${fmt(s.upstox_coverage_pct, 0)}%` : '—'}</td>
                        <td>{fmt(s.companies, 0)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Section>

            <Section
              title="Institutional flow (FII / DII)"
              subtitle={flows.available ? `Latest ${flows.latest_date}` : 'Warehouse institutional_flow'}
            >
              {flows.available ? (
                <>
                  <div className="msi-grid">
                    <Stat label="FII net" value={fmt(flows.fii_net_buy ?? -(flows.fii_net_sell || 0))} />
                    <Stat label="DII net" value={fmt(flows.dii_net_buy ?? -(flows.dii_net_sell || 0))} />
                    <Stat label="Combined" value={fmt(flows.net_institutional_flow)} />
                    <Stat label="5D trend" value={fmt(flows.trend_5d)} />
                    <Stat label="20D trend" value={fmt(flows.trend_20d)} />
                  </div>
                  {flows.explanation ? <p className="msi-note">{flows.explanation}</p> : null}
                </>
              ) : (
                <div className="msi-empty-flow">
                  <p className="msi-hint"><strong>No data collected yet</strong></p>
                  <p className="msi-hint">Last successful refresh: Never</p>
                  <p className="msi-hint">
                    Daily EOD ingest runs automatically at 18:05 IST after market close
                    (Upstox → DQIV → warehouse). Admin may also trigger refresh from Mission Control.
                  </p>
                </div>
              )}
            </Section>

            <Section title="Today's opportunities" subtitle="Research candidates — not recommendations">
              <div className="msi-opp-grid">
                {opps.slice(0, 12).map((c) => (
                  <article key={`${c.kind}-${c.symbol}`} className="msi-opp-card">
                    <span className="kind">{c.kind.replace(/_/g, ' ')}</span>
                    <h3>{c.company_name || c.symbol}</h3>
                    <p>{c.why}</p>
                    <Link to={`/valuation-terminal?symbol=${encodeURIComponent(c.symbol)}`}>Open valuation →</Link>
                  </article>
                ))}
              </div>
            </Section>

            <Section title="Research priorities" subtitle="Ranked for analyst attention today">
              <div className="msi-table-wrap">
                <table className="msi-table">
                  <thead>
                    <tr><th>Rank</th><th>Company</th><th>Reason</th><th>Confidence</th></tr>
                  </thead>
                  <tbody>
                    {priorities.map((p) => (
                      <tr key={p.rank}>
                        <td>{p.rank}</td>
                        <td><Link to={`/valuation-terminal?symbol=${p.symbol}`}>{p.company_name || p.symbol}</Link></td>
                        <td>{p.reason}</td>
                        <td>{fmt(p.confidence, 0)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Section>

            {pack.rotation?.explanation ? (
              <Section title="Market rotation" subtitle="Money leaving → entering">
                <p className="msi-note">{pack.rotation.explanation}</p>
              </Section>
            ) : null}

            {pack.explainability?.length ? (
              <Section title="Market explainability" subtitle="Dependency-graph attribution">
                <ul className="msi-explain">
                  {pack.explainability.map((e) => (
                    <li key={e.sector}><strong>{e.sector}</strong> — {e.summary}</li>
                  ))}
                </ul>
              </Section>
            ) : null}

            <Section title="Provenance & coverage" subtitle="Every widget reads warehouse or engine">
              <div className="msi-prov">
                <div><span>Valuation</span><strong>{pack.provenance?.valuation}</strong></div>
                <div><span>Price / breadth</span><strong>{pack.provenance?.price}</strong></div>
                <div><span>Consensus</span><strong>{pack.provenance?.consensus}</strong></div>
                <div><span>Engine</span><strong>{pack.engine} v{pack.version}</strong></div>
                <div><span>Coverage</span><strong>{fmt(pack.coverage?.companies, 0)} cos</strong></div>
              </div>
            </Section>
          </>
        ) : null}

        {!loading && !pulseLoading && !pack?.ok && !error ? (
          <p className="msi-hint"><TrendingUp size={14} /> Waiting for warehouse valuation coverage.</p>
        ) : null}
      </main>
    </div>
  );
}
