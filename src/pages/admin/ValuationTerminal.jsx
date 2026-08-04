import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, useLocation, useSearchParams } from 'react-router-dom';
import {
  ArrowLeft,
  RefreshCw,
  Star,
  Clock,
  Search,
  Info,
  X,
} from 'lucide-react';
import {
  Line,
  LineChart as RLineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import {
  getSveSectors,
  getVtCompany,
  getVtExplain,
  getVtHealth,
  getVtSeries,
  searchVtCompanies,
} from '@/lib/intelligenceApi';
import SectorValuationWorkspace, { SectorDirectory } from '@/pages/admin/SectorValuationWorkspace';
import './valuationIntelligence.css';
import './valuationTerminal.css';
import './sectorValuationExplorer.css';

const METRIC_LABELS = {
  pe: 'P/E',
  forward_pe: 'Fwd P/E',
  pb: 'P/B',
  ev_ebitda: 'EV/EBITDA',
  ev_sales: 'EV/Sales',
  ps: 'P/S',
  roe: 'ROE %',
  eps: 'EPS',
  dividend_yield: 'Div Yield %',
  market_cap: 'Market Cap',
  price: 'Price',
  revenue: 'Revenue',
};

const CHART_METRICS = ['price', 'pe', 'pb', 'ev_ebitda', 'revenue', 'eps', 'roe', 'dividend_yield'];
const WINDOWS = ['1Y', '3Y', '5Y', '10Y', 'MAX'];
const RECENT_KEY = 'agi.vt.recent';
const FAV_KEY = 'agi.vt.favorites';

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

function readList(key) {
  try {
    const raw = JSON.parse(localStorage.getItem(key) || '[]');
    return Array.isArray(raw) ? raw : [];
  } catch {
    return [];
  }
}

function writeList(key, items) {
  try {
    localStorage.setItem(key, JSON.stringify(items.slice(0, 12)));
  } catch {
    /* ignore */
  }
}

function positionClass(pos) {
  if (!pos) return '';
  if (pos === 'Premium' || pos === 'Above') return 'vt-pos-up';
  if (pos === 'Discount' || pos === 'Below') return 'vt-pos-down';
  return 'vt-pos-flat';
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

function CompanySearch({ onSelect, recent, favorites, onToggleFavorite }) {
  const [q, setQ] = useState('');
  const [items, setItems] = useState([]);
  const [open, setOpen] = useState(false);
  const boxRef = useRef(null);

  useEffect(() => {
    if (!q.trim()) {
      setItems([]);
      return undefined;
    }
    const t = setTimeout(() => {
      searchVtCompanies(q.trim(), 10)
        .then((r) => setItems(r?.suggestions || []))
        .catch(() => setItems([]));
    }, 180);
    return () => clearTimeout(t);
  }, [q]);

  useEffect(() => {
    const onDoc = (e) => {
      if (!boxRef.current?.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', onDoc);
    return () => document.removeEventListener('mousedown', onDoc);
  }, []);

  const pick = (symbol, name) => {
    onSelect(symbol, name);
    setQ('');
    setOpen(false);
  };

  return (
    <div className="vt-search" ref={boxRef}>
      <div className="vt-search-bar">
        <Search size={16} />
        <input
          value={q}
          placeholder="Search Axis Bank, ICICI Bank, Infosys, TCS…"
          onChange={(e) => { setQ(e.target.value); setOpen(true); }}
          onFocus={() => setOpen(true)}
        />
      </div>
      {open ? (
        <div className="vt-search-panel">
          {q.trim() && items.length ? (
            <ul>
              {items.map((s) => (
                <li key={s.symbol}>
                  <button type="button" onClick={() => pick(s.symbol, s.name)}>
                    <strong>{s.symbol}</strong>
                    <span>{s.name}</span>
                  </button>
                  <button
                    type="button"
                    className={`vt-fav ${favorites.some((f) => f.symbol === s.symbol) ? 'on' : ''}`}
                    onClick={() => onToggleFavorite(s.symbol, s.name)}
                    aria-label="Favorite"
                  >
                    <Star size={14} />
                  </button>
                </li>
              ))}
            </ul>
          ) : null}
          {!q.trim() && favorites.length ? (
            <div className="vt-search-block">
              <div className="k"><Star size={12} /> Favorites</div>
              <ul>
                {favorites.map((s) => (
                  <li key={s.symbol}>
                    <button type="button" onClick={() => pick(s.symbol, s.name)}>
                      <strong>{s.symbol}</strong>
                      <span>{s.name}</span>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
          {!q.trim() && recent.length ? (
            <div className="vt-search-block">
              <div className="k"><Clock size={12} /> Recent</div>
              <ul>
                {recent.map((s) => (
                  <li key={s.symbol}>
                    <button type="button" onClick={() => pick(s.symbol, s.name)}>
                      <strong>{s.symbol}</strong>
                      <span>{s.name}</span>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
          {q.trim() && !items.length ? (
            <p className="hint">No warehouse matches for “{q}”.</p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

function OverviewStrip({ overview, healthScore }) {
  if (!overview) return null;
  return (
    <section className="vt-overview-strip">
      <div className="vt-company-title">
        <h2>{overview.name || overview.symbol}</h2>
        <span className="vt-ticker">{overview.symbol}</span>
      </div>
      <div className="vt-ov-grid">
        <div><span className="k">CMP</span><span className="v">{fmt(overview.cmp)}</span></div>
        <div><span className="k">Market Cap</span><span className="v">{fmt(overview.market_cap)}</span></div>
        <div><span className="k">Sector</span><span className="v">{overview.sector || '—'}</span></div>
        <div><span className="k">Industry</span><span className="v">{overview.industry || '—'}</span></div>
        <div><span className="k">Historical Coverage</span><span className="v">{fmt(overview.historical_coverage, 0)}</span></div>
        <div><span className="k">Consensus</span><span className="v">{overview.consensus_coverage ? 'Available' : 'Missing'}</span></div>
        <div>
          <span className="k">Updated</span>
          <span className="v">
            {overview.updated ? new Date(overview.updated).toLocaleString() : '—'}
          </span>
        </div>
        <div>
          <span className="k">Data Quality</span>
          <span className={`v vt-band-${overview.data_quality || 'low'}`}>
            {overview.data_quality || '—'}
          </span>
        </div>
        <div className="vt-health-cell">
          <span className="k">{healthScore?.label || 'Valuation Confidence'}</span>
          <span className="v vt-health">{healthScore?.score != null ? `${healthScore.score}%` : '—'}</span>
        </div>
      </div>
    </section>
  );
}

function InstitutionalTable({ rows, onExplain }) {
  return (
    <section className="vt-panel">
      <div className="vt-panel-head">
        <h3>Institutional valuation</h3>
        <p className="hint">Company · Industry · Historical · Position · Source</p>
      </div>
      <div className="vi-table-wrap">
        <table className="vi-table vt-inst-table">
          <thead>
            <tr>
              <th>Metric</th>
              <th>Company</th>
              <th>Industry</th>
              <th>Historical</th>
              <th>Position</th>
              <th>Source</th>
            </tr>
          </thead>
          <tbody>
            {(rows || []).map((r) => (
              <tr key={r.metric} className={!r.meaningful ? 'vt-na-row' : ''}>
                <td>
                  <button type="button" className="vt-metric-btn" onClick={() => onExplain(r.metric)}>
                    {METRIC_LABELS[r.metric] || r.metric}
                    <Info size={11} />
                  </button>
                </td>
                <td>{!r.meaningful ? 'n/a' : fmt(r.company)}</td>
                <td>{!r.meaningful ? '—' : fmt(r.industry)}</td>
                <td>{!r.meaningful ? '—' : fmt(r.historical)}</td>
                <td className={positionClass(r.position)}>{r.position || (r.note ? '—' : '—')}</td>
                <td className="vt-source">{r.source || (r.available ? 'Engine' : '—')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function ChartPanel({ symbol, window, onWindow, coverage }) {
  const [metric, setMetric] = useState('pe');
  const [series, setSeries] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!symbol || !metric) return;
    setLoading(true);
    getVtSeries(symbol, metric, window)
      .then(setSeries)
      .catch(() => setSeries(null))
      .finally(() => setLoading(false));
  }, [symbol, metric, window]);

  const data = useMemo(
    () => (series?.points || []).map((p) => ({ period: p.period, value: p.value })),
    [series],
  );
  const cov = series?.coverage || coverage?.series?.[metric] || {};

  return (
    <section className="vt-panel">
      <div className="vt-panel-head">
        <h3>Historical charts</h3>
        <div className="vt-window-row">
          {WINDOWS.map((w) => (
            <button
              key={w}
              type="button"
              className={`vt-chip ${window === w ? 'on' : ''}`}
              onClick={() => onWindow(w)}
            >
              {w}
            </button>
          ))}
        </div>
      </div>
      <div className="vt-metric-row">
        {CHART_METRICS.map((m) => (
          <button
            key={m}
            type="button"
            className={`vt-chip ${metric === m ? 'on' : ''}`}
            onClick={() => setMetric(m)}
          >
            {METRIC_LABELS[m] || m}
          </button>
        ))}
      </div>
      <div className="vt-cov-line">
        Coverage {fmt(cov.history ?? cov.count, 0)}
        {' · '}History {cov.confidence || '—'}
        {' · '}Span {cov.observed_span != null ? `${cov.observed_span}y` : '—'}
        {cov.first && cov.last ? ` · ${cov.first} → ${cov.last}` : ''}
      </div>
      <div className="vt-chart">
        {loading ? (
          <p className="hint">Loading series…</p>
        ) : !data.length ? (
          <p className="hint">No history for {METRIC_LABELS[metric] || metric} in this window.</p>
        ) : (
          <ResponsiveContainer width="100%" height={260}>
            <RLineChart data={data}>
              <XAxis dataKey="period" hide />
              <YAxis width={48} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Line type="monotone" dataKey="value" stroke="#0f6e6a" strokeWidth={2} dot={false} />
            </RLineChart>
          </ResponsiveContainer>
        )}
      </div>
    </section>
  );
}

function SectorContext({ ctx }) {
  if (!ctx?.sector) return null;
  const dist = ctx.distribution || {};
  return (
    <section className="vt-panel">
      <div className="vt-panel-head">
        <h3>Sector context</h3>
        <p className="hint">{ctx.sector}</p>
      </div>
      <div className="vt-ov-grid vt-sector-grid">
        <div><span className="k">Current Median</span><span className="v">{fmt(ctx.current_median)}</span></div>
        <div><span className="k">Historical Median</span><span className="v">{fmt(ctx.historical_median)}</span></div>
        <div>
          <span className="k">Current Rank</span>
          <span className="v">
            {ctx.current_rank != null ? `${ctx.current_rank} / ${ctx.universe || '—'}` : '—'}
          </span>
        </div>
        <div>
          <span className="k">Distribution</span>
          <span className="v">
            {dist.low != null ? `${fmt(dist.low)} – ${fmt(dist.high)}` : '—'}
          </span>
        </div>
        <div><span className="k">Peer Percentile</span><span className="v">{fmt(ctx.peer_percentile, 1)}</span></div>
        <div><span className="k">Primary Metric</span><span className="v">{METRIC_LABELS[ctx.primary_metric] || ctx.primary_metric}</span></div>
      </div>
    </section>
  );
}

function PeerTable({ peers }) {
  const rows = peers?.rows || [];
  if (!rows.length) return null;
  return (
    <section className="vt-panel">
      <div className="vt-panel-head">
        <h3>Peer comparison</h3>
        <p className="hint">Current multiple · Historical · ROE · Consensus · Relative score</p>
      </div>
      <div className="vi-table-wrap">
        <table className="vi-table vt-peers">
          <thead>
            <tr>
              <th>Company</th>
              <th>P/E</th>
              <th>P/B</th>
              <th>Historical P/E</th>
              <th>ROE</th>
              <th>Consensus upside</th>
              <th>Relative score</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((p) => (
              <tr key={p.symbol} className={p.is_self ? 'vt-self' : ''}>
                <td>{p.company_name || p.symbol}</td>
                <td>{fmt(p.pe)}</td>
                <td>{fmt(p.pb)}</td>
                <td>{fmt(p.historical_pe)}</td>
                <td>{fmt(p.roe)}</td>
                <td>{fmt(p.consensus_upside)}</td>
                <td>{fmt(p.relative_score, 1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function Explanation({ explanation }) {
  if (!explanation?.sections?.length) return null;
  return (
    <section className="vt-panel vt-explain-panel">
      <div className="vt-panel-head"><h3>Valuation explanation</h3></div>
      <ol className="vt-explain-flow">
        {explanation.sections.map((s) => (
          <li key={s.title}>
            <strong>{s.title}</strong>
            <p>{s.text}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}

function ChangeLog({ log }) {
  if (!log) return null;
  const entries = log.entries || [];
  return (
    <section className="vt-panel">
      <div className="vt-panel-head">
        <h3>Valuation change log</h3>
        <p className="hint">
          {log.before_date || 'Prior'} → {log.after_date || 'Today'}
          {log.note ? ` · ${log.note}` : ''}
        </p>
      </div>
      {!entries.length ? (
        <p className="hint">No material multiple moves between the two observations.</p>
      ) : (
        <ul className="vt-changelog">
          {entries.map((e) => (
            <li key={e.metric}>
              <div className="vt-change-head">
                <strong>{METRIC_LABELS[e.metric] || e.metric}</strong>
                <span>{fmt(e.from)} → {fmt(e.to)}</span>
                <span className={e.change_pct < 0 ? 'vt-pos-down' : 'vt-pos-up'}>
                  {e.change_pct != null ? `${e.change_pct > 0 ? '+' : ''}${e.change_pct.toFixed(1)}%` : ''}
                </span>
              </div>
              <p>{e.summary}</p>
              {e.drivers?.length ? (
                <div className="vt-drivers">
                  {e.drivers.map((d) => (
                    <span key={d.input}>
                      {d.input.replace(/_/g, ' ')} {d.change_pct > 0 ? 'rose' : 'declined'} {Math.abs(d.change_pct).toFixed(1)}%
                    </span>
                  ))}
                  {(e.unchanged || []).map((u) => (
                    <span key={u} className="flat">{u.replace(/_/g, ' ')} unchanged</span>
                  ))}
                </div>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function ProvenancePanel({ provenance, version }) {
  if (!provenance) return null;
  const blocks = [
    ['Price', provenance.price],
    ['Statements', provenance.financials],
    ['Consensus', provenance.consensus],
  ];
  return (
    <section className="vt-panel">
      <div className="vt-panel-head"><h3>Provenance</h3></div>
      <div className="vt-prov-grid">
        {blocks.map(([label, block]) => (
          <div key={label}>
            <span className="k">{label}</span>
            <span className="v">{block?.source || '—'}</span>
            <span className="hint">
              {block?.updated_at ? new Date(block.updated_at).toLocaleString() : '—'}
              {block?.reported_unit ? ` · ${block.reported_unit}` : ''}
            </span>
          </div>
        ))}
        <div>
          <span className="k">Formula</span>
          <span className="v">{provenance.formula || 'unified_valuation_engine'}</span>
          <span className="hint">Version {provenance.formula_version || version || '3.0'}</span>
        </div>
      </div>
    </section>
  );
}

function DataQualityPanel({ dq, healthScore }) {
  if (!dq && !healthScore) return null;
  return (
    <section className="vt-panel">
      <div className="vt-panel-head">
        <h3>Data quality · Valuation confidence</h3>
      </div>
      <div className="vt-dq-grid">
        <div><span className="k">Validated</span><span className="v">{dq?.validated ? 'Yes' : 'No'}</span></div>
        <div><span className="k">Warnings</span><span className="v">{dq?.warnings?.length || 0}</span></div>
        <div><span className="k">Missing</span><span className="v">{(dq?.missing || []).join(', ') || 'None'}</span></div>
        <div><span className="k">Conflicts</span><span className="v">{dq?.conflicts ?? 0}</span></div>
        <div><span className="k">Overrides</span><span className="v">{dq?.overrides ?? 0}</span></div>
        <div><span className="k">Confidence</span><span className="v vt-health">{healthScore?.score != null ? `${healthScore.score}%` : '—'}</span></div>
      </div>
      {healthScore ? (
        <div className="vt-reasons">
          <ul className="ok">
            {(healthScore.reasons_ok || []).map((r) => <li key={r}>✓ {r}</li>)}
          </ul>
          <ul className="miss">
            {(healthScore.reasons_missing || []).map((r) => <li key={r}>Missing — {r}</li>)}
          </ul>
        </div>
      ) : null}
    </section>
  );
}

export default function ValuationTerminal() {
  const location = useLocation();
  const [params, setParams] = useSearchParams();
  const [symbol, setSymbol] = useState(params.get('symbol') || '');
  const [sector, setSector] = useState(params.get('sector') || '');
  const [window, setWindow] = useState('5Y');
  const [pack, setPack] = useState(null);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [metric, setMetric] = useState(null);
  const [recent, setRecent] = useState(() => readList(RECENT_KEY));
  const [favorites, setFavorites] = useState(() => readList(FAV_KEY));
  const [sectors, setSectors] = useState([]);
  const [sectorsLoading, setSectorsLoading] = useState(true);
  const [compare, setCompare] = useState([]);

  const home = location.pathname.startsWith('/admin') ? '/admin' : '/';

  const loadHealth = useCallback(() => {
    getVtHealth().then(setHealth).catch(() => setHealth(null));
  }, []);

  const selectSector = useCallback((name) => {
    setSector(name);
    setSymbol('');
    setPack(null);
    setCompare([]);
    setParams((prev) => {
      const next = new URLSearchParams(prev);
      next.delete('symbol');
      next.set('sector', name);
      return next;
    });
  }, [setParams]);

  const clearSector = useCallback(() => {
    setSector('');
    setParams((prev) => {
      const next = new URLSearchParams(prev);
      next.delete('sector');
      return next;
    });
  }, [setParams]);

  const selectCompany = useCallback((sym, name) => {
    const ticker = String(sym || '').toUpperCase();
    setSymbol(ticker);
    setParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set('symbol', ticker);
      // Keep sector context when drilling down from sector workspace.
      return next;
    });
    const entry = { symbol: ticker, name: name || ticker };
    setRecent((prev) => {
      const next = [entry, ...prev.filter((r) => r.symbol !== ticker)];
      writeList(RECENT_KEY, next);
      return next;
    });
  }, [setParams]);

  const toggleFavorite = useCallback((sym, name) => {
    const ticker = String(sym || '').toUpperCase();
    setFavorites((prev) => {
      const exists = prev.some((f) => f.symbol === ticker);
      const next = exists
        ? prev.filter((f) => f.symbol !== ticker)
        : [{ symbol: ticker, name: name || ticker }, ...prev];
      writeList(FAV_KEY, next);
      return next;
    });
  }, []);

  const loadPack = useCallback(async () => {
    if (!symbol) {
      setPack(null);
      return;
    }
    setLoading(true);
    setError('');
    try {
      const out = await getVtCompany(symbol, { window, peer_limit: 12 });
      setPack(out);
      if (!out?.ok) setError(out?.error || 'Company not in warehouse');
    } catch (err) {
      setError(err?.message || 'Failed to load valuation');
      setPack(null);
    } finally {
      setLoading(false);
    }
  }, [symbol, window]);

  useEffect(() => { loadHealth(); }, [loadHealth]);
  useEffect(() => { loadPack(); }, [loadPack]);
  useEffect(() => {
    setSectorsLoading(true);
    getSveSectors()
      .then((r) => setSectors(r?.sectors || []))
      .catch(() => setSectors([]))
      .finally(() => setSectorsLoading(false));
  }, []);

  useEffect(() => {
    const fromUrl = params.get('symbol');
    const sectorUrl = params.get('sector') || '';
    if (fromUrl && fromUrl.toUpperCase() !== symbol) setSymbol(fromUrl.toUpperCase());
    if (sectorUrl !== sector) setSector(sectorUrl);
  }, [params, symbol, sector]);

  const isFavorite = favorites.some((f) => f.symbol === symbol);
  const showSectorHome = !symbol && !sector;
  const showSectorWorkspace = !symbol && !!sector;

  return (
    <div className="vi-root vt-root">
      <header className="vi-header">
        <div className="vi-brand-row">
          <div className="vi-brand">
            <Link to={home} className="vt-back"><ArrowLeft size={14} /> Back</Link>
            <h1>Valuation Terminal</h1>
            <p>Market → Sector → Company → History · Warehouse → UVE / HVIE / VPAE</p>
          </div>
          <div className="vi-actions">
            <button type="button" className="vi-btn" onClick={() => { loadHealth(); loadPack(); getSveSectors().then((r) => setSectors(r?.sectors || [])); }} disabled={loading}>
              <RefreshCw size={14} /> Refresh
            </button>
            <div className="vi-updated">
              Engine {health?.version || pack?.version || '3.0'}
              <div style={{ color: 'var(--vi-ink)', fontWeight: 600 }}>
                {health?.companies != null ? `${health.companies} companies` : 'Warehouse'}
              </div>
            </div>
          </div>
        </div>
        <CompanySearch
          onSelect={selectCompany}
          recent={recent}
          favorites={favorites}
          onToggleFavorite={toggleFavorite}
        />
      </header>

      <main className="vi-body">
        {error ? <div className="vi-error">{error}</div> : null}

        {showSectorHome ? (
          <>
            <section className="vt-empty-state">
              <h2>Institutional Valuation Terminal</h2>
              <p>
                Search a company, or start from a sector below for top-down research.
                Multiples come from the Unified Valuation Engine and HVIE — never from the UI.
              </p>
              <div className="vt-quick">
                {['AXISBANK', 'ICICIBANK', 'INFY', 'TCS'].map((s) => (
                  <button key={s} type="button" className="vt-chip" onClick={() => selectCompany(s, s)}>
                    {s}
                  </button>
                ))}
              </div>
            </section>
            <SectorDirectory
              sectors={sectors}
              loading={sectorsLoading}
              onSelect={selectSector}
            />
          </>
        ) : null}

        {showSectorWorkspace ? (
          <SectorValuationWorkspace
            sector={sector}
            onBack={clearSector}
            onSelectCompany={selectCompany}
            compare={compare}
            onToggleCompare={(sym) => {
              setCompare((prev) => (
                prev.includes(sym) ? prev.filter((x) => x !== sym) : [...prev, sym].slice(0, 5)
              ));
            }}
          />
        ) : null}

        {symbol && sector ? (
          <div className="sve-context-bar">
            <button type="button" onClick={() => { setSymbol(''); setParams((p) => { const n = new URLSearchParams(p); n.delete('symbol'); return n; }); }}>
              ← Back to {sector}
            </button>
            <span className="hint">Company drill-down from sector workspace</span>
          </div>
        ) : null}

        {loading ? <p className="hint">Computing valuation from warehouse…</p> : null}

        {pack?.ok ? (
          <>
            <div className="vt-title-actions">
              <OverviewStrip overview={pack.overview} healthScore={pack.health_score} />
              <button
                type="button"
                className={`vt-fav-btn ${isFavorite ? 'on' : ''}`}
                onClick={() => toggleFavorite(symbol, pack.overview?.name)}
              >
                <Star size={14} /> {isFavorite ? 'Favorited' : 'Favorite'}
              </button>
            </div>

            <div className="vt-main-grid">
              <InstitutionalTable rows={pack.table} onExplain={setMetric} />
              <ChartPanel
                symbol={symbol}
                window={window}
                onWindow={setWindow}
                coverage={pack.charts}
              />
            </div>

            <div className="vt-main-grid">
              <SectorContext ctx={pack.sector_context} />
              <Explanation explanation={pack.explanation} />
            </div>

            <PeerTable peers={pack.peers} />
            <ChangeLog log={pack.change_log} />

            <div className="vt-main-grid">
              <ProvenancePanel provenance={pack.provenance} version={pack.version} />
              <DataQualityPanel dq={pack.data_quality} healthScore={pack.health_score} />
            </div>

            {pack.coverage ? (
              <p className="vt-cov-foot">
                Metric coverage {pack.coverage.pct}%
                ({pack.coverage.available}/{pack.coverage.applicable} applicable)
                · Engine {pack.engine} v{pack.version}
              </p>
            ) : null}
          </>
        ) : null}
      </main>

      <MetricModal metric={metric} onClose={() => setMetric(null)} />
    </div>
  );
}
