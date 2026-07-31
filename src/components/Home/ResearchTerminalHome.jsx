import { useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import {
  BookOpen,
  Building2,
  Briefcase,
  Globe2,
  Landmark,
  LineChart,
} from 'lucide-react';
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

const DESK_BUTTONS = [
  { label: 'Articles', to: '/research', icon: BookOpen, hint: 'Research notes' },
  { label: 'Indian Market', to: '/market-intelligence', icon: LineChart, hint: 'India desk' },
  { label: 'Global Markets', to: '/global-markets', icon: Globe2, hint: 'World markets' },
  { label: 'Private Markets', to: '/private-markets', icon: Briefcase, hint: 'Deals & exits' },
  { label: 'Hedge Funds', to: '/hedge-fund', icon: Building2, hint: 'Strategies' },
  { label: 'Economics', to: '/economics', icon: Landmark, hint: 'Macro & policy' },
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

function articleMeta(article) {
  const published = article?.publishedLabel
    ? formatTimeAgo(article.publishedLabel) || article.publishedLabel
    : article?.date
      ? formatTimeAgo(article.date)
      : 'Recently';
  return {
    category: article?.section || article?.category || 'Research',
    summary: article?.excerpt || article?.summary || 'Institutional research note from the AGI desk.',
    author: articleAuthor(article),
    published,
    readTime: article?.readTime || '5 min read',
  };
}

function isMorning(article) {
  const hay = `${article?.section || ''} ${article?.category || ''} ${article?.title || ''}`;
  return /morning|pre-?market|overnight|open/i.test(hay);
}

function isEvening(article) {
  const hay = `${article?.section || ''} ${article?.category || ''} ${article?.title || ''}`;
  return /evening|post\s*market|day\s*close|market\s*close|wrap/i.test(hay);
}

/** Featured story — image + copy in one balanced row on desktop. */
function FeaturedArticle({ article }) {
  if (!article) return null;
  const href = articleHref(article);
  const cover = articleCover(article);
  const meta = articleMeta(article);

  return (
    <article className="group grid h-full overflow-hidden rounded-xl border border-[#e4e7ec] bg-white lg:grid-cols-[1.15fr_1fr] animate-home-rise">
      <Link to={href} className="relative block min-h-[240px] bg-[#f3f4f6] lg:min-h-full">
        <img
          src={cover}
          alt=""
          className="absolute inset-0 h-full w-full object-cover transition-transform duration-500 group-hover:scale-[1.02]"
          loading="eager"
        />
      </Link>
      <div className="flex flex-col justify-center p-6 md:p-8">
        <p className="text-[11px] font-bold uppercase tracking-[0.14em] text-[#6b7280]">{meta.category}</p>
        <h3 className="mt-3 font-serif text-2xl md:text-[1.75rem] font-bold leading-snug text-[#111111]">
          <Link to={href} className="hover:underline underline-offset-4 decoration-[#111]/25">
            {article.title}
          </Link>
        </h3>
        <p className="mt-3 text-sm md:text-[15px] leading-relaxed text-[#555555] line-clamp-4">{meta.summary}</p>
        <div className="mt-5 flex flex-wrap items-center gap-x-3 gap-y-1 text-[12px] text-[#767676]">
          <span className="font-medium text-[#333]">{meta.author}</span>
          <span aria-hidden>·</span>
          <span>{meta.published}</span>
          <span aria-hidden>·</span>
          <span>{meta.readTime}</span>
        </div>
        <Link
          to={href}
          className="mt-6 inline-flex w-fit text-sm font-semibold text-[#0b1f33] underline-offset-4 hover:underline"
        >
          Read research →
        </Link>
      </div>
    </article>
  );
}

/** Compact stacked row used beside the featured story. */
function StackArticle({ article, index = 0 }) {
  if (!article) return null;
  const href = articleHref(article);
  const cover = articleCover(article);
  const meta = articleMeta(article);

  return (
    <article
      className="group flex gap-4 border-b border-[#eceef2] py-4 first:pt-0 last:border-b-0 last:pb-0 animate-home-rise"
      style={{ animationDelay: `${Math.min(index, 6) * 40}ms` }}
    >
      <Link to={href} className="relative h-[88px] w-[118px] shrink-0 overflow-hidden rounded-lg bg-[#f3f4f6]">
        <img
          src={cover}
          alt=""
          className="absolute inset-0 h-full w-full object-cover transition-transform duration-500 group-hover:scale-[1.03]"
          loading="lazy"
        />
      </Link>
      <div className="min-w-0 flex-1 py-0.5">
        <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-[#6b7280]">{meta.category}</p>
        <h3 className="mt-1 font-serif text-[1.05rem] font-bold leading-snug text-[#111111] line-clamp-2">
          <Link to={href} className="hover:underline underline-offset-4 decoration-[#111]/25">
            {article.title}
          </Link>
        </h3>
        <div className="mt-2 flex flex-wrap items-center gap-x-2 text-[11px] text-[#767676]">
          <span>{meta.published}</span>
          <span aria-hidden>·</span>
          <span>{meta.readTime}</span>
        </div>
      </div>
    </article>
  );
}

/** Equal grid card for the lower research shelf. */
function GridArticle({ article, index = 0 }) {
  if (!article) return null;
  const href = articleHref(article);
  const cover = articleCover(article);
  const meta = articleMeta(article);

  return (
    <article
      className="group flex h-full flex-col overflow-hidden rounded-xl border border-[#e4e7ec] bg-white transition-shadow hover:shadow-sm animate-home-rise"
      style={{ animationDelay: `${Math.min(index, 8) * 35}ms` }}
    >
      <Link to={href} className="relative block aspect-[16/10] overflow-hidden bg-[#f3f4f6]">
        <img
          src={cover}
          alt=""
          className="absolute inset-0 h-full w-full object-cover transition-transform duration-500 group-hover:scale-[1.03]"
          loading="lazy"
        />
      </Link>
      <div className="flex flex-1 flex-col p-5">
        <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-[#6b7280]">{meta.category}</p>
        <h3 className="mt-2 font-serif text-lg font-bold leading-snug text-[#111111] line-clamp-2">
          <Link to={href} className="hover:underline underline-offset-4 decoration-[#111]/25">
            {article.title}
          </Link>
        </h3>
        <p className="mt-2 flex-1 text-sm leading-relaxed text-[#555555] line-clamp-2">{meta.summary}</p>
        <div className="mt-4 flex flex-wrap items-center gap-x-2 text-[11px] text-[#767676]">
          <span className="font-medium text-[#333]">{meta.author}</span>
          <span aria-hidden>·</span>
          <span>{meta.published}</span>
          <span aria-hidden>·</span>
          <span>{meta.readTime}</span>
        </div>
      </div>
    </article>
  );
}

function BriefCard({ title, description, href, cta }) {
  return (
    <Link
      to={href}
      className="group flex flex-col justify-between rounded-xl border border-[#e4e7ec] bg-white p-6 md:p-7 transition-shadow hover:shadow-sm"
    >
      <div>
        <p className="text-[11px] font-bold uppercase tracking-[0.14em] text-[#6b7280]">Daily Brief</p>
        <h3 className="mt-2 font-serif text-xl md:text-2xl font-bold text-[#111111]">{title}</h3>
        <p className="mt-3 text-sm leading-relaxed text-[#555555] line-clamp-3">{description}</p>
      </div>
      <span className="mt-6 inline-flex text-sm font-semibold text-[#0b1f33] group-hover:underline underline-offset-4">
        {cta}
      </span>
    </Link>
  );
}

export default function ResearchTerminalHome() {
  const navigate = useNavigate();
  const { articles, loading } = usePublishedArticles({ limit: 18, section: null });

  const featured = articles[0] || null;
  const stack = articles.slice(1, 4);
  const grid = articles.slice(4, 10);

  const morningArticle = useMemo(() => articles.find(isMorning), [articles]);
  const eveningArticle = useMemo(() => articles.find(isEvening), [articles]);

  return (
    <div className="home-terminal min-h-screen bg-white text-[#111111]">
      <Helmet>
        <title>AGI — Institutional Research</title>
        <meta
          name="description"
          content="Ask AGI and read institutional research across Indian markets, global markets, private equity, hedge funds and economics."
        />
      </Helmet>

      {/* Compact Ask — under the strip */}
      <section id="agi-ask" className="border-b border-[#e8eaee] bg-[#f7f8fa]" aria-label="Ask AGI">
        <div className="mx-auto max-w-[1680px] px-4 sm:px-6 lg:px-8 py-4 home-hero-brand">
          <div className="rounded-xl border border-[#e4e7ec] bg-white px-4 py-3.5 sm:px-5">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:gap-6">
              <div className="shrink-0 lg:w-40">
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
                className="hidden shrink-0 text-xs font-semibold text-[#111111] underline-offset-4 hover:underline xl:inline"
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
                  className="rounded-full border border-[#e6e8ec] bg-[#fafbfc] px-2.5 py-1 text-[11px] font-medium text-[#444] transition-colors hover:border-[#111] hover:text-[#111]"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Desk navigation — six equal professional buttons */}
      <section className="border-b border-[#e8eaee] bg-white" aria-label="Research desks">
        <div className="mx-auto max-w-[1680px] px-4 sm:px-6 lg:px-8 py-5">
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 xl:grid-cols-6">
            {DESK_BUTTONS.map((desk) => {
              const Icon = desk.icon;
              return (
                <Link
                  key={desk.label}
                  to={desk.to}
                  className="group flex items-center gap-3 rounded-xl border border-[#e4e7ec] bg-[#fafbfc] px-3.5 py-3.5 transition-colors hover:border-[#0b1f33]/35 hover:bg-white"
                >
                  <span className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-[#e8eaee] bg-white text-[#0b1f33] group-hover:border-[#0b1f33]/20">
                    <Icon className="h-4 w-4" aria-hidden />
                  </span>
                  <span className="min-w-0">
                    <span className="block text-sm font-semibold text-[#111111]">{desk.label}</span>
                    <span className="block text-[11px] text-[#767676]">{desk.hint}</span>
                  </span>
                </Link>
              );
            })}
          </div>
        </div>
      </section>

      {/* Research mosaic */}
      <section id="latest-research" className="border-b border-[#e8eaee] bg-white" aria-label="Latest research">
        <div className="mx-auto max-w-[1680px] px-4 sm:px-6 lg:px-8 py-10 md:py-12">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 className="font-serif text-3xl font-bold tracking-tight text-[#111111]">Latest Research</h2>
              <p className="mt-1.5 text-sm text-[#555555]">Editorial research from the AGI desk.</p>
            </div>
            <Link to="/research" className="text-sm font-semibold text-[#111111] hover:underline underline-offset-4">
              View all research →
            </Link>
          </div>

          {loading ? (
            <div className="mt-8 grid grid-cols-1 gap-5 lg:grid-cols-[1.6fr_1fr]">
              <div className="h-[340px] animate-pulse rounded-xl border border-[#e8eaee] bg-[#f7f8fa]" />
              <div className="h-[340px] animate-pulse rounded-xl border border-[#e8eaee] bg-[#f7f8fa]" />
            </div>
          ) : !articles.length ? (
            <div className="mt-8 rounded-xl border border-[#e8eaee] px-6 py-14 text-center">
              <p className="font-serif text-xl font-bold text-[#111111]">Research notes are publishing soon</p>
              <p className="mt-2 text-sm text-[#555555]">Ask AGI while the desk prepares the next notes.</p>
            </div>
          ) : (
            <>
              <div className="mt-8 grid grid-cols-1 gap-5 lg:grid-cols-[1.65fr_1fr] lg:items-stretch">
                <FeaturedArticle article={featured} />
                <div className="rounded-xl border border-[#e4e7ec] bg-white px-5 py-4 md:px-6">
                  <p className="mb-1 text-[11px] font-bold uppercase tracking-[0.14em] text-[#6b7280]">
                    Also on the desk
                  </p>
                  <div>
                    {stack.map((article, i) => (
                      <StackArticle key={article.id || article.slug || i} article={article} index={i} />
                    ))}
                  </div>
                </div>
              </div>

              {grid.length > 0 ? (
                <div className="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-3">
                  {grid.map((article, i) => (
                    <GridArticle key={article.id || article.slug || i} article={article} index={i} />
                  ))}
                </div>
              ) : null}
            </>
          )}
        </div>
      </section>

      {/* Morning / Evening */}
      <section className="border-b border-[#e8eaee] bg-[#f7f8fa]" aria-label="Morning and evening intelligence">
        <div className="mx-auto max-w-[1680px] px-4 sm:px-6 lg:px-8 py-10 md:py-12">
          <h2 className="font-serif text-2xl md:text-3xl font-bold text-[#111111]">Daily Intelligence</h2>
          <p className="mt-1.5 text-sm text-[#555555]">Overnight developments and market-close summaries.</p>
          <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2">
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

      <NewsletterSection variant="minimal" />
    </div>
  );
}
