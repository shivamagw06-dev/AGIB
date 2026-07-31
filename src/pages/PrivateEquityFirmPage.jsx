import { useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, Download } from 'lucide-react';
import PeTerminalLayout from '@/components/private-equity/PeTerminalLayout';
import { PeFirmAnalytics } from '@/components/private-equity/PeDashboard';
import { usePeFirm } from '@/hooks/usePeIntelligence';
import '@/components/private-equity/peTerminal.css';

const TABS = [
  'Overview', 'Portfolio', 'Criteria', 'Transactions', 'Funds', 'Team', 'News', 'Case Studies', 'ESG', 'Analytics', 'AI Insights',
];

function exportCsv(rows) {
  if (!rows.length) return;
  const headers = ['Company', 'Industry', 'Country', 'Region', 'Investment Year', 'Status', 'Asset Class', 'Website'];
  const lines = [headers.join(',')];
  rows.forEach((r) => {
    lines.push([
      r.company, r.industry, r.country, r.region, r.investmentYear, r.status, r.assetClass, r.website,
    ].map((v) => `"${String(v || '').replace(/"/g, '""')}"`).join(','));
  });
  const blob = new Blob([lines.join('\n')], { type: 'text/csv' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'portfolio.csv';
  a.click();
}

export default function PrivateEquityFirmPage() {
  const { slug } = useParams();
  const { data, loading, error } = usePeFirm(slug);
  const [tab, setTab] = useState('Overview');
  const [search, setSearch] = useState('');
  const [sortKey, setSortKey] = useState('company');
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const filteredPortfolio = useMemo(() => {
    let rows = data?.portfolio || [];
    if (search) {
      const q = search.toLowerCase();
      rows = rows.filter((r) =>
        [r.company, r.industry, r.country, r.region].some((f) => String(f).toLowerCase().includes(q))
      );
    }
    rows = [...rows].sort((a, b) => String(a[sortKey] || '').localeCompare(String(b[sortKey] || '')));
    return rows;
  }, [data, search, sortKey]);

  const paged = filteredPortfolio.slice((page - 1) * pageSize, page * pageSize);
  const totalPages = Math.ceil(filteredPortfolio.length / pageSize) || 1;

  if (loading) {
    return (
      <PeTerminalLayout title="Loading…">
        <div className="pe-loading">Loading firm intelligence…</div>
      </PeTerminalLayout>
    );
  }

  if (error || !data) {
    return (
      <PeTerminalLayout title="Not Found">
        <div className="pe-firm-page">
          <Link to="/private-equity" className="inline-flex items-center gap-2 text-sm pe-gold no-underline mb-6">
            <ArrowLeft size={16} /> Back to PE Intelligence
          </Link>
          <p>Firm not found.</p>
        </div>
      </PeTerminalLayout>
    );
  }

  return (
    <PeTerminalLayout title={data.name}>
      <div className="pe-firm-page">
        <Link to="/private-equity" className="inline-flex items-center gap-2 text-sm text-[var(--pe-text-muted)] no-underline mb-6 hover:text-white">
          <ArrowLeft size={16} /> PE Intelligence
        </Link>

        <section className="pe-glass p-6 md:p-8">
          <div className="flex flex-wrap items-start gap-6">
            <img src={data.logo} alt="" className="w-16 h-16 rounded-2xl bg-white/5 p-2" />
            <div className="flex-1 min-w-0">
              <p className="pe-eyebrow">{data.hq} · Founded {data.founded}</p>
              <h1 className="pe-title text-3xl mt-1">{data.name}</h1>
              <p className="text-[var(--pe-text-muted)] text-sm mt-2 max-w-2xl">{data.strategy}</p>
              {data.dataSource === 'live_crawler' && (
                <span className="pe-badge mt-3 inline-block">Live crawler data</span>
              )}
            </div>
            <div className="text-right">
              <div className="pe-kpi-value pe-gold">{data.aum}</div>
              <div className="pe-kpi-label">Assets Under Management</div>
            </div>
          </div>
          <div className="pe-hero-stats">
            {[
              { l: 'Portfolio Companies', v: data.portfolioTotal },
              { l: 'Funds', v: data.fundCount },
              { l: 'Exits', v: data.exitCount },
              { l: 'Offices', v: data.offices },
              { l: 'Focus', v: data.geoFocus?.[0] },
            ].map((s) => (
              <div key={s.l} className="pe-glass p-3 text-center">
                <div className="font-bold">{s.v}</div>
                <div className="text-[10px] text-[var(--pe-text-muted)] uppercase mt-1">{s.l}</div>
              </div>
            ))}
          </div>
        </section>

        <div className="pe-tabs">
          {TABS.map((t) => (
            <button key={t} type="button" className={`pe-tab ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
              {t}
            </button>
          ))}
        </div>

        {tab === 'Overview' && (
          <div className="pe-glass p-6 space-y-4 text-sm leading-relaxed">
            <p>{data.overview.history}</p>
            <p><strong className="pe-gold">Philosophy:</strong> {data.overview.philosophy}</p>
            <p><strong className="pe-gold">Positioning:</strong> {data.overview.positioning}</p>
            <p><strong className="pe-gold">Operating model:</strong> {data.overview.operatingModel}</p>
            <div className="flex flex-wrap gap-2 mt-4">
              {data.industries.map((i) => <span key={i} className="pe-badge">{i}</span>)}
            </div>
          </div>
        )}

        {tab === 'Portfolio' && (
          <div>
            <div className="flex flex-wrap gap-3 items-center mb-4">
              <input
                type="search"
                placeholder="Search portfolio…"
                className="pe-search"
                value={search}
                onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              />
              <select
                className="pe-search max-w-[160px]"
                value={sortKey}
                onChange={(e) => setSortKey(e.target.value)}
              >
                <option value="company">Sort: Company</option>
                <option value="industry">Sort: Industry</option>
                <option value="investmentYear">Sort: Year</option>
                <option value="region">Sort: Region</option>
              </select>
              <button type="button" className="pe-tab flex items-center gap-2" onClick={() => exportCsv(filteredPortfolio)}>
                <Download size={14} /> Export CSV
              </button>
            </div>
            <div className="pe-table-wrap pe-glass">
              <table className="pe-table">
                <thead>
                  <tr>
                    <th>Company</th>
                    <th>Industry</th>
                    <th>Country</th>
                    <th>Region</th>
                    <th>Year</th>
                    <th>Status</th>
                    <th>Asset Class</th>
                  </tr>
                </thead>
                <tbody>
                  {paged.map((r) => (
                    <tr key={`${r.company}-${r.investmentYear}`}>
                      <td className="font-medium">{r.company}</td>
                      <td>{r.industry}</td>
                      <td>{r.country}</td>
                      <td>{r.region}</td>
                      <td>{r.investmentYear}</td>
                      <td><span className="pe-badge">{r.status}</span></td>
                      <td>{r.assetClass}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="flex justify-between items-center mt-4 text-sm">
              <span className="text-[var(--pe-text-muted)]">{filteredPortfolio.length} companies</span>
              <div className="flex gap-2">
                <button type="button" className="pe-tab" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>Prev</button>
                <span className="py-2 px-3">{page} / {totalPages}</span>
                <button type="button" className="pe-tab" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>Next</button>
              </div>
            </div>
          </div>
        )}

        {tab === 'Criteria' && data.investmentCriteria && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {Object.entries(data.investmentCriteria).map(([k, v]) => (
              <div key={k} className="pe-glass p-4">
                <div className="text-xs uppercase text-[var(--pe-text-muted)]">{k.replace(/([A-Z])/g, ' $1')}</div>
                <div className="mt-1 font-medium">{Array.isArray(v) ? v.join(', ') : v}</div>
              </div>
            ))}
          </div>
        )}

        {tab === 'Transactions' && (
          <div className="pe-table-wrap pe-glass">
            <table className="pe-table">
              <thead>
                <tr><th>Buyer</th><th>Target</th><th>Value</th><th>Industry</th><th>Date</th><th>Status</th></tr>
              </thead>
              <tbody>
                {(data.transactions?.length ? data.transactions : [{ buyer: data.name, target: '—', dealValue: '—', industry: '—', date: '—', status: '—' }]).map((t) => (
                  <tr key={t.id || t.target}>
                    <td>{t.buyer}</td>
                    <td>{t.target}</td>
                    <td className="pe-gold">{t.dealValue}</td>
                    <td>{t.industry}</td>
                    <td>{t.date}</td>
                    <td><span className="pe-badge">{t.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {tab === 'Funds' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {(data.funds?.length ? data.funds : [{ id: 'x', name: `${data.name} Flagship`, vintage: '—', fundSize: '—', strategy: data.strategy.slice(0, 40), status: 'Investing', geography: data.geoFocus?.[0] }]).map((f) => (
              <div key={f.id} className="pe-glass p-4">
                <div className="font-semibold">{f.name}</div>
                <div className="text-xs text-[var(--pe-text-muted)] mt-2 grid grid-cols-2 gap-1">
                  <span>Vintage {f.vintage}</span><span className="pe-gold">{f.fundSize}</span>
                  <span>{f.strategy}</span><span>{f.status}</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {tab === 'Team' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {data.team.map((m) => (
              <div key={m.name} className="pe-glass p-4">
                <div className="font-semibold">{m.name}</div>
                <div className="text-sm pe-gold">{m.title}</div>
                <div className="text-xs text-[var(--pe-text-muted)] mt-2">{m.office} · {m.bio}</div>
              </div>
            ))}
          </div>
        )}

        {tab === 'News' && (
          <div className="space-y-3">
            {(data.news?.length ? data.news : []).map((n) => (
              <div key={n.id} className="pe-glass p-4">
                <span className="pe-badge">{n.category}</span>
                <h4 className="font-semibold mt-2">{n.headline}</h4>
                <p className="text-sm text-[var(--pe-text-muted)] mt-1">{n.summary}</p>
              </div>
            ))}
            {!data.news?.length && <p className="text-[var(--pe-text-muted)]">No firm-specific news in feed yet.</p>}
          </div>
        )}

        {tab === 'Case Studies' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {(data.caseStudies?.length ? data.caseStudies : [{ id: 'd', title: 'Value creation playbook', thesis: data.strategy, valueCreation: 'Operational improvements across portfolio.' }]).map((c) => (
              <div key={c.id} className="pe-glass p-4">
                <h4 className="font-semibold">{c.title}</h4>
                <p className="text-xs mt-2 text-[var(--pe-text-muted)]">{c.thesis}</p>
              </div>
            ))}
          </div>
        )}

        {tab === 'ESG' && data.esg && (
          <div className="pe-glass p-6 space-y-3 text-sm">
            <p>{data.esg.framework}</p>
            <p><strong className="pe-gold">Goals:</strong> {data.esg.goals}</p>
            <ul className="list-disc pl-5 text-[var(--pe-text-muted)]">
              {data.esg.initiatives.map((i) => <li key={i}>{i}</li>)}
            </ul>
          </div>
        )}

        {tab === 'Analytics' && <PeFirmAnalytics analytics={data.analytics} />}

        {tab === 'AI Insights' && (
          <div className="pe-glass p-4">
            {Object.values(data.aiInsights || {}).map((item) => (
              <div key={item.label} className="pe-insight-row">
                <div>
                  <div className="text-xs text-[var(--pe-text-muted)]">{item.label}</div>
                  <div className="font-medium">{item.value}</div>
                  <div className="text-xs text-[var(--pe-text-muted)]">{item.detail}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </PeTerminalLayout>
  );
}
