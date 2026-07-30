import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  createPortfolioOfficePortfolio,
  getPortfolioGraph,
  getPortfolioOfficeDashboard,
  getPortfolioOfficeHoldings,
  getPortfolioOfficePortfolio,
} from '@/lib/intelligenceApi';

const DEMO_HOLDINGS = [
  { ticker: 'KOTAKBANK', company: 'Kotak Mahindra Bank', sector: 'Banks', weight: '28%' },
  { ticker: 'HDFCBANK', company: 'HDFC Bank', sector: 'Banks', weight: '24%' },
  { ticker: 'TCS', company: 'Tata Consultancy Services', sector: 'IT', weight: '22%' },
  { ticker: 'RELIANCE', company: 'Reliance Industries', sector: 'Energy', weight: '26%' },
];

function formatPct(weight) {
  if (weight == null || Number.isNaN(Number(weight))) return '—';
  const n = Number(weight);
  if (n <= 1) return `${(n * 100).toFixed(0)}%`;
  return `${n.toFixed(0)}%`;
}

export default function PortfolioWorkspacePage() {
  const [portfolioId, setPortfolioId] = useState('agi-desk-demo');
  const [holdings, setHoldings] = useState(DEMO_HOLDINGS);
  const [meta, setMeta] = useState({ name: 'AGI Desk Demo', health: 'Calm', coverage: '—' });
  const [portfolioGraph, setPortfolioGraph] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const dash = await getPortfolioOfficeDashboard().catch(() => null);
        const listed = dash?.portfolios || [];
        let id = listed.find((p) => p.portfolio_id === 'agi-desk-demo')?.portfolio_id;
        if (!id) {
          const created = await createPortfolioOfficePortfolio({
            portfolio_id: 'agi-desk-demo',
            name: 'AGI Desk Demo',
            holdings: DEMO_HOLDINGS.map((h) => ({
              ticker: h.ticker,
              company: h.company,
              sector: h.sector,
              quantity: 100,
              average_cost: 1000,
            })),
          }).catch(() => null);
          id = created?.portfolio_id || created?.portfolio?.portfolio_id || 'agi-desk-demo';
        }
        if (!active) return;
        setPortfolioId(id);
        const pf = await getPortfolioOfficePortfolio(id).catch(() => null);
        const holds =
          (await getPortfolioOfficeHoldings(id).catch(() => null))?.holdings ||
          pf?.holdings ||
          DEMO_HOLDINGS;
        setHoldings(
          (holds.length ? holds : DEMO_HOLDINGS).map((h) => ({
            ticker: h.ticker,
            company: h.company || h.ticker,
            sector: h.sector || '—',
            weight:
              h.weight != null
                ? `${Math.round(Number(h.weight) * (Number(h.weight) <= 1 ? 100 : 1))}%`
                : h.weight_label || '—',
          }))
        );
        setMeta({
          name: pf?.metadata?.name || 'AGI Desk Demo',
          health: 'Calm',
          coverage: `${holds.length || DEMO_HOLDINGS.length} names`,
        });

        const graph = await getPortfolioGraph('agi-core-equity', {
          includeCompanyGraphs: true,
        }).catch(() => null);
        if (active) setPortfolioGraph(graph && graph.ok !== false ? graph : null);
      } catch (err) {
        if (active) setError(err?.message || 'Portfolio unavailable — showing desk demo');
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  const concentration = portfolioGraph?.concentration || {};
  const largest = concentration.largest_position || {};
  const sectorExposures = (portfolioGraph?.exposures || []).filter((e) => e.dimension === 'sector');
  const risks = portfolioGraph?.risks || [];

  return (
    <div>
      <h1 className="agi-greeting">Portfolio</h1>
      <p className="agi-lede">
        Think like a CIO — overall quality, exposure, research coverage, and the portfolio knowledge
        graph that connects holdings to company decisions.
      </p>

      {error && <div className="agi-error">{error}</div>}

      <div className="agi-stat-row">
        <div className="agi-stat">
          <div className="agi-stat-label">Portfolio Health</div>
          <div className="agi-stat-value">{meta.health}</div>
        </div>
        <div className="agi-stat">
          <div className="agi-stat-label">Research Coverage</div>
          <div className="agi-stat-value" style={{ fontSize: '1.15rem' }}>
            {meta.coverage}
          </div>
        </div>
        <div className="agi-stat">
          <div className="agi-stat-label">HHI</div>
          <div className="agi-stat-value" style={{ fontSize: '1.15rem' }}>
            {concentration.hhi != null ? Number(concentration.hhi).toFixed(2) : '—'}
          </div>
        </div>
        <div className="agi-stat">
          <div className="agi-stat-label">Avg correlation</div>
          <div className="agi-stat-value" style={{ fontSize: '1.15rem' }}>
            {portfolioGraph?.correlations?.average != null
              ? Number(portfolioGraph.correlations.average).toFixed(2)
              : '—'}
          </div>
        </div>
      </div>

      <div className="agi-grid-2" style={{ marginTop: '1.5rem' }}>
        <section className="agi-section">
          <div className="agi-section-head">
            <h2>Holdings</h2>
            <Link
              to={`/agi/ask?context=portfolio&portfolio=${encodeURIComponent(portfolioId)}&q=${encodeURIComponent('Which holding concerns you most?')}`}
            >
              Ask AGI
            </Link>
          </div>
          <ul className="agi-list">
            {holdings.map((h) => (
              <li key={h.ticker}>
                <Link to={`/agi/companies/${h.ticker}`}>
                  <div className="agi-list-title">
                    {h.ticker} · {h.company}
                  </div>
                  <div className="agi-list-meta">
                    {h.sector} · weight {h.weight}
                  </div>
                </Link>
                <span className="agi-chip">Workspace</span>
              </li>
            ))}
          </ul>
        </section>

        <section className="agi-section">
          <div className="agi-section-head">
            <h2>Portfolio Knowledge Graph</h2>
            <span className="agi-list-meta">PKG-01 · AGI Core Equity</span>
          </div>
          {!portfolioGraph ? (
            <div className="agi-empty">Portfolio graph unavailable.</div>
          ) : (
            <>
              <p className="agi-list-meta" style={{ marginBottom: '0.75rem' }}>
                {(portfolioGraph.lineage || []).join(' → ')}
              </p>
              <div className="agi-stat-row">
                <div className="agi-stat">
                  <div className="agi-stat-label">Entities</div>
                  <div className="agi-stat-value">{portfolioGraph.entity_count ?? 0}</div>
                </div>
                <div className="agi-stat">
                  <div className="agi-stat-label">Relationships</div>
                  <div className="agi-stat-value">{portfolioGraph.relationship_count ?? 0}</div>
                </div>
                <div className="agi-stat">
                  <div className="agi-stat-label">Largest</div>
                  <div className="agi-stat-value" style={{ fontSize: '1rem' }}>
                    {largest.ticker || '—'} {formatPct(largest.weight)}
                  </div>
                </div>
              </div>

              <h3 style={{ fontFamily: 'var(--agi-display)', fontSize: '1.1rem', marginTop: '1rem' }}>
                Graph holdings
              </h3>
              <ul className="agi-list" style={{ marginTop: '0.5rem' }}>
                {(portfolioGraph.holdings || []).map((h) => (
                  <li key={`pg-${h.ticker}`}>
                    <Link to={`/agi/companies/${h.ticker}`}>
                      <div className="agi-list-title">
                        {h.ticker} · {formatPct(h.weight)} · {h.recommendation || '—'}
                      </div>
                      <div className="agi-list-meta">
                        conf {h.confidence ?? '—'}
                        {h.company_graph_id ? ` · company graph linked` : ''}
                      </div>
                    </Link>
                  </li>
                ))}
              </ul>

              <h3 style={{ fontFamily: 'var(--agi-display)', fontSize: '1.1rem', marginTop: '1rem' }}>
                Sector exposure
              </h3>
              <ul className="agi-list" style={{ marginTop: '0.5rem' }}>
                {sectorExposures.map((e) => (
                  <li key={e.name}>
                    <div className="agi-list-title">
                      {e.name} <span className="agi-list-meta">{formatPct(e.weight)}</span>
                    </div>
                  </li>
                ))}
              </ul>

              <h3 style={{ fontFamily: 'var(--agi-display)', fontSize: '1.1rem', marginTop: '1rem' }}>
                Concentration risks
              </h3>
              <ul className="agi-list" style={{ marginTop: '0.5rem' }}>
                {risks.length ? (
                  risks.map((r) => (
                    <li key={`${r.kind}-${r.label}`}>
                      <div className="agi-list-title">
                        [{r.severity}] {r.label}
                      </div>
                      <div className="agi-list-meta">{r.detail}</div>
                    </li>
                  ))
                ) : (
                  <li>
                    <div className="agi-list-meta">No concentration risks above threshold.</div>
                  </li>
                )}
              </ul>
            </>
          )}
        </section>
      </div>
    </div>
  );
}
