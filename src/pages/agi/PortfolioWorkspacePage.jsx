import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  createPortfolioOfficePortfolio,
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

export default function PortfolioWorkspacePage() {
  const [portfolioId, setPortfolioId] = useState('agi-desk-demo');
  const [holdings, setHoldings] = useState(DEMO_HOLDINGS);
  const [meta, setMeta] = useState({ name: 'AGI Desk Demo', health: 'Calm', coverage: '—' });
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
            weight: h.weight != null ? `${Math.round(Number(h.weight) * (Number(h.weight) <= 1 ? 100 : 1))}%` : h.weight_label || '—',
          }))
        );
        setMeta({
          name: pf?.metadata?.name || 'AGI Desk Demo',
          health: 'Calm',
          coverage: `${holds.length || DEMO_HOLDINGS.length} names`,
        });
      } catch (err) {
        if (active) setError(err?.message || 'Portfolio unavailable — showing desk demo');
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  return (
    <div>
      <h1 className="agi-greeting">Portfolio</h1>
      <p className="agi-lede">
        Think like a CIO — overall quality, exposure, research coverage, and ideas. Each holding opens Company
        Workspace.
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
          <div className="agi-stat-label">Business Quality</div>
          <div className="agi-stat-value">Mixed</div>
        </div>
        <div className="agi-stat">
          <div className="agi-stat-label">Concentration</div>
          <div className="agi-stat-value" style={{ fontSize: '1.15rem' }}>
            Banks-led
          </div>
        </div>
      </div>

      <div className="agi-grid-2" style={{ marginTop: '1.5rem' }}>
        <section className="agi-section">
          <div className="agi-section-head">
            <h2>Holdings</h2>
            <Link to={`/agi/ask?context=portfolio&portfolio=${encodeURIComponent(portfolioId)}&q=${encodeURIComponent('Which holding concerns you most?')}`}>
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
            <h2>Recent Changes</h2>
            <Link to="/agi/watchlists">Watchlist Candidates</Link>
          </div>
          <ul className="agi-list">
            <li>
              <div>
                <div className="agi-list-title">KOTAKBANK research refresh</div>
                <div className="agi-list-meta">Evidence update · Review recommended</div>
              </div>
            </li>
            <li>
              <div>
                <div className="agi-list-title">Banking concentration watch</div>
                <div className="agi-list-meta">Sector exposure elevated vs benchmark</div>
              </div>
            </li>
            <li>
              <Link to="/agi/watchlists">
                <div className="agi-list-title">Watchlist Candidates</div>
                <div className="agi-list-meta">Names queued for research coverage</div>
              </Link>
            </li>
          </ul>
          <div className="agi-panel" style={{ marginTop: '1rem' }}>
            <p className="agi-list-meta">
              Back navigation: open any holding, then return here via Portfolio in the product nav — context stays in
              AGI.
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
