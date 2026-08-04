import { useEffect, useMemo, useState } from 'react';
import {
  getSveSector,
  getSveSectorLeaders,
  getSveSectorResearch,
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
  if (s.includes('cheap') || s.includes('undervalued')) return 'sve-status-cheap';
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

const QUICK = [
  { id: 'cheap', label: 'Cheap', apply: (r) => String(r.valuation_status || '').toLowerCase().includes('cheap') || String(r.valuation_status || '').includes('Undervalued') },
  { id: 'premium', label: 'Premium', apply: (r) => String(r.valuation_status || '').toLowerCase().includes('premium') || String(r.valuation_status || '').includes('Expensive') },
  { id: 'roe', label: 'Highest ROE', sort: 'roe' },
  { id: 'roce', label: 'Highest ROCE', sort: 'roce' },
  { id: 'low_pct', label: 'Lowest Hist %', sort: 'historical_percentile', order: 'asc' },
  { id: 'high_pct', label: 'Highest Hist %', sort: 'historical_percentile' },
  { id: 'large', label: 'Large Cap', bucket: 'large' },
  { id: 'mid', label: 'Mid Cap', bucket: 'mid' },
  { id: 'small', label: 'Small Cap', bucket: 'small' },
];

export default function SectorValuationWorkspace({
  sector,
  onBack,
  onSelectCompany,
  compare = [],
  onToggleCompare,
}) {
  const [pack, setPack] = useState(null);
  const [leaders, setLeaders] = useState(null);
  const [research, setResearch] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [industry, setIndustry] = useState('');
  const [quick, setQuick] = useState(null);
  const [sort, setSort] = useState('market_cap');
  const [order, setOrder] = useState('desc');

  useEffect(() => {
    if (!sector) return undefined;
    let cancelled = false;
    setLoading(true);
    Promise.all([
      getSveSector(sector),
      getSveSectorLeaders(sector),
      getSveSectorResearch(sector),
    ])
      .then(([p, l, r]) => {
        if (cancelled) return;
        setPack(p);
        setLeaders(l);
        setResearch(r);
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

  if (loading) return <div className="sve-workspace hint">Loading sector workspace…</div>;
  if (error) return <div className="sve-workspace sve-error">{error}</div>;
  if (!pack?.ok) return <div className="sve-workspace hint">Sector unavailable.</div>;

  const summary = pack.summary || {};
  const explanation = pack.explanation || {};
  const outcome = pack.outcome || {};
  const dists = pack.distributions || {};

  return (
    <div className="sve-workspace">
      <div className="sve-workspace-head">
        <button type="button" className="sve-back" onClick={onBack}>← All sectors</button>
        <div>
          <h2>{pack.sector}</h2>
          <p className="hint">
            {fmt(pack.companies, 0)} companies · as of {pack.as_of || '—'} · warehouse → UVE / HVIE / VPAE
          </p>
        </div>
      </div>

      <section className="sve-dash">
        <div><span className="k">Current Median</span><span className="v">{fmt(summary.current_median)} <small>{summary.primary_metric_label}</small></span></div>
        <div><span className="k">Historical Median</span><span className="v">{fmt(summary.historical_median)}</span></div>
        <div><span className="k">Premium</span><span className="v">{summary.premium_pct != null ? `${fmt(summary.premium_pct, 1)}%` : '—'}</span></div>
        <div><span className="k">Historical %ile</span><span className="v">{fmt(summary.historical_percentile, 0)}</span></div>
        <div><span className="k">Market Cap</span><span className="v">{fmt(summary.market_cap)}</span></div>
        <div><span className="k">Coverage</span><span className="v">{summary.coverage_pct != null ? `${fmt(summary.coverage_pct, 0)}%` : '—'}</span></div>
        <div><span className="k">Overall</span><span className="v">{outcome.overall || summary.overall || '—'}</span></div>
        <div><span className="k">Confidence</span><span className="v">{outcome.confidence != null ? `${fmt(outcome.confidence, 0)}%` : '—'}</span></div>
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
          <h3>{outcome.title || 'Sector valuation conclusion'}</h3>
          <p className="sve-conclusion">{outcome.conclusion}</p>
          <ul>
            {(outcome.evidence || []).map((e, i) => <li key={i}>{e}</li>)}
          </ul>
          <div className="sve-outcome-foot">
            <span>Overall <strong>{outcome.overall}</strong></span>
            <span>Confidence <strong>{fmt(outcome.confidence, 0)}%</strong></span>
          </div>
          <p className="hint">Analysis and evidence only — not a recommendation.</p>
        </section>
      </div>

      <section className="sve-panel">
        <div className="sve-panel-head">
          <h3>Company valuation table</h3>
          <div className="sve-filters">
            <select value={industry} onChange={(e) => setIndustry(e.target.value)}>
              <option value="">All industries</option>
              {(pack.industries || []).map((ind) => (
                <option key={ind} value={ind}>{ind}</option>
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
                <th>Premium %</th>
                <th>Hist %</th>
                <th>P/B</th>
                <th>ROE</th>
                <th>ROCE</th>
                <th>EV/EBITDA</th>
                <th>Status</th>
                <th>Cov</th>
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
                  <td>{fmt(r.pe)}</td>
                  <td>{fmt(r.sector_pe)}</td>
                  <td>{r.premium_pct != null ? `${fmt(r.premium_pct, 1)}%` : '—'}</td>
                  <td>{fmt(r.historical_percentile, 0)}</td>
                  <td>{fmt(r.pb)}</td>
                  <td>{fmt(r.roe)}</td>
                  <td>{fmt(r.roce)}</td>
                  <td>{fmt(r.ev_ebitda)}</td>
                  <td><span className={`sve-status ${statusClass(r.valuation_status)}`}>{r.valuation_status}</span></td>
                  <td>{r.coverage?.provider || 0}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="hint">Showing {Math.min(rows.length, 250)} of {rows.length}. Values from warehouse via UVE / HVIE — no UI calculations.</p>
      </section>

      {compare.length >= 2 ? (
        <section className="sve-panel">
          <h3>Compare ({compare.length})</h3>
          <div className="vi-table-wrap">
            <table className="vi-table sve-table">
              <thead>
                <tr>
                  <th>Company</th>
                  <th>P/E</th>
                  <th>P/B</th>
                  <th>ROE</th>
                  <th>ROCE</th>
                  <th>EV/EBITDA</th>
                  <th>Hist %</th>
                  <th>Premium %</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {rows.filter((r) => compare.includes(r.symbol)).map((r) => (
                  <tr key={r.symbol}>
                    <td>{r.symbol}</td>
                    <td>{fmt(r.pe)}</td>
                    <td>{fmt(r.pb)}</td>
                    <td>{fmt(r.roe)}</td>
                    <td>{fmt(r.roce)}</td>
                    <td>{fmt(r.ev_ebitda)}</td>
                    <td>{fmt(r.historical_percentile, 0)}</td>
                    <td>{r.premium_pct != null ? `${fmt(r.premium_pct, 1)}%` : '—'}</td>
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
          <h3>Sector leaders</h3>
          {leaders?.leaders ? Object.entries(leaders.leaders).map(([key, list]) => (
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
          )) : <p className="hint">No leaders yet.</p>}
        </section>
      </div>

      <section className="sve-panel">
        <h3>Research priorities</h3>
        <p className="hint">{research?.note}</p>
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
      </section>
    </div>
  );
}

export function SectorDirectory({ sectors, onSelect, loading }) {
  if (loading) return <section className="sve-directory hint">Loading sectors…</section>;
  return (
    <section className="sve-directory">
      <div className="sve-directory-head">
        <h3>All sectors</h3>
        <p className="hint">Start top-down: sector → industry → company → history → research</p>
      </div>
      <div className="sve-cards">
        {(sectors || []).map((s) => (
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
            <div className="sve-card-row">
              <span>Median P/B</span>
              <strong>{fmt(s.median_pb)}</strong>
            </div>
            <div className="sve-card-row">
              <span>Historical %</span>
              <strong>{fmt(s.historical_percentile, 0)}</strong>
            </div>
            <div className={`sve-pill ${String(s.opportunity || '').toLowerCase()}`}>
              {s.opportunity || 'Unknown'}
            </div>
          </button>
        ))}
      </div>
    </section>
  );
}
