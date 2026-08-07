import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Activity, ArrowLeft, BarChart3, Database, RefreshCw, TrendingUp } from 'lucide-react';
import { getMiDashboard, getMiSector } from '@/lib/intelligenceApi';
import useMarketIntelligence from '@/hooks/useMarketIntelligence';
import useMarketSnapshot from '@/hooks/useMarketSnapshot';
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

function fmtFlow(buy, sell) {
  if (buy != null) return fmt(buy);
  if (sell != null) return fmt(-sell);
  return '—';
}

function breadthHint(b) {
  const adv = b.advancing ?? 0;
  const dec = b.declining ?? 0;
  const flat = b.unchanged ?? 0;
  let hint = `${adv}↑ ${dec}↓ ${flat}→`;
  if (b.universe_total != null && b.not_tracked > 0) {
    hint += ` · ${b.not_tracked} untracked`;
  }
  return hint;
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

/** Index cards for MSI overview — prefer live snapshot quotes; else AGI sentiment labels. */
function buildIndexCards(snapshotItems = [], indexSentiments = [], pulseIndices = []) {
  const live = (Array.isArray(snapshotItems) ? snapshotItems : [])
    .filter((row) => row && (row.name || row.symbol) && Number(row.price || row.ltp || row.value) > 0)
    .slice(0, 5)
    .map((row) => {
      const change = row.percentChange ?? row.change_pct ?? row.changePct;
      return {
        key: row.name || row.symbol,
        label: row.name || row.symbol,
        value: row.price ?? row.ltp ?? row.value,
        hint: change != null && change !== '' ? `${fmt(Number(change))}%` : 'Live quote',
      };
    });
  if (live.length) return live;

  const sentiments = (Array.isArray(indexSentiments) && indexSentiments.length
    ? indexSentiments
    : Array.isArray(pulseIndices)
      ? pulseIndices
      : [])
    .filter((row) => row && (row.label || row.name || row.symbol || row.key))
    .slice(0, 5)
    .map((row) => {
      const label = row.label || row.name || row.symbol || row.key;
      const quote = row.value ?? row.ltp ?? row.price;
      if (quote != null && quote !== '') {
        const change = row.change_pct ?? row.percentChange;
        return {
          key: row.key || label,
          label,
          value: quote,
          hint:
            change != null && change !== ''
              ? `${fmt(Number(change))}%`
              : row.sentiment || 'Index',
        };
      }
      return {
        key: row.key || label,
        label,
        value: row.sentiment || 'Pending',
        hint: row.strength || 'AGI index signal',
      };
    });
  return sentiments;
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

function Sparkline({ points = [], current }) {
  const values = points.map((point) => Number(point?.value)).filter(Number.isFinite);
  const all = Number.isFinite(Number(current)) ? [...values, Number(current)] : values;
  if (all.length < 2) return <p className="msi-hint">Verified historical points will appear as coverage develops.</p>;
  const lo = Math.min(...all);
  const hi = Math.max(...all);
  const span = Math.max(hi - lo, 0.0001);
  const coordinates = values.map((value, index) => {
    const x = 4 + (index * 232) / Math.max(values.length - 1, 1);
    const y = 58 - ((value - lo) / span) * 48;
    return `${x},${y}`;
  }).join(' ');
  return (
    <div className="msi-chart" aria-label="Historical valuation series">
      <svg viewBox="0 0 240 64" role="img">
        <line x1="4" x2="236" y1="58" y2="58" />
        <polyline points={coordinates} fill="none" />
      </svg>
      <div className="msi-chart-labels"><span>{points[0]?.period || 'History'}</span><span>{points.at(-1)?.period || 'Current'}</span></div>
    </div>
  );
}

function CoverageBadge({ snapshot = {} }) {
  const confidence = snapshot.confidence || 'Insufficient';
  return <span className={`msi-confidence msi-confidence-${confidence.toLowerCase()}`}>{confidence} confidence</span>;
}

export default function MarketSectorIntelligence() {
  const { indexSentiments = [], pulse } = useMarketIntelligence();
  const { items: snapshotItems = [] } = useMarketSnapshot();
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
  const regime = pack?.market_regime || {};
  const marketHealth = pack?.market_health || {};
  const drivers = pack?.market_drivers?.drivers || [];
  const breadth = pack?.breadth || {};
  const flows = pack?.flows || {};
  const heatmap = pack?.sector_heatmap || [];
  const sectors = pack?.sectors || [];
  const opps = pack?.opportunities?.cards || [];
  const priorities = pack?.research_priorities || [];
  const rotation = pack?.rotation || {};
  const selectedResearch = sectorPack?.research || {};
  const indexCards = useMemo(
    () => buildIndexCards(snapshotItems, indexSentiments, pulse?.indices || []),
    [snapshotItems, indexSentiments, pulse],
  );

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
              subtitle={`Constitution v${pack.constitution || '2.0'} · Valuation as of ${overview.valuation_date || '—'} · ${overview.companies || 0} companies · PE coverage ${overview.coverage?.pct != null ? overview.coverage.pct : '—'}%`}
            >
              <div className="msi-index-row">
                {indexCards.length ? (
                  indexCards.map((idx) => (
                    <Stat
                      key={idx.key}
                      label={idx.label}
                      value={fmt(idx.value)}
                      hint={idx.hint}
                    />
                  ))
                ) : (
                  <p className="msi-hint">Index quotes unavailable from live gateway for this session.</p>
                )}
              </div>
              <div className="msi-grid">
                <Stat label="Market regime" value={regime.regime || '—'} hint={regime.drivers?.slice(0, 2).join(' · ')} />
                <Stat label="Market health" value={marketHealth.overall != null ? `${marketHealth.overall}/100` : '—'} />
                <Stat label="Hist %ile (market)" value={fmt(marketHealth.market_historical_percentile, 0)} hint="Sector median of historical percentiles" />
                <Stat label="Median P/E" value={fmt(overview.averages?.pe)} />
                <Stat label="Median P/B" value={fmt(overview.averages?.pb)} />
                <Stat label="Median EV/EBITDA" value={fmt(overview.averages?.ev_ebitda)} />
                <Stat label="Breadth" value={breadth.heatmap || '—'} hint={breadthHint(breadth)} />
                <Stat label="Breadth coverage" value={breadth.coverage_pct != null ? `${fmt(breadth.coverage_pct, 1)}%` : '—'} hint={`${breadth.tracked_universe || breadth.sample_size || 0} tracked`} />
              </div>
              {breadth.universe_definition ? <p className="msi-hint">{breadth.universe_definition}</p> : null}
              {pack.summary ? <blockquote className="msi-summary">{pack.summary}</blockquote> : null}
            </Section>

            <Section
              title="Sector valuation map"
              subtitle={`Historical valuation percentile · data through ${overview.valuation_date || '—'} · colours describe valuation range, not expected return · click a sector`}
            >
              <div className="msi-sector-nav" aria-label="Sector navigation">
                {sectors.map((s) => (
                  <button type="button" key={`nav-${s.sector}`} onClick={() => openSector(s.sector)} className={selectedSector === s.sector ? 'on' : ''}>
                    {s.sector}<small>{s.historical_percentile != null ? `${fmt(s.historical_percentile, 0)}%ile` : 'coverage'}</small>
                  </button>
                ))}
              </div>
              <div className="msi-heatmap">
                {heatmap.map((s) => (
                  <button
                    type="button"
                    key={s.sector}
                    className={`msi-heat-cell ${HEATMAP_CLASS[s.heatmap_band] || 'msi-heat-grey'} ${selectedSector === s.sector ? 'on' : ''}`}
                    onClick={() => openSector(s.sector)}
                  >
                    <strong>{s.sector}</strong>
                    <span>
                      {s.historical_percentile != null
                        ? `${fmt(s.historical_percentile, 0)}%ile`
                        : (s.historical_percentile_status === 'DATA_QUALITY_FAIL' ? 'unreliable' : 'coverage developing')}
                    </span>
                    <span className="tag">{s.historical_range_status || s.opportunity}</span>
                    {s.historical_observations != null ? (
                      <span className="msi-obs">{s.historical_observation_label || `${s.historical_observations} observations`} · {s.historical_years ? `${s.historical_years} yrs · ` : ''}{s.historical_confidence || 'Developing'} confidence</span>
                    ) : null}
                  </button>
                ))}
              </div>
            </Section>

            {selectedSector && sectorPack?.ok ? (
              <>
                <Section title={`${selectedSector} — sector snapshot`} subtitle={sectorPack.agi_sector_intelligence}>
                  <div className="msi-sector-hero">
                    <div className="msi-sector-title"><span>AGI Sector View</span><h2>{selectedSector}</h2><CoverageBadge snapshot={selectedResearch.snapshot} /></div>
                    <div className="msi-grid sm">
                      <Stat label="Valuation regime" value={selectedResearch.view?.valuation || '—'} />
                      <Stat label="Historical percentile" value={sectorPack.valuation?.historical_percentile != null ? `${fmt(sectorPack.valuation.historical_percentile, 0)}%ile` : 'Developing'} />
                      <Stat label={sectorPack.valuation?.primary_metric_label || 'Primary metric'} value={fmt(sectorPack.valuation?.current)} />
                      <Stat label="Historical median" value={fmt(sectorPack.valuation?.historical_median)} />
                      <Stat label="Companies" value={fmt(selectedResearch.snapshot?.companies || sectorPack.companies, 0)} />
                      <Stat label="Historical coverage" value={selectedResearch.snapshot?.coverage_pct != null ? `${fmt(selectedResearch.snapshot.coverage_pct, 0)}%` : '—'} hint={`${selectedResearch.snapshot?.historical_years || 0} verified years`} />
                    </div>
                  </div>
                </Section>

                <Section title="Valuation intelligence" subtitle={`${selectedResearch.valuation_history?.label || 'Primary valuation metric'} · ${selectedResearch.valuation_history?.source || 'verified warehouse history'}`}>
                  <div className="msi-detail-grid">
                    <div>
                      <Sparkline points={selectedResearch.valuation_history?.points} current={selectedResearch.valuation_history?.current} />
                      <p className="msi-hint">Current value is ranked against valid historical sector observations. Missing constituents reduce coverage; they do not erase the available history.</p>
                    </div>
                    <div className="msi-band-grid">
                      {Object.entries(selectedResearch.valuation_history?.bands || {}).map(([label, value]) => <Stat key={label} label={label} value={fmt(value)} />)}
                    </div>
                  </div>
                </Section>

                <Section title="Fundamental intelligence" subtitle="Current sector medians from the verified company universe; coverage is shown per metric.">
                  <div className="msi-fundamentals">
                    {(selectedResearch.fundamentals || []).map((item) => <Stat key={item.key} label={item.label} value={fmt(item.current)} hint={`${item.interpretation} · ${fmt(item.coverage_pct, 0)}% coverage`} />)}
                  </div>
                </Section>

                <Section title="Industry breakdown" subtitle="Constituent industries ranked by covered company count.">
                  <div className="msi-table-wrap"><table className="msi-table"><thead><tr><th>Industry</th><th>Companies</th><th>Median P/E</th><th>Median P/B</th><th>Median ROE</th></tr></thead><tbody>
                    {(selectedResearch.industries || []).map((row) => <tr key={row.industry}><td><strong>{row.industry}</strong></td><td>{row.companies}</td><td>{fmt(row.median_pe)}</td><td>{fmt(row.median_pb)}</td><td>{fmt(row.median_roe)}</td></tr>)}
                  </tbody></table></div>
                </Section>

                <Section title="Company leaders and valuation context" subtitle="Largest constituents first. This is a research starting point, not a security recommendation.">
                  <div className="msi-table-wrap"><table className="msi-table"><thead><tr><th>Company</th><th>Industry</th><th>P/E</th><th>P/B</th><th>ROE</th><th>Hist. %ile</th></tr></thead><tbody>
                    {(selectedResearch.companies || []).slice(0, 15).map((row) => <tr key={row.symbol}><td><Link to={`/valuation-terminal?symbol=${encodeURIComponent(row.symbol || '')}`}>{row.company_name || row.symbol}</Link></td><td>{row.industry || '—'}</td><td>{fmt(row.pe)}</td><td>{fmt(row.pb)}</td><td>{fmt(row.roe)}</td><td>{row.historical_percentile != null ? `${fmt(row.historical_percentile, 0)}%ile` : '—'}</td></tr>)}
                  </tbody></table></div>
                </Section>
              </>
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
                      <th>History</th>
                      <th>Hist range</th>
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
                        <td title={s.historical_percentile_reason || ''}>
                          {s.historical_percentile != null
                            ? `${fmt(s.historical_percentile, 0)}%ile`
                            : (s.historical_percentile_status === 'INSUFFICIENT_HISTORY'
                              ? `Limited (${s.historical_observations || 0})`
                              : s.historical_percentile_status === 'DATA_QUALITY_FAIL'
                                ? 'unreliable'
                                : '—')}
                        </td>
                        <td>{s.historical_range_status || s.opportunity}</td>
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
              subtitle={
                flows.available
                  ? flows.latest_values_available === false
                    ? `History through ${flows.latest_date} · latest session unavailable`
                    : `Latest ${flows.latest_date}`
                  : 'Warehouse institutional_flow'
              }
            >
              {flows.available ? (
                <>
                  <div className="msi-grid">
                    <Stat
                      label="FII net"
                      value={
                        flows.latest_values_available === false
                          ? 'Awaiting EOD print'
                          : fmtFlow(flows.fii_net_buy ?? flows.fii_net, flows.fii_net_sell)
                      }
                    />
                    <Stat
                      label="DII net"
                      value={
                        flows.latest_values_available === false
                          ? 'Awaiting EOD print'
                          : fmtFlow(flows.dii_net_buy ?? flows.dii_net, flows.dii_net_sell)
                      }
                    />
                    <Stat
                      label="Combined"
                      value={flows.latest_values_available === false ? '—' : fmt(flows.net_institutional_flow)}
                    />
                    <Stat label="5D trend" value={fmt(flows.trend_5d)} />
                    <Stat label="20D trend" value={fmt(flows.trend_20d)} />
                  </div>
                  {flows.latest_values_available === false ? (
                    <p className="msi-hint">
                      Flow history exists through {flows.latest_date || 'recent sessions'}, but net FII/DII
                      values are still null in warehouse (Upstox EOD often lands after 18:05 IST).
                    </p>
                  ) : null}
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

            <Section title="Today’s research candidates" subtitle="Evidence-backed starting points for research — not recommendations">
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

            {drivers.length ? (
              <Section title="Market drivers" subtitle="Top institutional drivers today — magnitude and affected sectors">
                <ul className="msi-explain">
                  {drivers.map((d) => (
                    <li key={d.driver}>
                      <strong>{d.driver}</strong> ({d.direction}) — {d.detail}
                      {d.affected_sectors?.length ? ` · Sectors: ${d.affected_sectors.join(', ')}` : ''}
                    </li>
                  ))}
                </ul>
              </Section>
            ) : null}

            {pack.rotation?.explanation ? (
              <Section title="Market rotation" subtitle="Valuation rotation — compression → expansion; this is not a measured fund-flow claim.">
                <p className="msi-note">{pack.rotation.explanation}</p>
                <div className="msi-grid sm">
                  {(pack.rotation.leaving || []).length ? (
                    <Stat
                      label="Leaving"
                      value={(rotation.leaving || []).map((r) => r.sector).join(', ')}
                      hint={(rotation.leaving || []).map((r) => `${r.median_pe_change_pct ?? r.avg_pe_change_pct}%`).join(', ')}
                    />
                  ) : null}
                  {(pack.rotation.entering || []).length ? (
                    <Stat
                      label="Entering"
                      value={(rotation.entering || []).map((r) => r.sector).join(', ')}
                      hint={(rotation.entering || []).map((r) => `${r.median_pe_change_pct ?? r.avg_pe_change_pct}%`).join(', ')}
                    />
                  ) : null}
                </div>
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

            <Section title="Provenance & validation" subtitle="Constitution v2.0 — auditable warehouse-backed intelligence">
              <div className="msi-prov">
                <div><span>Valuation</span><strong>{pack.provenance?.valuation}</strong></div>
                <div><span>Price / breadth</span><strong>{pack.provenance?.price}</strong></div>
                <div><span>Fresh through</span><strong>{overview.valuation_date || '—'}</strong></div>
                <div><span>Engine</span><strong>{pack.engine} v{pack.version}</strong></div>
                <div><span>Coverage</span><strong>{fmt(pack.coverage?.companies, 0)} cos</strong></div>
                <div><span>Validation</span><strong>{pack.validation?.publishable ? 'Passed' : `${pack.validation?.checks_passed || 0}/${pack.validation?.checks_total || 0} checks`}</strong></div>
                <div><span>Confidence</span><strong className="msi-hint-inline">{pack.confidence?.methodology?.slice(0, 80)}…</strong></div>
                <div><span>Historical hierarchy</span><strong><Database size={13} /> CapIQ → normalized warehouse → HVIE → verified provider ratios</strong></div>
              </div>
            </Section>
          </>
        ) : null}

        {!loading && !pack?.ok && !error ? (
          <p className="msi-hint"><TrendingUp size={14} /> Waiting for warehouse valuation coverage.</p>
        ) : null}
      </main>
    </div>
  );
}
