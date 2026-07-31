import { Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { useEffect, useMemo, useState } from 'react';
import usePublishedArticles from '@/hooks/usePublishedArticles';
import { usePeOverview } from '@/hooks/usePeIntelligence';
import NewsletterSection from '@/components/Home/NewsletterSection';
import AskAgiBar from '@/components/Home/AskAgiBar';
import { formatTimeAgo } from '@/lib/articleUtils';
import { fetchPipelineStatus } from '@/lib/intelligencePlatformApi';
import {
  articleMatchesDesk,
  getSectionsForDesk,
} from '@/lib/deskSections';
import '@/components/private-equity/editorial/peEditorial.css';

const DEFAULT_COVER =
  'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1200&q=80';

const BRIEF_TOPICS = [
  { label: 'Acquisitions', tag: 'Acquisition' },
  { label: 'Fundraising', tag: 'Fundraise' },
  { label: 'Private Markets', tag: 'Private Markets' },
  { label: 'Exits', tag: 'Exit' },
  { label: 'Valuation', tag: 'Valuation' },
  { label: 'IPO', tag: 'IPO' },
  { label: 'Infrastructure', tag: 'Infrastructure' },
  { label: 'Healthcare', tag: 'Healthcare' },
  { label: 'Technology', tag: 'Technology' },
];

const INDUSTRIES = [
  { name: 'Healthcare', path: '/sectors/healthcare' },
  { name: 'Technology', path: '/sectors/it-software' },
  { name: 'Consumer', path: '/sectors/fmcg' },
  { name: 'Financial Services', path: '/sectors/banks' },
  { name: 'Infrastructure', path: '/sectors/infrastructure' },
  { name: 'Industrials', path: '/sectors/industrials' },
  { name: 'Energy', path: '/sectors/oil-gas' },
  { name: 'Business Services', path: '/research' },
  { name: 'Real Estate', path: '/research' },
];

const VALUATION_PLACEHOLDER = [
  {
    company: 'Enterprise SaaS Platform',
    sector: 'Technology',
    evRev: '8.2x',
    evEbitda: '22.4x',
    growth: '14%',
    geography: 'US / Global',
    comment: 'Selective on rule-of-40 leaders',
    view: 'Selective',
  },
  {
    company: 'Regional Healthcare Services',
    sector: 'Healthcare',
    evRev: '4.1x',
    evEbitda: '16.8x',
    growth: '11%',
    geography: 'India',
    comment: 'Consolidation theme intact',
    view: 'Constructive',
  },
  {
    company: 'Industrial Components Group',
    sector: 'Industrials',
    evRev: '2.8x',
    evEbitda: '12.1x',
    growth: '8%',
    geography: 'India / Export',
    comment: 'Prefer export-oriented niches',
    view: 'Core',
  },
];

function dealComment(data = {}) {
  return (
    data.comment ||
    data.commentary ||
    data.agi_rating ||
    data.view ||
    '—'
  );
}

/** Premium recent-deals / valuation strip for the Private Markets hero. */
function HeroDealsTable() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    import('@/lib/intelligenceCmsApi')
      .then(({ fetchPublicCmsModule }) => fetchPublicCmsModule('valuation_monitor'))
      .then((res) => setRows((res.records || []).slice(0, 6)))
      .catch(() => setRows([]))
      .finally(() => setLoading(false));
  }, []);

  const displayRows = rows.length
    ? rows
    : VALUATION_PLACEHOLDER.map((r, i) => ({
        id: `ph-${i}`,
        data: {
          company: r.company,
          sector: r.sector,
          ev_revenue: r.evRev,
          ev_ebitda: r.evEbitda,
          growth: r.growth,
          geography: r.geography,
          commentary: r.comment,
          agi_rating: r.view,
        },
      }));

  return (
    <aside className="pe-hero-deals" aria-label="Recent private market deals">
      <div className="pe-hero-deals-head">
        <div>
          <p className="pe-kicker">Recent deals</p>
          <h2>Valuation &amp; deal multiples</h2>
        </div>
        <Link to="#valuation-monitor" className="text-[13px] font-semibold text-[var(--pe-accent)] no-underline hover:underline">
          Full monitor →
        </Link>
      </div>
      {loading ? (
        <div className="h-40 animate-pulse rounded bg-[#eee]" />
      ) : (
        <div className="pe-hero-deals-scroll">
          <table className="pe-table-editorial pe-hero-deals-table">
            <thead>
              <tr>
                <th>Company</th>
                <th>Sector</th>
                <th>EV / Revenue</th>
                <th>EV / EBITDA</th>
                <th>Growth</th>
                <th>Geography</th>
                <th>Comment</th>
              </tr>
            </thead>
            <tbody>
              {displayRows.map((row) => (
                <tr key={row.id}>
                  <td className="font-medium">{row.data.company}</td>
                  <td>{row.data.sector || '—'}</td>
                  <td>{row.data.ev_revenue || '—'}</td>
                  <td>{row.data.ev_ebitda || '—'}</td>
                  <td>{row.data.growth || '—'}</td>
                  <td>{row.data.geography || '—'}</td>
                  <td className="pe-hero-deals-comment">{dealComment(row.data)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </aside>
  );
}

function SectionHead({ kicker, title, href, linkLabel = 'View all →' }) {
  return (
    <div className="pe-section-head">
      <div>
        {kicker && <span className="pe-kicker">{kicker}</span>}
        <h2>{title}</h2>
      </div>
      {href && <Link to={href}>{linkLabel}</Link>}
    </div>
  );
}

function EditorsDesk({ article, loading }) {
  const fallback = {
    title: 'What institutional investors should watch today',
    body: 'Every market session begins with an editor\'s note synthesizing the most important developments across private equity, capital markets, fundraising, valuation trends, and macro events. Rather than listing headlines, we explain why today\'s developments matter and what deserves attention next. Publish daily notes from the admin CMS under section "Editor\'s Desk".',
  };

  const title = article?.title || fallback.title;
  const body = article?.excerpt || article?.summary || fallback.body;
  const href = article?.slug ? `/article/${article.slug}` : null;

  return (
    <section className="pe-card pe-editors-desk pe-block" aria-labelledby="editors-desk-heading">
      <p className="pe-editors-desk-label" id="editors-desk-heading">Editor&apos;s Desk</p>
      {loading ? (
        <div className="h-24 bg-[#eee] animate-pulse mt-4" />
      ) : (
        <>
          <h3>{title}</h3>
          <p className="pe-editors-desk-body">{body}</p>
          {href && (
            <Link to={href} className="pe-btn">Read the editor&apos;s note</Link>
          )}
        </>
      )}
    </section>
  );
}

function FeaturedResearch({ featured, top10, loading }) {
  const lead = featured || top10[0];
  const cover = lead?.coverUrl || lead?.cover_url || DEFAULT_COVER;

  return (
    <section className="pe-block">
      <SectionHead kicker="Research" title="Featured Research" href="/research" />
      <div className="pe-feature-grid">
        {loading ? (
          <div className="pe-card h-96 animate-pulse bg-[#eee]" />
        ) : lead ? (
          <article className="pe-card pe-featured">
            <Link to={`/article/${lead.slug}`} className="pe-featured-media min-w-0">
              <img src={cover} alt="" className="pe-featured-img" loading="eager" />
            </Link>
            <div className="pe-featured-body min-w-0">
              <span className="pe-tag">{lead.section || 'Research'}</span>
              <h3 className="font-serif text-2xl font-semibold mt-3 leading-snug">
                <Link to={`/article/${lead.slug}`} className="text-inherit no-underline hover:text-[var(--pe-accent)]">
                  {lead.title}
                </Link>
              </h3>
              <p className="text-[var(--pe-muted)] text-[17px] leading-relaxed mt-3 line-clamp-4">
                {lead.excerpt || lead.summary}
              </p>
              <p className="pe-meta">
                {lead.author || 'AGI Research'} · {formatTimeAgo(lead.date || lead.published_at)} · 8 min read
              </p>
              <Link to={`/article/${lead.slug}`} className="pe-btn">Read article</Link>
            </div>
          </article>
        ) : (
          <div className="pe-card p-8 text-[var(--pe-muted)]">
            No Private Markets research yet. In Admin → Articles, set Research Desk to
            “Private Markets” and publish.
          </div>
        )}

        <aside className="pe-card pe-top10-box">
          <h3>Private Markets Top Research</h3>
          {(top10.length ? top10 : []).slice(0, 10).map((a) => (
            <Link key={a.slug} to={`/article/${a.slug}`} className="pe-top10-item">
              <img
                src={a.coverUrl || a.cover_url || DEFAULT_COVER}
                alt=""
                className="pe-top10-thumb"
              />
              <div className="min-w-0">
                <h4 className="text-sm font-semibold leading-snug line-clamp-2">{a.title}</h4>
                <p className="pe-meta">{a.section || 'Research'} · {formatTimeAgo(a.date || a.published_at)}</p>
              </div>
            </Link>
          ))}
          {!top10.length && !loading && (
            <p className="text-sm text-[var(--pe-muted)]">
              Publish Private Markets desk articles to fill this list.
            </p>
          )}
        </aside>
      </div>
    </section>
  );
}

function DailyBrief({ feed }) {
  const items = feed?.length ? feed : [];
  return (
    <section className="pe-block">
      <SectionHead kicker="Markets" title="Daily Private Market Brief" href="/sections/deal-tracker" linkLabel="Deal tracker →" />
      <div className="pe-brief-grid">
        {BRIEF_TOPICS.map((topic) => {
          const match = items.find((f) => f.dealType === topic.tag || f.category?.includes(topic.label));
          return (
            <Link
              key={topic.label}
              to={match?.firmSlug ? `/private-markets/firms/${match.firmSlug}` : '/sections/deal-tracker'}
              className="pe-card pe-brief-card"
            >
              <span className="pe-tag">{topic.label}</span>
              <h4>{match?.headline || `${topic.label} intelligence — updated daily`}</h4>
              <p className="text-xs text-[var(--pe-muted)] mt-2 line-clamp-2">
                {match?.summary || 'Structured data and editorial coverage across India and global private markets.'}
              </p>
            </Link>
          );
        })}
      </div>
    </section>
  );
}

function ValuationMonitor() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    import('@/lib/intelligenceCmsApi')
      .then(({ fetchPublicCmsModule }) => fetchPublicCmsModule('valuation_monitor'))
      .then((res) => setRows(res.records || []))
      .catch(() => setRows([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <section className="pe-block">
      <SectionHead
        kicker="Valuation"
        title="Private Market Valuation Monitor"
      />
      <p className="text-[var(--pe-muted)] text-sm mb-4 max-w-2xl">
        Updated daily by AGI Research. Administer via{' '}
        <Link to="/admin/intelligence/valuation-monitor" className="text-[var(--pe-accent)]">
          Intelligence CMS
        </Link>
        .
      </p>
      {loading ? (
        <div className="pe-card h-32 animate-pulse bg-[#eee]" />
      ) : (
        <div className="pe-card overflow-hidden">
          <table className="pe-table-editorial">
            <thead>
              <tr>
                <th>Company</th>
                <th>Sector</th>
                <th>EV / Revenue</th>
                <th>EV / EBITDA</th>
                <th>Growth</th>
                <th>Geography</th>
                <th>AGI Rating</th>
                <th>Analyst</th>
              </tr>
            </thead>
            <tbody>
              {(rows.length ? rows : VALUATION_PLACEHOLDER.map((r, i) => ({
                id: `ph-${i}`,
                data: {
                  company: r.company,
                  sector: r.sector,
                  ev_revenue: r.evRev,
                  ev_ebitda: r.evEbitda,
                  growth: r.growth,
                  geography: r.geography,
                  agi_rating: r.view,
                  analyst: 'AGI Research',
                  commentary: r.comment,
                },
              }))).map((row) => (
                <tr key={row.id}>
                  <td className="font-medium">{row.data.company}</td>
                  <td>{row.data.sector}</td>
                  <td>{row.data.ev_revenue}</td>
                  <td>{row.data.ev_ebitda}</td>
                  <td>{row.data.growth}</td>
                  <td>{row.data.geography}</td>
                  <td className="text-[var(--pe-accent)] font-medium">{row.data.agi_rating}</td>
                  <td>{row.data.analyst}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function RecentTransactions() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    import('@/lib/intelligenceCmsApi')
      .then(({ fetchPublicCmsModule }) => fetchPublicCmsModule('transactions'))
      .then((res) => setRows(res.records || []))
      .catch(() => setRows([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <section className="pe-block" id="recent-transactions">
      <SectionHead title="Recent Transactions" href="/sections/deal-tracker" linkLabel="Full database →" />
      <p className="text-[var(--pe-muted)] text-sm mb-4 max-w-2xl">
        Updated manually by AGI Research. Administer via{' '}
        <Link to="/admin/intelligence/transactions" className="text-[var(--pe-accent)]">
          Intelligence CMS
        </Link>
        .
      </p>
      {loading ? (
        <div className="pe-card h-32 animate-pulse bg-[#eee]" />
      ) : (
        <div className="pe-card overflow-x-auto">
          <table className="pe-table-editorial">
            <thead>
              <tr>
                <th>Date</th>
                <th>Target</th>
                <th>Buyer</th>
                <th>EV</th>
                <th>Sector</th>
                <th>Country</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.length ? rows.map((row) => (
                <tr key={row.id}>
                  <td>{row.data.date}</td>
                  <td className="font-medium">{row.data.target}</td>
                  <td>{row.data.buyer}</td>
                  <td>{row.data.enterprise_value || row.data.deal_value}</td>
                  <td>{row.data.industry}</td>
                  <td>{row.data.country}</td>
                  <td><span className="pe-tag">{row.data.status}</span></td>
                </tr>
              )) : (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-[var(--pe-muted)]">
                    No transactions published yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function IndustryIntelligence() {
  return (
    <section className="pe-block">
      <SectionHead title="Industry Intelligence" href="/sectors/it-software" linkLabel="All sectors →" />
      <div className="pe-industry-grid">
        {INDUSTRIES.map((ind) => (
          <Link key={ind.name} to={ind.path} className="pe-card pe-industry-card">
            {ind.name}
          </Link>
        ))}
      </div>
    </section>
  );
}

function FundraisingSection({ funds }) {
  return (
    <section className="pe-block">
      <SectionHead title="Fundraising Intelligence" />
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {(funds || []).map((f) => (
          <div key={f.id} className="pe-card p-5">
            <span className="pe-tag">{f.status}</span>
            <h4 className="font-serif text-lg font-semibold mt-2">{f.name}</h4>
            <p className="text-sm text-[var(--pe-muted)] mt-2">
              {f.gp} · Vintage {f.vintage} · {f.fundSize}
            </p>
            <p className="text-sm mt-2">{f.strategy}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function TopPeFirms({ firms }) {
  return (
    <section className="pe-block">
      <SectionHead title="Top Global Private Markets Firms" />
      <div className="pe-card">
        {(firms || []).map((f, i) => (
          <Link key={f.slug} to={`/private-markets/firms/${f.slug}`} className="pe-firm-row">
            <span className="pe-firm-rank">{i + 1}</span>
            <img src={f.logo} alt="" className="w-9 h-9 rounded object-contain bg-[#f5f5f5] p-1" />
            <div className="flex-1 min-w-0">
              <div className="font-semibold text-sm">{f.name}</div>
              <div className="text-xs text-[var(--pe-muted)]">{f.hq}</div>
            </div>
            <div className="text-sm font-semibold text-[var(--pe-accent)]">{f.aum}</div>
          </Link>
        ))}
      </div>
    </section>
  );
}

export default function PeEditorialHome() {
  const privateSections = useMemo(() => getSectionsForDesk('private-markets'), []);
  const { articles: editorsDeskArticles, loading: deskLoading } = usePublishedArticles({
    limit: 1,
    section: "Editor's Desk",
  });
  const { articles: fetchedResearch, loading: researchLoading } = usePublishedArticles({
    limit: 24,
    sections: privateSections,
  });
  const research = useMemo(
    () => fetchedResearch.filter((article) => articleMatchesDesk(article, 'private-markets')),
    [fetchedResearch]
  );
  const { data: peData, loading: peLoading } = usePeOverview();

  const editorsDesk = editorsDeskArticles[0];
  const featured = research[0];
  const top10 = research.slice(0, 10);

  return (
    <div className="pe-editorial">
      <Helmet>
        <title>Private Markets Intelligence | Agarwal Global Investments</title>
        <meta
          name="description"
          content="Institutional intelligence combining editorial research, structured private market data, and AI-driven knowledge for PE, M&A, fundraising, and valuation."
        />
      </Helmet>

      <div className="pe-editorial-inner">
        <header className="pe-hero">
          <div className="pe-hero-grid">
            <div className="pe-hero-copy min-w-0">
              <p className="pe-tag">Institutional Intelligence</p>
              <h1>Private market intelligence for institutional investors.</h1>
              <p className="pe-hero-lead">
                Editorial research, structured data, and AI-driven knowledge — covering private equity,
                M&A, valuation, fundraising, and investment opportunities across India and global markets.
              </p>
              <div className="mt-8 max-w-2xl">
                <AskAgiBar
                  placeholder="Search companies, deals, PE firms, industries, valuation themes…"
                  size="large"
                  buttonLabel="Ask AGI"
                  ariaLabel="Ask AGI about private markets"
                />
              </div>
              <nav className="flex flex-wrap gap-4 mt-6 text-sm font-semibold">
                {[
                  { label: 'Latest Research', to: '#pe-research' },
                  { label: 'Transactions', to: '#recent-transactions' },
                  { label: 'Valuation Monitor', to: '#valuation-monitor' },
                  { label: 'Industries', to: '#industries' },
                  { label: 'Fundraising', to: '#fundraising' },
                ].map((l) => (
                  <Link key={l.label} to={l.to} className="text-[var(--pe-accent)] no-underline hover:underline">
                    {l.label}
                  </Link>
                ))}
              </nav>
            </div>
            <HeroDealsTable />
          </div>
        </header>

        <EditorsDesk article={editorsDesk} loading={deskLoading} />
        <div id="pe-research">
          <FeaturedResearch featured={featured} top10={top10} loading={researchLoading} />
        </div>
        <DailyBrief feed={peData?.feed} />
        <div id="valuation-monitor"><ValuationMonitor /></div>
        <RecentTransactions />
        <div id="industries"><IndustryIntelligence /></div>
        <div id="fundraising"><FundraisingSection funds={peData?.funds} /></div>
        {!peLoading && <TopPeFirms firms={peData?.firms} />}
      </div>

      <NewsletterSection variant="minimal" initialSelected="agi_macro" />
    </div>
  );
}
