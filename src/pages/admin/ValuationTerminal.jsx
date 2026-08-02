import { Fragment, useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ArrowLeft, RefreshCw, Info, X } from 'lucide-react';
import {
  getVtCompanies,
  getVtCompany,
  getVtExplain,
  getVtHealth,
  getVtInsights,
  getVtOverview,
  getVtSectorIntelligence,
  getVtSectors,
} from '@/lib/intelligenceApi';
import './valuationIntelligence.css';
import './valuationTerminal.css';

const METRIC_LABELS = {
  pe: 'P/E',
  forward_pe: 'Fwd P/E',
  pb: 'P/B',
  ev_ebitda: 'EV/EBITDA',
  ev_sales: 'EV/Sales',
  ps: 'P/S',
  roe: 'ROE %',
  eps: 'EPS',
  book_value: 'Book Value',
  dividend_yield: 'Div Yield %',
  profit_margin: 'Margin %',
  debt_to_equity: 'D/E',
  market_cap: 'Market Cap',
  price: 'Price',
};

const TABLE_METRICS = ['pe', 'forward_pe', 'pb', 'ev_ebitda', 'roe', 'dividend_yield'];

function fmt(v, digits = 2) {
  if (v == null || v === '') return '—';
  if (typeof v === 'number') {
    if (Math.abs(v) >= 1e11) return `${(v / 1e10).toFixed(1)}k cr`;
    if (Math.abs(v) >= 1e7) return `${(v / 1e7).toFixed(0)} cr`;
    if (Math.abs(v) >= 1000) return v.toLocaleString(undefined, { maximumFractionDigits: 0 });
    return Number.isInteger(v) ? String(v) : v.toFixed(digits);
  }
  return String(v);
}

function Stat({ label, value, hint }) {
  return (
    <div className="vt-stat">
      <div className="label">{label}</div>
      <div className="value">{value}</div>
      {hint ? <div className="hint">{hint}</div> : null}
    </div>
  );
}

function MetricModal({ metric, onClose }) {
  const [body, setBody] = useState(null);
  useEffect(() => {
    if (!metric) return;
    getVtExplain(metric).then(setBody).catch(() => setBody(null));
  }, [metric]);
  if (!metric) return null;
  return (
    <div className="vi-modal-backdrop" onClick={onClose}>
      <div className="vi-modal" onClick={(e) => e.stopPropagation()}>
        <button type="button" className="vt-close" onClick={onClose} aria-label="Close">
          <X size={16} />
        </button>
        <h2>{body?.label || METRIC_LABELS[metric] || metric}</h2>
        {body?.ok ? (
          <div className="vt-explain">
            <p><strong>What it is.</strong> {body.what}</p>
            <p><strong>Why it matters.</strong> {body.why}</p>
            <p><strong>Where it applies.</strong> {body.where}</p>
            <p><strong>How to read it.</strong> {body.interpret}</p>
          </div>
        ) : (
          <p className="hint">No explanation available for this metric.</p>
        )}
      </div>
    </div>
  );
}

function SectorIntelligence({ sector, onClose }) {
  const [pack, setPack] = useState(null);
  useEffect(() => {
    if (!sector) return;
    setPack(null);
    getVtSectorIntelligence(sector).then(setPack).catch(() => setPack(null));
  }, [sector]);
  if (!sector) return null;
  return (
    <section className="vt-sector-intel">
      <div className="vt-intel-head">
        <div>
          <h2>{sector}</h2>
          <p className="hint">AGI Sector Intelligence — interpretation, not market data</p>
        </div>
        <button type="button" className="vi-btn" onClick={onClose}>Close</button>
      </div>
      {!pack ? (
        <p className="hint">Loading sector intelligence…</p>
      ) : !pack.ok ? (
        <p className="hint">No intelligence for this sector yet.</p>
      ) : (
        <>
          <p className="vt-dna">{pack.dna_note}</p>
          <div className="vt-lens">
            <div>
              <span className="k">Primary metric</span>
              <span className="v primary">{pack.primary_metric_label}</span>
            </div>
            <div>
              <span className="k">Supporting</span>
              <span className="v">{(pack.supporting_metrics || []).map((m) => m.label).join(' · ') || '—'}</span>
            </div>
            <div>
              <span className="k">Not used here</span>
              <span className="v avoid">{(pack.avoid_metrics || []).map((m) => m.label).join(' · ') || '—'}</span>
            </div>
          </div>
          <div className="vt-market-picture">
            {Object.entries(pack.market_picture || {})
              .filter(([, v]) => v != null)
              .map(([k, v]) => (
                <div key={k}>
                  <span className="k">{k.replace(/^median_/, 'Median ').replace(/_/g, ' ')}</span>
                  <span className="v">{fmt(v)}</span>
                </div>
              ))}
          </div>
          <ul className="vt-interpretation">
            {(pack.agi_interpretation || []).map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
          <p className="vt-bottom">{pack.bottom_line}</p>
        </>
      )}
    </section>
  );
}

function CompanyExpansion({ ticker }) {
  const [pack, setPack] = useState(null);
  useEffect(() => {
    setPack(null);
    getVtCompany(ticker).then(setPack).catch(() => setPack(null));
  }, [ticker]);
  if (!pack) return <div className="vt-expand hint">Loading…</div>;
  if (!pack.ok) return <div className="vt-expand hint">No valuation detail for {ticker}.</div>;
  const metrics = Object.entries(pack.market_metrics || {}).filter(([, v]) => v != null);
  const peers = pack.peers || {};
  return (
    <div className="vt-expand">
      <div className="vt-expand-grid">
        <div className="vt-panel">
          <h3>Market metrics · Yahoo Finance</h3>
          <div className="vt-kv">
            {metrics.map(([k, v]) => (
              <Fragment key={k}>
                <span className="k">{METRIC_LABELS[k] || k}</span>
                <span className="v">{fmt(v)}</span>
              </Fragment>
            ))}
          </div>
        </div>
        <div className="vt-panel">
          <h3>Consensus · Capital IQ</h3>
          <div className="vt-kv">
            {Object.entries(pack.consensus || {})
              .filter(([, v]) => v != null)
              .map(([k, v]) => (
                <Fragment key={k}>
                  <span className="k">{k.replace(/_/g, ' ')}</span>
                  <span className="v">{fmt(v)}</span>
                </Fragment>
              ))}
          </div>
        </div>
        <div className="vt-panel vt-agi">
          <h3>AGI valuation view</h3>
          <p>{pack.agi_valuation_summary}</p>
          <p className="hint">{pack.lens?.rationale}</p>
        </div>
      </div>
      {peers.peers?.length ? (
        <div className="vt-panel" style={{ marginTop: '0.75rem' }}>
          <h3>
            Peer comparison · {peers.industry} · {peers.primary_metric_label} median{' '}
            {fmt(peers.peer_median)}
          </h3>
          <table className="vt-peers">
            <thead>
              <tr>
                <th>Company</th>
                <th>{peers.primary_metric_label}</th>
                <th>ROE %</th>
                <th>Div %</th>
                <th>Upside %</th>
                <th>Analysts</th>
              </tr>
            </thead>
            <tbody>
              {peers.peers.map((p) => (
                <tr key={p.ticker}>
                  <td>{p.company_name || p.ticker}</td>
                  <td>{fmt(p[peers.primary_metric])}</td>
                  <td>{fmt(p.roe)}</td>
                  <td>{fmt(p.dividend_yield)}</td>
                  <td>{fmt(p.consensus_upside)}</td>
                  <td>{fmt(p.coverage, 0)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  );
}

export default function ValuationTerminal() {
  const location = useLocation();
  const [overview, setOverview] = useState(null);
  const [sectorCards, setSectorCards] = useState([]);
  const [insights, setInsights] = useState([]);
  const [health, setHealth] = useState(null);
  const [rows, setRows] = useState({ items: [], total: 0, pages: 0 });
  const [q, setQ] = useState('');
  const [sector, setSector] = useState('');
  const [sort, setSort] = useState('market_cap');
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState({ pe_max: '', pb_max: '', roe_min: '', dividend_yield_min: '' });
  const [expanded, setExpanded] = useState(null);
  const [openSector, setOpenSector] = useState(null);
  const [metric, setMetric] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadMeta = useCallback(async () => {
    try {
      const [o, s, i, h] = await Promise.all([
        getVtOverview(),
        getVtSectors(),
        getVtInsights(),
        getVtHealth(),
      ]);
      setOverview(o);
      setSectorCards(s?.sectors || []);
      setInsights(i?.insights || []);
      setHealth(h);
    } catch (err) {
      setError(err?.message || 'Failed to load valuation terminal');
    }
  }, []);

  const loadRows = useCallback(async () => {
    setLoading(true);
    try {
      const out = await getVtCompanies({ q, sector, sort, page, page_size: 50, ...filters });
      setRows(out || { items: [], total: 0 });
    } catch (err) {
      setError(err?.message || 'Failed to load companies');
    } finally {
      setLoading(false);
    }
  }, [q, sector, sort, page, filters]);

  useEffect(() => { loadMeta(); }, [loadMeta]);
  useEffect(() => { loadRows(); }, [loadRows]);

  const home = location.pathname.startsWith('/admin') ? '/admin' : '/';

  return (
    <div className="vi-root vt-root">
      <header className="vi-header">
        <div className="vi-brand-row">
          <div className="vi-brand">
            <Link to={home} className="vt-back"><ArrowLeft size={14} /> Back</Link>
            <h1>Valuation Intelligence</h1>
            <p>Institutional valuation terminal — Indian equities</p>
          </div>
          <div className="vi-actions">
            <button type="button" className="vi-btn" onClick={() => { loadMeta(); loadRows(); }}>
              <RefreshCw size={14} /> Refresh
            </button>
            <div className="vi-updated">
              {health?.companies ? `${health.companies} companies` : '—'}
              <div style={{ color: 'var(--vi-ink)', fontWeight: 600 }}>
                {health?.updated_at ? new Date(health.updated_at).toLocaleDateString() : '—'}
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="vi-body">
        {error ? <div className="vi-error">{error}</div> : null}

        <p className="vi-note">
          Market multiples come from Yahoo Finance and consensus from Capital IQ, reported as
          published. AGI supplies the interpretation — which metric governs each industry, how a
          company sits against its peers, and what would change the rating. No buy or sell calls.
        </p>

        <section className="vi-analytics vt-overview">
          <Stat label="Companies" value={fmt(overview?.companies_covered, 0)} />
          <Stat label="Median P/E" value={fmt(overview?.median_pe)} />
          <Stat label="Median P/B" value={fmt(overview?.median_pb)} />
          <Stat label="Median EV/EBITDA" value={fmt(overview?.median_ev_ebitda)} hint="excl. financials" />
          <Stat label="Median ROE" value={`${fmt(overview?.median_roe)}%`} />
          <Stat label="Median Div Yield" value={`${fmt(overview?.median_dividend_yield)}%`} />
          <Stat
            label="Cheapest sector"
            value={overview?.cheapest_sector?.sector || '—'}
            hint={overview?.cheapest_sector ? `${fmt(overview.cheapest_sector.median_pe)}× P/E` : ''}
          />
          <Stat
            label="Most expensive"
            value={overview?.most_expensive_sector?.sector || '—'}
            hint={overview?.most_expensive_sector ? `${fmt(overview.most_expensive_sector.median_pe)}× P/E` : ''}
          />
        </section>

        {insights.length ? (
          <section className="vt-insights">
            <h2>Institutional insights</h2>
            <ul>{insights.map((line) => <li key={line}>{line}</li>)}</ul>
          </section>
        ) : null}

        <section className="vt-sectors">
          {sectorCards.map((c) => (
            <button
              type="button"
              key={c.sector}
              className={`vt-sector-card ${sector === c.sector ? 'active' : ''}`}
              onClick={() => { setPage(1); setSector((s) => (s === c.sector ? '' : c.sector)); setOpenSector(c.sector); }}
            >
              <div className="name">{c.sector}</div>
              <div className="count">{c.companies} companies · {c.primary_metric_label} led</div>
              <div className="metrics">
                <span>P/E {fmt(c.median_pe)}</span>
                <span>P/B {fmt(c.median_pb)}</span>
                {c.ev_ebitda_meaningful ? <span>EV/E {fmt(c.median_ev_ebitda)}</span> : null}
                <span>ROE {fmt(c.median_roe)}%</span>
              </div>
            </button>
          ))}
        </section>

        {openSector ? <SectorIntelligence sector={openSector} onClose={() => setOpenSector(null)} /> : null}

        <div className="vi-filters vt-filters">
          <div className="vi-field">
            <label>Search</label>
            <input value={q} placeholder="Company, ticker, industry…" onChange={(e) => { setPage(1); setQ(e.target.value); }} />
          </div>
          <div className="vi-field">
            <label>Sector</label>
            <select value={sector} onChange={(e) => { setPage(1); setSector(e.target.value); }}>
              <option value="">All</option>
              {sectorCards.map((c) => <option key={c.sector} value={c.sector}>{c.sector}</option>)}
            </select>
          </div>
          {[
            ['pe_max', 'Max P/E'],
            ['pb_max', 'Max P/B'],
            ['roe_min', 'Min ROE %'],
            ['dividend_yield_min', 'Min Div %'],
          ].map(([key, label]) => (
            <div className="vi-field" key={key}>
              <label>{label}</label>
              <input
                value={filters[key]}
                onChange={(e) => { setPage(1); setFilters((f) => ({ ...f, [key]: e.target.value })); }}
              />
            </div>
          ))}
        </div>

        <div className="vi-table-wrap">
          <table className="vi-table vt-table">
            <thead>
              <tr>
                <th className="pin" onClick={() => setSort('ticker')}>Ticker</th>
                <th className="pin company" onClick={() => setSort('company')}>Company</th>
                <th>Industry</th>
                <th onClick={() => setSort('price')}>Price</th>
                <th onClick={() => setSort('market_cap')}>Market Cap</th>
                {TABLE_METRICS.map((m) => (
                  <th key={m} onClick={() => setSort(m)}>
                    {METRIC_LABELS[m]}
                    <button
                      type="button"
                      className="vt-info"
                      onClick={(e) => { e.stopPropagation(); setMetric(m); }}
                      aria-label={`Explain ${METRIC_LABELS[m]}`}
                    >
                      <Info size={11} />
                    </button>
                  </th>
                ))}
                <th>Upside %</th>
                <th>Analysts</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={13} className="vt-empty">Loading valuation data…</td></tr>
              ) : !rows.items?.length ? (
                <tr><td colSpan={13} className="vt-empty">No companies match these filters.</td></tr>
              ) : (
                rows.items.map((r) => (
                  <Fragment key={r.ticker}>
                    <tr
                      className={expanded === r.ticker ? 'open' : ''}
                      onClick={() => setExpanded((t) => (t === r.ticker ? null : r.ticker))}
                    >
                      <td className="pin"><strong>{r.ticker}</strong></td>
                      <td className="pin company">{r.company_name}</td>
                      <td>{r.primary_industry || '—'}</td>
                      <td>{fmt(r.price)}</td>
                      <td>{fmt(r.market_cap)}</td>
                      {TABLE_METRICS.map((m) => (
                        <td key={m} className={r[m] == null ? 'vt-na' : ''}>
                          {r[m] == null && !r.visible_metrics?.includes(m) ? (
                            <span title={`${METRIC_LABELS[m]} is not used for ${r.primary_industry}`}>n/a</span>
                          ) : (
                            fmt(r[m])
                          )}
                        </td>
                      ))}
                      <td>{fmt(r.consensus?.upside)}</td>
                      <td>{fmt(r.consensus?.coverage, 0)}</td>
                    </tr>
                    {expanded === r.ticker ? (
                      <tr><td colSpan={13} style={{ padding: 0 }}><CompanyExpansion ticker={r.ticker} /></td></tr>
                    ) : null}
                  </Fragment>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="vi-pager">
          <span>{fmt(rows.total, 0)} companies · page {rows.page || page} / {rows.pages || 1}</span>
          <div className="vi-actions">
            <button type="button" className="vi-btn" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>Prev</button>
            <button type="button" className="vi-btn" disabled={page >= (rows.pages || 1)} onClick={() => setPage((p) => p + 1)}>Next</button>
          </div>
        </div>
      </main>

      <MetricModal metric={metric} onClose={() => setMetric(null)} />
    </div>
  );
}
