import { useEffect, useMemo, useState } from 'react';
import {
  getSveOpportunities,
  getSvePremium,
  getSveRerating,
  getSveSector,
  getSveSectorLeaders,
  getSveSectorResearch,
  getSveSectorRotation,
} from '@/lib/intelligenceApi';

function fmt(v, digits = 2) {
  if (v == null || v === '') return '—';
  if (typeof v === 'number') {
    if (Math.abs(v) >= 1e12) return `₹${(v / 1e12).toFixed(1)}T`;
    if (Math.abs(v) >= 1e7) return `₹${(v / 1e7).toFixed(0)} cr`;
    if (Math.abs(v) >= 1000) return v.toLocaleString(undefined, { maximumFractionDigits: 0 });
    return Number.isInteger(v) ? String(v) : v.toFixed(digits);
  }
  return String(v);
}

function statusClass(status) {
  const s = String(status || '').toLowerCase();
  if (s.includes('cheap') || s.includes('undervalued') || s.includes('attractive')) return 'sve-status-cheap';
  if (s.includes('expensive') || s.includes('premium')) return 'sve-status-rich';
  if (s.includes('insufficient') || s.includes('not applicable')) return 'sve-status-na';
  return 'sve-status-fair';
}

function DistBars({ dist, label }) {
  const bins = dist?.bins || [];
  const max = Math.max(1, ...bins.map((b) => b.count || 0));
  if (!bins.length) return <p className="hint">No {label} distribution.</p>;
  return (
    <div className="sve-dist">
      <div className="sve-dist-label">{label}</div>
      <div className="sve-dist-bars">
        {bins.map((b, i) => (
          <div key={i} className="sve-dist-col" title={`${fmt(b.start)}–${fmt(b.end)}: ${b.count}`}>
            <div className="sve-dist-bar" style={{ height: `${Math.max(6, (100 * b.count) / max)}%` }} />
          </div>
        ))}
      </div>
      <div className="sve-dist-meta">
        <span>n={dist.count}</span>
        <span>med {fmt(dist.median)}</span>
      </div>
    </div>
  );
}

function MetricTip({ label, value, sector, industry, hist, pct, source, confidence }) {
  return (
    <span className="sve-tip" tabIndex={0}>
      {value}
      <span className="sve-tip-pop" role="tooltip">
        <strong>{label}</strong>
        <div>Current · {value}</div>
        {sector != null ? <div>Sector · {fmt(sector)}</div> : null}
        {industry != null ? <div>Industry · {fmt(industry)}</div> : null}
        {hist != null ? <div>Historical median · {fmt(hist)}</div> : null}
        {pct != null ? <div>Historical % · {fmt(pct, 0)}</div> : null}
        <div className="hint">Source · {source || 'Warehouse / HVIE'}</div>
        {confidence != null ? <div className="hint">Confidence · {fmt(confidence, 0)}%</div> : null}
      </span>
    </span>
  );
}

const QUICK = [
  { id: 'cheap', label: 'Historically Cheap', apply: (r) => String(r.valuation_status || '').toLowerCase().includes('cheap') },
  { id: 'expensive', label: 'Historically Expensive', apply: (r) => String(r.valuation_status || '').toLowerCase().includes('expensive') },
  { id: 'premium', label: 'Premium', apply: (r) => String(r.valuation_status || '').toLowerCase().includes('premium') || String(r.valuation_status || '').includes('Expensive') },
  { id: 'fair', label: 'Fair', apply: (r) => String(r.valuation_status || '').toLowerCase().includes('fair') },
  { id: 'deep', label: 'Deep Value', apply: (r) => (r.historical_percentile != null && r.historical_percentile <= 15) },
  { id: 'growth', label: 'Growth Premium', apply: (r) => (r.premium_pct != null && r.premium_pct >= 25 && (r.roe || 0) >= 18) },
  { id: 'roe', label: 'Highest ROE', sort: 'roe' },
  { id: 'roce', label: 'Highest ROCE', sort: 'roce' },
  { id: 'discount', label: 'Largest Discount', sort: 'premium_pct', order: 'asc' },
  { id: 'low_pct', label: 'Lowest Hist %', sort: 'historical_percentile', order: 'asc' },
  { id: 'high_pct', label: 'Highest Hist %', sort: 'historical_percentile' },
  { id: 'large', label: 'Large Cap', bucket: 'large' },
  { id: 'mid', label: 'Mid Cap', bucket: 'mid' },
  { id: 'small', label: 'Small Cap', bucket: 'small' },
  { id: 'hi_conf', label: 'High Confidence', apply: (r) => (r.confidence || 0) >= 0.85 || (r.coverage?.provider || 0) >= 3 },
  { id: 'low_cov', label: 'Low Coverage', apply: (r) => !(r.coverage?.provider) },
];

function copyText(text) {
  if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
    return navigator.clipboard.writeText(text);
  }
  return Promise.resolve();
}

function rowsToCsv(rows) {
  const cols = [
    'symbol', 'company_name', 'cmp', 'market_cap', 'sector', 'industry',
    'pe', 'sector_pe', 'industry_pe', 'premium_pct', 'historical_percentile',
    'pb', 'sector_pb', 'roe', 'roce', 'ev_ebitda', 'historical_regime',
    'valuation_status',
  ];
  const header = cols.join(',');
  const body = rows.map((r) => cols.map((c) => {
    const v = r[c];
    if (v == null) return '';
    const s = String(v).replace(/"/g, '""');
    return s.includes(',') ? `"${s}"` : s;
  }).join(',')).join('\n');
  return `${header}\n${body}`;
}

export function MarketSnapshot({ market, loading }) {
  if (loading) return <section className="sve-market hint">Loading Indian market snapshot…</section>;
  if (!market?.ok) return null;
  return (
    <section className="sve-market">
      <div className="sve-directory-head">
        <h3>Indian Market</h3>
        <p className="hint">
          Market valuation snapshot · as of {market.as_of || market.last_updated || '—'} · warehouse-backed
        </p>
      </div>
      <div className="sve-market-grid">
        <div><span className="k">Companies Covered</span><span className="v">{fmt(market.companies_covered, 0)}</span></div>
        <div><span className="k">Coverage</span><span className="v">{market.coverage_pct != null ? `${fmt(market.coverage_pct, 1)}%` : '—'}</span></div>
        <div><span className="k">Median PE</span><span className="v">{fmt(market.median_pe)}</span></div>
        <div><span className="k">10Y Median PE</span><span className="v">{fmt(market.historical_median_pe)}</span></div>
        <div><span className="k">Premium</span><span className="v">{market.premium_pct != null ? `${fmt(market.premium_pct, 1)}%` : '—'}</span></div>
        <div><span className="k">Median PB</span><span className="v">{fmt(market.median_pb)}</span></div>
        <div><span className="k">Historical %</span><span className="v">{fmt(market.historical_percentile, 0)}</span></div>
        <div><span className="k">Market Regime</span><span className="v">{market.regime || '—'}</span></div>
        <div><span className="k">Median EV/EBITDA</span><span className="v">{fmt(market.median_ev_ebitda)}</span></div>
        <div><span className="k">Median ROE</span><span className="v">{fmt(market.median_roe)}</span></div>
        <div><span className="k">Median ROCE</span><span className="v">{fmt(market.median_roce)}</span></div>
        <div><span className="k">Dividend Yield</span><span className="v">{fmt(market.median_dividend_yield)}</span></div>
        <div><span className="k">Market Cap Covered</span><span className="v">{fmt(market.market_cap)}</span></div>
        <div><span className="k">Confidence</span><span className="v">{market.confidence != null ? `${fmt(market.confidence, 0)}%` : '—'}</span></div>
        <div className="sve-market-focus">
          <span className="k">Research Focus</span>
          <span className="v">{market.research_focus || '—'}</span>
        </div>
      </div>
      <p className="hint">Analysis only — not a recommendation. Provenance: {market.provenance?.universe || 'warehouse'}.</p>
    </section>
  );
}

export default function SectorValuationWorkspace({
  sector,
  industry: industryProp = '',
  onBack,
  onSelectIndustry,
  onClearIndustry,
  onSelectCompany,
  compare = [],
  onToggleCompare,
}) {
  const [pack, setPack] = useState(null);
  const [leaders, setLeaders] = useState(null);
  const [research, setResearch] = useState(null);
  const [rotation, setRotation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [industry, setIndustry] = useState(industryProp || '');
  const [quick, setQuick] = useState(null);
  const [sort, setSort] = useState('market_cap');
  const [order, setOrder] = useState('desc');
  const [dashTab, setDashTab] = useState('leaders');

  useEffect(() => {
    setIndustry(industryProp || '');
  }, [industryProp]);

  useEffect(() => {
    if (!sector) return undefined;
    let cancelled = false;
    setLoading(true);
    Promise.all([
      getSveSector(sector),
      getSveSectorLeaders(sector),
      getSveSectorResearch(sector),
      getSveSectorRotation(sector),
    ])
      .then(([p, l, r, rot]) => {
        if (cancelled) return;
        setPack(p);
        setLeaders(l);
        setResearch(r);
        setRotation(rot);
        setError(p?.ok === false ? p.error : null);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message || 'sector_load_failed');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [sector]);

  const industryCards = useMemo(() => {
    const list = pack?.industries || [];
    return list.map((ind) => (typeof ind === 'string' ? { industry: ind } : ind));
  }, [pack]);

  const rows = useMemo(() => {
    let list = [...(pack?.company_rows || [])];
    if (industry) list = list.filter((r) => r.industry === industry);
    const q = QUICK.find((x) => x.id === quick);
    if (q?.apply) list = list.filter(q.apply);
    if (q?.bucket) list = list.filter((r) => r.market_cap_bucket === q.bucket);
    const sortKey = q?.sort || sort;
    const sortOrder = q?.order || order;
    const reverse = sortOrder !== 'asc';
    list.sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (av == null && bv == null) return 0;
      if (av == null) return 1;
      if (bv == null) return -1;
      if (typeof av === 'number' && typeof bv === 'number') {
        return reverse ? bv - av : av - bv;
      }
      return reverse
        ? String(bv).localeCompare(String(av))
        : String(av).localeCompare(String(bv));
    });
    return list;
  }, [pack, industry, quick, sort, order]);

  const selectIndustry = (name) => {
    setIndustry(name);
    onSelectIndustry?.(name);
  };

  const clearIndustry = () => {
    setIndustry('');
    onClearIndustry?.();
  };

  const exportCsv = () => {
    const csv = rowsToCsv(rows);
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${sector.replace(/\s+/g, '_')}_valuation.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const copyTable = () => copyText(rowsToCsv(rows));
  const copySummary = () => {
    const o = pack?.outcome || {};
    const text = [
      pack?.sector,
      o.conclusion,
      `Overall: ${o.overall || '—'}`,
      `Confidence: ${o.confidence ?? '—'}%`,
      'Analysis only — not a recommendation.',
    ].filter(Boolean).join('\n');
    return copyText(text);
  };

  if (loading) return <div className="sve-workspace hint">Loading sector workspace…</div>;
  if (error) return <div className="sve-workspace sve-error">{error}</div>;
  if (!pack?.ok) return <div className="sve-workspace hint">Sector unavailable.</div>;

  const summary = pack.summary || {};
  const explanation = pack.explanation || {};
  const outcome = pack.outcome || {};
  const dists = pack.distributions || {};
  const activeIndustry = industryCards.find((c) => c.industry === industry);

  return (
    <div className="sve-workspace">
      <div className="sve-workspace-head">
        <button type="button" className="sve-back" onClick={onBack}>← All sectors</button>
        <div>
          <h2>{pack.sector}{industry ? ` · ${industry}` : ''}</h2>
          <p className="hint">
            {fmt(industry ? rows.length : pack.companies, 0)} companies · as of {pack.as_of || '—'} · warehouse → UVE / HVIE / VPAE
          </p>
        </div>
        <div className="sve-export">
          <button type="button" onClick={exportCsv}>Export CSV</button>
          <button type="button" onClick={copyTable}>Copy Table</button>
          <button type="button" onClick={copySummary}>Copy Research Summary</button>
        </div>
      </div>

      <section className="sve-dash">
        <div><span className="k">Current Median</span><span className="v">{fmt(activeIndustry?.median_pe ?? summary.current_median)} <small>{summary.primary_metric_label}</small></span></div>
        <div><span className="k">Historical Median</span><span className="v">{fmt(summary.historical_median)}</span></div>
        <div><span className="k">Premium</span><span className="v">{(activeIndustry?.premium_pct ?? summary.premium_pct) != null ? `${fmt(activeIndustry?.premium_pct ?? summary.premium_pct, 1)}%` : '—'}</span></div>
        <div><span className="k">Historical %ile</span><span className="v">{fmt(activeIndustry?.historical_percentile ?? summary.historical_percentile, 0)}</span></div>
        <div><span className="k">Market Cap</span><span className="v">{fmt(activeIndustry?.market_cap ?? summary.market_cap)}</span></div>
        <div><span className="k">Coverage</span><span className="v">{(activeIndustry?.coverage_pct ?? summary.coverage_pct) != null ? `${fmt(activeIndustry?.coverage_pct ?? summary.coverage_pct, 0)}%` : '—'}</span></div>
        <div><span className="k">Overall</span><span className="v">{outcome.overall || summary.overall || '—'}</span></div>
        <div><span className="k">Confidence</span><span className="v">{(activeIndustry?.confidence ?? outcome.confidence) != null ? `${fmt(activeIndustry?.confidence ?? outcome.confidence, 0)}%` : '—'}</span></div>
      </section>

      <section className="sve-panel">
        <div className="sve-panel-head">
          <h3>Industry workspace</h3>
          {industry ? (
            <button type="button" className="sve-back" onClick={clearIndustry}>Clear industry filter</button>
          ) : null}
        </div>
        <p className="hint">Sector → Industry → Company. Cards are warehouse medians — no UI calculations.</p>
        <div className="sve-cards sve-industry-cards">
          {industryCards.map((ind) => (
            <button
              key={ind.industry}
              type="button"
              className={`sve-card ${industry === ind.industry ? 'sve-card-on' : ''}`}
              onClick={() => selectIndustry(ind.industry)}
            >
              <div className="sve-card-title">{ind.industry}</div>
              <div className="sve-card-meta">{fmt(ind.companies, 0)} companies</div>
              <div className="sve-card-row"><span>Median PE</span><strong>{fmt(ind.median_pe)}</strong></div>
              <div className="sve-card-row"><span>Median PB</span><strong>{fmt(ind.median_pb)}</strong></div>
              <div className="sve-card-row"><span>EV/EBITDA</span><strong>{fmt(ind.median_ev_ebitda)}</strong></div>
              <div className="sve-card-row"><span>Historical %</span><strong>{fmt(ind.historical_percentile, 0)}</strong></div>
              <div className="sve-card-row"><span>Premium</span><strong>{ind.premium_pct != null ? `${fmt(ind.premium_pct, 1)}%` : '—'}</strong></div>
              <div className="sve-card-row"><span>ROE</span><strong>{fmt(ind.median_roe)}</strong></div>
              <div className={`sve-pill ${String(ind.opportunity || '').toLowerCase()}`}>
                {ind.opportunity || '—'} · cov {fmt(ind.coverage_pct, 0)}% · conf {fmt(ind.confidence, 0)}%
              </div>
            </button>
          ))}
        </div>
      </section>

      <div className="sve-two">
        <section className="sve-panel">
          <h3>Sector explanation</h3>
          <p className="sve-primary">
            Primary metric <strong>{explanation.primary_metric_label || '—'}</strong>
          </p>
          <p>{explanation.rationale || explanation.why}</p>
          {explanation.interpret ? <p className="hint">{explanation.interpret}</p> : null}
          <div className="sve-chips">
            {(explanation.supporting || []).map((m) => (
              <span key={m.metric} className="sve-chip">Supporting · {m.label}</span>
            ))}
            {(explanation.hidden || []).map((m) => (
              <span key={m.metric} className="sve-chip sve-chip-muted">Hidden · {m.label}</span>
            ))}
          </div>
          <p className="hint">Rules from sector_lens / VPAE — not duplicated in the UI.</p>
        </section>

        <section className="sve-panel sve-outcome">
          <h3>{outcome.title || 'Institutional outcome'}</h3>
          <p className="sve-conclusion">{outcome.conclusion}</p>
          <ul>
            {(outcome.evidence || []).map((e, i) => <li key={i}>{e}</li>)}
          </ul>
          <div className="sve-outcome-foot">
            <span>Overall <strong>{outcome.overall}</strong></span>
            <span>Confidence <strong>{fmt(outcome.confidence, 0)}%</strong></span>
          </div>
          <p className="hint">Analysis and evidence only — never BUY / SELL / target price.</p>
        </section>
      </div>

      <section className="sve-panel">
        <div className="sve-panel-head">
          <h3>Company valuation table{industry ? ` · ${industry}` : ''}</h3>
          <div className="sve-filters">
            <select
              value={industry}
              onChange={(e) => (e.target.value ? selectIndustry(e.target.value) : clearIndustry())}
            >
              <option value="">All industries</option>
              {industryCards.map((ind) => (
                <option key={ind.industry} value={ind.industry}>{ind.industry}</option>
              ))}
            </select>
            <select value={sort} onChange={(e) => setSort(e.target.value)}>
              <option value="market_cap">Market cap</option>
              <option value="pe">P/E</option>
              <option value="pb">P/B</option>
              <option value="roe">ROE</option>
              <option value="roce">ROCE</option>
              <option value="ev_ebitda">EV/EBITDA</option>
              <option value="premium_pct">Premium %</option>
              <option value="historical_percentile">Historical %</option>
            </select>
            <select value={order} onChange={(e) => setOrder(e.target.value)}>
              <option value="desc">Desc</option>
              <option value="asc">Asc</option>
            </select>
          </div>
        </div>
        <div className="sve-quick">
          {QUICK.map((q) => (
            <button
              key={q.id}
              type="button"
              className={quick === q.id ? 'on' : ''}
              onClick={() => setQuick(quick === q.id ? null : q.id)}
            >
              {q.label}
            </button>
          ))}
        </div>
        <div className="vi-table-wrap">
          <table className="vi-table sve-table">
            <thead>
              <tr>
                <th />
                <th>Company</th>
                <th>CMP</th>
                <th>Mkt Cap</th>
                <th>Industry</th>
                <th>P/E</th>
                <th>Sector PE</th>
                <th>Industry PE</th>
                <th>Premium %</th>
                <th>Hist %</th>
                <th>P/B</th>
                <th>Sector PB</th>
                <th>ROE</th>
                <th>ROCE</th>
                <th>EV/EBITDA</th>
                <th>Regime</th>
                <th>Status</th>
                <th>Cov</th>
                <th>Conf</th>
              </tr>
            </thead>
            <tbody>
              {rows.slice(0, 250).map((r) => (
                <tr key={r.symbol}>
                  <td>
                    <input
                      type="checkbox"
                      checked={compare.includes(r.symbol)}
                      disabled={!compare.includes(r.symbol) && compare.length >= 5}
                      onChange={() => onToggleCompare?.(r.symbol)}
                      aria-label={`Compare ${r.symbol}`}
                    />
                  </td>
                  <td>
                    <button type="button" className="sve-link" onClick={() => onSelectCompany(r.symbol, r.company_name)}>
                      <strong>{r.symbol}</strong>
                      <span>{r.company_name}</span>
                    </button>
                  </td>
                  <td>{fmt(r.cmp)}</td>
                  <td>{fmt(r.market_cap)}</td>
                  <td>{r.industry || '—'}</td>
                  <td>
                    <MetricTip
                      label="P/E"
                      value={fmt(r.pe)}
                      sector={r.sector_pe}
                      industry={r.industry_pe}
                      pct={r.historical_percentile}
                      source={r.source || r.coverage?.source}
                      confidence={(r.confidence || 0) * 100}
                    />
                  </td>
                  <td>{fmt(r.sector_pe)}</td>
                  <td>{fmt(r.industry_pe)}</td>
                  <td>{r.premium_pct != null ? `${fmt(r.premium_pct, 1)}%` : '—'}</td>
                  <td>{fmt(r.historical_percentile, 0)}</td>
                  <td>{fmt(r.pb)}</td>
                  <td>{fmt(r.sector_pb)}</td>
                  <td>{fmt(r.roe)}</td>
                  <td>{fmt(r.roce)}</td>
                  <td>{fmt(r.ev_ebitda)}</td>
                  <td>{r.historical_regime || '—'}</td>
                  <td><span className={`sve-status ${statusClass(r.valuation_status)}`}>{r.valuation_status}</span></td>
                  <td>{r.coverage?.provider || 0}</td>
                  <td>{r.confidence != null ? `${Math.round((r.confidence > 1 ? r.confidence : r.confidence * 100))}%` : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="hint">Showing {Math.min(rows.length, 250)} of {rows.length}. Values from warehouse via UVE / HVIE — no UI calculations.</p>
      </section>

      {compare.length >= 2 ? (
        <section className="sve-panel">
          <h3>Peer comparison ({compare.length})</h3>
          <div className="vi-table-wrap">
            <table className="vi-table sve-table">
              <thead>
                <tr>
                  <th>Company</th>
                  <th>P/E</th>
                  <th>P/B</th>
                  <th>EV/EBITDA</th>
                  <th>ROE</th>
                  <th>ROCE</th>
                  <th>Hist %</th>
                  <th>Premium %</th>
                  <th>Industry PE</th>
                  <th>Sector PE</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {rows.filter((r) => compare.includes(r.symbol)).map((r) => (
                  <tr key={r.symbol}>
                    <td>{r.symbol}</td>
                    <td>{fmt(r.pe)}</td>
                    <td>{fmt(r.pb)}</td>
                    <td>{fmt(r.ev_ebitda)}</td>
                    <td>{fmt(r.roe)}</td>
                    <td>{fmt(r.roce)}</td>
                    <td>{fmt(r.historical_percentile, 0)}</td>
                    <td>{r.premium_pct != null ? `${fmt(r.premium_pct, 1)}%` : '—'}</td>
                    <td>{fmt(r.industry_pe)}</td>
                    <td>{fmt(r.sector_pe)}</td>
                    <td>{r.valuation_status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}

      <div className="sve-two">
        <section className="sve-panel">
          <h3>Distributions</h3>
          <div className="sve-dist-grid">
            <DistBars dist={dists.pe} label="P/E" />
            <DistBars dist={dists.pb} label="P/B" />
            <DistBars dist={dists.historical_percentile} label="Historical %" />
            <DistBars dist={dists.premium_pct} label="Premium %" />
            <DistBars dist={dists.roe} label="ROE" />
          </div>
        </section>
        <section className="sve-panel">
          <div className="sve-panel-head">
            <h3>Workspace dashboards</h3>
            <div className="sve-quick">
              {['leaders', 'rotation', 'research'].map((t) => (
                <button key={t} type="button" className={dashTab === t ? 'on' : ''} onClick={() => setDashTab(t)}>
                  {t}
                </button>
              ))}
            </div>
          </div>
          {dashTab === 'leaders' ? (
            leaders?.leaders ? Object.entries(leaders.leaders).map(([key, list]) => (
              <div key={key} className="sve-leader-block">
                <div className="k">{key.replace(/_/g, ' ')}</div>
                <ul>
                  {(list || []).slice(0, 5).map((item) => (
                    <li key={`${key}-${item.symbol}`}>
                      <button type="button" className="sve-link" onClick={() => onSelectCompany(item.symbol, item.company_name)}>
                        {item.symbol}
                      </button>
                      <span>{fmt(item.value)}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )) : <p className="hint">No leaders yet.</p>
          ) : null}
          {dashTab === 'rotation' ? (
            <div className="sve-rotation">
              <p>{rotation?.rotation?.explanation || rotation?.note || 'Rotation context loading…'}</p>
              <ul>
                {(rotation?.rotation?.rows || rotation?.sectors || []).slice(0, 8).map((s) => (
                  <li key={s.sector}>
                    <strong>{s.sector}</strong>
                    <span> hist% {fmt(s.historical_percentile, 0)}</span>
                    <span> PE chg {s.avg_pe_change_pct != null ? `${fmt(s.avg_pe_change_pct, 1)}%` : '—'}</span>
                  </li>
                ))}
              </ul>
              <p className="hint">Capital rotation context for research priority — not a portfolio mandate.</p>
            </div>
          ) : null}
          {dashTab === 'research' ? (
            <ul className="sve-research">
              {(research?.priorities || []).map((p) => (
                <li key={p.symbol}>
                  <button type="button" className="sve-link" onClick={() => onSelectCompany(p.symbol, p.company_name)}>
                    <strong>{p.symbol}</strong>
                  </button>
                  <span>{p.reason}</span>
                  <span className="hint">→ {p.action}</span>
                </li>
              ))}
            </ul>
          ) : null}
        </section>
      </div>

      <section className="sve-panel">
        <h3>Research priorities</h3>
        <p className="hint">{research?.note}</p>
        <ul className="sve-research">
          {(research?.priorities || []).map((p) => (
            <li key={`rp-${p.symbol}`}>
              <button type="button" className="sve-link" onClick={() => onSelectCompany(p.symbol, p.company_name)}>
                <strong>{p.symbol}</strong>
              </button>
              <span>{p.reason}</span>
              <span className="hint">→ {p.action}</span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

export function SectorDirectory({ sectors, onSelect, loading }) {
  const [q, setQ] = useState('');
  const [sort, setSort] = useState('companies');

  const list = useMemo(() => {
    let rows = [...(sectors || [])];
    if (q.trim()) {
      const needle = q.trim().toLowerCase();
      rows = rows.filter((s) => String(s.sector || '').toLowerCase().includes(needle));
    }
    rows.sort((a, b) => {
      if (sort === 'name') return String(a.sector).localeCompare(String(b.sector));
      if (sort === 'pe') return (b.median_pe || b.current || 0) - (a.median_pe || a.current || 0);
      if (sort === 'pct') return (b.historical_percentile || 0) - (a.historical_percentile || 0);
      if (sort === 'premium') return (b.premium_pct || 0) - (a.premium_pct || 0);
      return (b.companies || 0) - (a.companies || 0);
    });
    return rows;
  }, [sectors, q, sort]);

  if (loading) return <section className="sve-directory hint">Loading sectors…</section>;
  return (
    <section className="sve-directory">
      <div className="sve-directory-head">
        <h3>All sectors</h3>
        <p className="hint">Start top-down: market → sector → industry → company → history → research</p>
      </div>
      <div className="sve-directory-tools">
        <input
          type="search"
          placeholder="Search sectors…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          aria-label="Search sectors"
        />
        <select value={sort} onChange={(e) => setSort(e.target.value)} aria-label="Sort sectors">
          <option value="companies">Companies</option>
          <option value="name">Name</option>
          <option value="pe">Median PE</option>
          <option value="pct">Historical %</option>
          <option value="premium">Premium</option>
        </select>
      </div>
      <div className="sve-cards">
        {list.map((s) => (
          <button
            key={s.sector}
            type="button"
            className={`sve-card band-${s.heatmap_band || 'grey'}`}
            onClick={() => onSelect(s.sector)}
          >
            <div className="sve-card-title">{s.sector}</div>
            <div className="sve-card-meta">{fmt(s.companies, 0)} companies</div>
            <div className="sve-card-row">
              <span>Median {s.primary_metric_label || 'P/E'}</span>
              <strong>{fmt(s.current)}</strong>
            </div>
            <div className="sve-card-row"><span>Median P/B</span><strong>{fmt(s.median_pb)}</strong></div>
            <div className="sve-card-row"><span>EV/EBITDA</span><strong>{fmt(s.median_ev_ebitda)}</strong></div>
            <div className="sve-card-row"><span>Historical %</span><strong>{fmt(s.historical_percentile, 0)}</strong></div>
            <div className="sve-card-row"><span>Premium</span><strong>{s.premium_pct != null ? `${fmt(s.premium_pct, 1)}%` : '—'}</strong></div>
            <div className="sve-card-row"><span>ROE</span><strong>{fmt(s.median_roe)}</strong></div>
            <div className="sve-card-row"><span>Coverage</span><strong>{s.coverage_pct != null ? `${fmt(s.coverage_pct, 0)}%` : '—'}</strong></div>
            <div className={`sve-pill ${String(s.status || s.opportunity || '').toLowerCase()}`}>
              {s.status || s.opportunity || 'Unknown'} · conf {fmt(s.confidence, 0)}%
            </div>
          </button>
        ))}
      </div>
    </section>
  );
}

export function ResearchBoards({ onSelectCompany }) {
  const [opps, setOpps] = useState(null);
  const [premium, setPremium] = useState(null);
  const [rerating, setRerating] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    Promise.all([
      getSveOpportunities({ limit: 10 }),
      getSvePremium({ limit: 10 }),
      getSveRerating({ limit: 15 }),
    ])
      .then(([o, p, r]) => {
        if (cancelled) return;
        setOpps(o);
        setPremium(p);
        setRerating(r);
      })
      .catch(() => {
        if (!cancelled) {
          setOpps(null);
          setPremium(null);
          setRerating(null);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, []);

  if (loading) return <section className="sve-boards hint">Loading opportunity / premium / re-rating boards…</section>;

  const boards = opps?.boards || {};
  const boardEntries = [
    ['Most Attractive', boards.most_attractive],
    ['Most Undervalued', boards.most_undervalued],
    ['Most Overvalued', boards.most_overvalued],
    ['Largest Discounts', boards.largest_discounts],
    ['Largest Premiums', boards.largest_premiums],
    ['Highest ROE', boards.highest_roe],
    ['Lowest Historical %', boards.lowest_historical_percentile],
  ];

  return (
    <section className="sve-boards">
      <div className="sve-directory-head">
        <h3>Opportunity, premium & re-rating</h3>
        <p className="hint">Warehouse-backed screens for research — not recommendations.</p>
      </div>
      <div className="sve-boards-grid">
        {boardEntries.map(([title, rows]) => (
          <div key={title} className="sve-panel sve-board-card">
            <h4>{title}</h4>
            <ul>
              {(rows || []).slice(0, 8).map((r) => (
                <li key={`${title}-${r.symbol}`}>
                  <button type="button" className="sve-link" onClick={() => onSelectCompany?.(r.symbol, r.company_name)}>
                    {r.symbol}
                  </button>
                  <span className="hint">{r.sector || r.why || r.valuation_status || ''}</span>
                </li>
              ))}
              {!rows?.length ? <li className="hint">No rows yet</li> : null}
            </ul>
          </div>
        ))}
        <div className="sve-panel sve-board-card">
          <h4>Premium dashboard</h4>
          <ul>
            {(premium?.rows || []).slice(0, 10).map((r) => (
              <li key={`prem-${r.symbol}`}>
                <button type="button" className="sve-link" onClick={() => onSelectCompany?.(r.symbol, r.company_name)}>
                  {r.symbol}
                </button>
                <span>
                  {r.premium_pct != null ? `${fmt(r.premium_pct, 1)}%` : '—'} · hist% {fmt(r.historical_percentile, 0)}
                </span>
                <span className="hint">{r.reason}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="sve-panel sve-board-card">
          <h4>Re-rating dashboard</h4>
          <ul>
            {(rerating?.rows || []).slice(0, 10).map((r) => (
              <li key={`re-${r.symbol}`}>
                <button type="button" className="sve-link" onClick={() => onSelectCompany?.(r.symbol, r.company_name)}>
                  {r.symbol}
                </button>
                <span>{r.transition}</span>
                <span className="hint">
                  {r.magnitude_pct != null ? `${fmt(r.magnitude_pct, 1)}%` : '—'} · {r.reason}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
