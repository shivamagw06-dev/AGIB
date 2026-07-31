import { useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import AskAgiBar from '@/components/Home/AskAgiBar';
import NewsletterSection from '@/components/Home/NewsletterSection';
import usePublishedArticles from '@/hooks/usePublishedArticles';
import { formatTimeAgo } from '@/lib/articleUtils';

const ASK_SUGGESTIONS = [
  'Analyse Reliance Industries',
  'Why is Nifty falling today?',
  'Should I apply for this IPO?',
  "Explain today's RBI policy",
  'Compare HDFC Bank vs ICICI Bank',
];

const RESEARCH_CATEGORIES = [
  { label: 'Markets', to: '/market-intelligence' },
  { label: 'Macro', to: '/macro-intelligence' },
  { label: 'IPO', to: '/ipo-intelligence' },
  { label: 'Equities', to: '/research' },
  { label: 'Private Equity', to: '/private-equity' },
  { label: 'Global Markets', to: '/global-markets' },
  { label: 'Business', to: '/business' },
  { label: 'Technology', to: '/research?q=Technology' },
  { label: 'Energy', to: '/research?q=Energy' },
  { label: 'Healthcare', to: '/research?q=Healthcare' },
];

const DEFAULT_COVER =
  'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1400&q=80';

function articleHref(article) {
  return article?.href || (article?.slug ? `/article/${article.slug}` : '/research');
}

function articleCover(article) {
  return article?.coverUrl || article?.cover_url || article?.image || DEFAULT_COVER;
}

function articleAuthor(article) {
  return article?.author || article?.byline || 'AGI Research';
}

function isMorning(article) {
  const hay = `${article?.section || ''} ${article?.category || ''} ${article?.title || ''}`;
  return /morning|pre-?market|overnight|open/i.test(hay);
}

function isEvening(article) {
  const hay = `${article?.section || ''} ${article?.category || ''} ${article?.title || ''}`;
  return /evening|post\s*market|day\s*close|market\s*close|wrap/i.test(hay);
}

function ResearchCard({ article, featured = false, index = 0 }) {
  if (!article) return null;
  const href = articleHref(article);
  const cover = articleCover(article);
  const summary = article.excerpt || article.summary || 'Institutional research note from the AGI desk.';
  const category = article.section || article.category || 'Research';
  const published = article.publishedLabel
    ? formatTimeAgo(article.publishedLabel) || article.publishedLabel
    : article.date
      ? formatTimeAgo(article.date)
      : 'Recently';

  return (
    <article
      className={`group overflow-hidden rounded-xl border border-[#e6e8ec] bg-white transition-shadow hover:shadow-sm animate-home-rise ${
        featured ? 'md:col-span-2' : ''
      }`}
      style={{ animationDelay: `${Math.min(index, 8) * 40}ms` }}
    >
      <Link to={href} className="block">
        <div className={`overflow-hidden bg-[#f4f5f7] ${featured ? 'max-h-[340px]' : 'max-h-[200px]'}`}>
          <img
            src={cover}
            alt=""
            className="h-full w-full object-contain object-center transition-transform duration-500 group-hover:scale-[1.02]"
            loading={featured ? 'eager' : 'lazy'}
          />
        </div>
      </Link>
      <div className={`p-5 ${featured ? 'md:p-7' : ''}`}>
        <p className="text-[11px] font-bold uppercase tracking-[0.12em] text-[#5d6470]">{category}</p>
        <h3
          className={`mt-2 font-serif font-bold leading-snug text-[#111111] ${
            featured ? 'text-2xl md:text-[1.85rem]' : 'text-lg md:text-xl'
          }`}
        >
          <Link to={href} className="hover:underline underline-offset-4 decoration-[#111111]/30">
            {article.title}
          </Link>
        </h3>
        <p className={`mt-3 text-[#555555] leading-relaxed ${featured ? 'text-base line-clamp-3' : 'text-sm line-clamp-2'}`}>
          {summary}
        </p>
        <div className="mt-4 flex flex-wrap items-center gap-x-3 gap-y-1 text-[12px] text-[#767676]">
          <span className="font-medium text-[#333333]">{articleAuthor(article)}</span>
          <span aria-hidden>·</span>
          <span>{published}</span>
          <span aria-hidden>·</span>
          <span>{article.readTime || '5 min read'}</span>
        </div>
      </div>
    </article>
  );
}

function BriefCard({ title, description, href, cta }) {
  return (
    <Link
      to={href}
      className="group flex flex-col justify-between rounded-xl border border-[#e6e8ec] bg-white p-7 md:p-8 transition-shadow hover:shadow-sm"
    >
      <div>
        <p className="text-[11px] font-bold uppercase tracking-[0.14em] text-[#5d6470]">Daily Brief</p>
        <h3 className="mt-3 font-serif text-2xl font-bold text-[#111111]">{title}</h3>
        <p className="mt-3 text-sm leading-relaxed text-[#555555]">{description}</p>
      </div>
      <span className="mt-8 inline-flex text-sm font-semibold text-[#111111] group-hover:underline underline-offset-4">
        {cta}
      </span>
    </Link>
  );
}

export default function ResearchTerminalHome() {
  const navigate = useNavigate();
  const { articles, loading } = usePublishedArticles({ limit: 18, section: null });
  const [researchLane, setResearchLane] = useState('featured');

  const featured = articles[0] || null;
  const latest = articles.slice(1, 7);
  const trending = articles.slice(3, 9);

  const morningArticle = useMemo(() => articles.find(isMorning), [articles]);
  const eveningArticle = useMemo(() => articles.find(isEvening), [articles]);

  const laneArticles =
    researchLane === 'latest' ? latest : researchLane === 'trending' ? trending : [featured, ...latest.slice(0, 3)].filter(Boolean);

  return (
    <div className="home-terminal min-h-screen bg-white text-[#111111]">
      <Helmet>
        <title>AGI — Institutional Intelligence, Powered by AGI</title>
        <meta
          name="description"
          content="Research companies, markets, macroeconomics and investments using institutional-grade AI. Ask AGI and read the latest AGI research."
        />
      </Helmet>

      {/* Compact Ask box — directly under the sticky market strip */}
      <section id="agi-ask" className="border-b border-[#e8eaee] bg-[#fafbfc]" aria-label="Ask AGI">
        <div className="mx-auto max-w-[1200px] px-4 sm:px-6 py-4 md:py-5 home-hero-brand">
          <div className="rounded-xl border border-[#e2e5ea] bg-white px-4 py-3.5 sm:px-5 sm:py-4">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:gap-5">
              <div className="shrink-0 md:w-44">
                <p className="text-sm font-bold text-[#0b1f33]">Ask AGI</p>
                <p className="mt-0.5 text-xs text-[#767676]">Institutional research questions</p>
              </div>
              <div className="min-w-0 flex-1">
                <AskAgiBar
                  placeholder="Ask AGI anything..."
                  size="default"
                  autoFocus={false}
                  buttonLabel="Ask"
                  ariaLabel="Ask AGI"
                />
              </div>
              <Link
                to="/research"
                className="hidden shrink-0 text-xs font-semibold text-[#111111] underline-offset-4 hover:underline lg:inline"
              >
                Explore Research →
              </Link>
            </div>
            <div className="mt-3 flex flex-wrap gap-1.5">
              {ASK_SUGGESTIONS.map((q) => (
                <button
                  key={q}
                  type="button"
                  onClick={() => navigate(`/ask?q=${encodeURIComponent(q)}`)}
                  className="rounded-full border border-[#e6e8ec] bg-[#fafbfc] px-2.5 py-1 text-[11px] font-medium text-[#444444] transition-colors hover:border-[#111111] hover:text-[#111111]"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* RESEARCH CATEGORIES */}
      <section className="border-b border-[#e8eaee] bg-white" aria-label="Research categories">
        <div className="mx-auto max-w-[1200px] px-4 sm:px-6 py-8">
          <div className="flex flex-wrap justify-center gap-2">
            {RESEARCH_CATEGORIES.map((cat) => (
              <Link
                key={cat.label}
                to={cat.to}
                className="rounded-full border border-[#e2e5ea] bg-[#fafbfc] px-4 py-2 text-sm font-medium text-[#333333] transition-colors hover:border-[#111111] hover:bg-white hover:text-[#111111]"
              >
                {cat.label}
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* LATEST RESEARCH */}
      <section id="latest-research" className="border-b border-[#e8eaee] bg-white" aria-label="Latest research">
        <div className="mx-auto max-w-[1200px] px-4 sm:px-6 py-14 md:py-20">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <h2 className="font-serif text-3xl md:text-4xl font-bold text-[#111111]">Latest Research</h2>
              <p className="mt-2 text-sm text-[#555555]">Editorial research from the AGI desk.</p>
            </div>
            <Link to="/research" className="text-sm font-semibold text-[#111111] hover:underline underline-offset-4">
              View all research →
            </Link>
          </div>

          <div className="mt-8 flex flex-wrap gap-2 border-b border-[#e8eaee] pb-px">
            {[
              { id: 'featured', label: 'Featured Research' },
              { id: 'latest', label: 'Latest Research' },
              { id: 'trending', label: 'Trending' },
            ].map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setResearchLane(tab.id)}
                className={`-mb-px border-b-2 px-3 py-2.5 text-sm font-semibold transition-colors ${
                  researchLane === tab.id
                    ? 'border-[#111111] text-[#111111]'
                    : 'border-transparent text-[#767676] hover:text-[#111111]'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {loading ? (
            <div className="mt-10 grid grid-cols-1 gap-6 md:grid-cols-2">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-72 animate-pulse rounded-xl border border-[#e8eaee] bg-[#f7f8fa]" />
              ))}
            </div>
          ) : !laneArticles.length ? (
            <div className="mt-10 rounded-xl border border-[#e8eaee] px-6 py-16 text-center">
              <p className="font-serif text-xl font-bold text-[#111111]">Research notes are publishing soon</p>
              <p className="mt-2 text-sm text-[#555555]">Ask AGI while the desk prepares the next notes.</p>
              <Link to="/ask" className="mt-6 inline-flex text-sm font-semibold underline underline-offset-4">
                Ask AGI
              </Link>
            </div>
          ) : (
            <div className="mt-10 grid grid-cols-1 gap-6 md:grid-cols-2">
              {researchLane === 'featured' && featured ? (
                <>
                  <ResearchCard article={featured} featured index={0} />
                  {latest.slice(0, 2).map((article, i) => (
                    <ResearchCard key={article.id || article.slug || i} article={article} index={i + 1} />
                  ))}
                </>
              ) : (
                laneArticles.map((article, i) => (
                  <ResearchCard key={article.id || article.slug || i} article={article} index={i} />
                ))
              )}
            </div>
          )}
        </div>
      </section>

      {/* MORNING & EVENING BRIEF */}
      <section className="border-b border-[#e8eaee] bg-[#fafbfc]" aria-label="Morning and evening intelligence">
        <div className="mx-auto max-w-[1200px] px-4 sm:px-6 py-14 md:py-16">
          <h2 className="font-serif text-3xl font-bold text-[#111111]">Daily Intelligence</h2>
          <p className="mt-2 text-sm text-[#555555]">Overnight developments and market-close summaries.</p>
          <div className="mt-8 grid grid-cols-1 gap-5 md:grid-cols-2">
            <BriefCard
              title="Morning Intelligence"
              description={
                morningArticle?.excerpt ||
                morningArticle?.title ||
                'Latest overnight developments shaping the Indian and global open.'
              }
              href={morningArticle ? articleHref(morningArticle) : '/pre-market'}
              cta="Read morning brief →"
            />
            <BriefCard
              title="Evening Intelligence"
              description={
                eveningArticle?.excerpt ||
                eveningArticle?.title ||
                'Market close summary with the moves, catalysts and overnight watchlist.'
              }
              href={eveningArticle ? articleHref(eveningArticle) : '/research'}
              cta="Read evening brief →"
            />
          </div>
        </div>
      </section>

      {/* NEWSLETTER */}
      <NewsletterSection variant="minimal" />
    </div>
  );
}
