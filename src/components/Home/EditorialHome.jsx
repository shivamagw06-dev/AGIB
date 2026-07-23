import { Link } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';
import MorningBriefHero from '@/components/Home/MorningBriefHero';
import TodayDashboard from '@/components/Home/TodayDashboard';
import IndexSentimentTicker from '@/components/Home/IndexSentimentTicker';
import ResearchNotesPreview from '@/components/Home/ResearchNotesPreview';
import InstitutionalResearchCard from '@/components/Home/InstitutionalResearchCard';
import NewsletterSection from '@/components/Home/NewsletterSection';
import usePublishedArticles from '@/hooks/usePublishedArticles';
import { MARKET_UPDATE_SECTIONS, SECTOR_RESEARCH } from '@/config/sectors';
import { formatTimeAgo } from '@/lib/articleUtils';

function SectionHeader({ title, subtitle, href, linkLabel = 'View all →' }) {
  return (
    <div className="flex items-end justify-between mb-5 pb-3 border-b border-[#eeeeee]">
      <div>
        <h2 className="text-lg font-bold text-[#111111]">{title}</h2>
        {subtitle && <p className="text-xs text-[#767676] mt-1">{subtitle}</p>}
      </div>
      {href && (
        <Link to={href} className="text-xs font-bold text-[#111111] hover:text-[#ff6600] shrink-0">
          {linkLabel}
        </Link>
      )}
    </div>
  );
}

function MarketUpdateStrip({ section, articles, loading }) {
  const latest = articles[0];
  return (
    <div className="border border-[#dddddd] p-4 hover:border-[#999] transition-colors">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-bold text-[#111111]">{section.title}</h3>
        <Link
          to={section.path}
          className="text-[#ccc] hover:text-[#ff6600] transition-colors"
          aria-label={`View ${section.title}`}
        >
          <ChevronRight className="w-4 h-4" />
        </Link>
      </div>
      {loading ? (
        <div className="h-16 bg-[#eee] animate-pulse" />
      ) : latest ? (
        <Link to={`/article/${latest.slug}`} className="group block">
          <p className="text-sm font-bold text-[#111111] leading-snug group-hover:underline line-clamp-2">
            {latest.title}
          </p>
          <p className="text-[11px] text-[#767676] mt-2">
            {formatTimeAgo(latest.date || latest.published_at)}
          </p>
        </Link>
      ) : (
        <Link to={section.path} className="text-xs text-[#767676] hover:text-[#ff6600]">
          Publish in CMS →
        </Link>
      )}
    </div>
  );
}

function SectorGrid() {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-7 gap-2">
      {SECTOR_RESEARCH.map((s) => (
        <Link
          key={s.id}
          to={s.path}
          className="border border-[#dddddd] px-3 py-3 text-center text-xs font-bold text-[#111111] hover:border-[#111111] hover:text-[#ff6600] transition-colors"
        >
          {s.name}
        </Link>
      ))}
    </div>
  );
}

function MarketUpdateSectionLoader({ sectionId }) {
  const section = MARKET_UPDATE_SECTIONS.find((s) => s.id === sectionId);
  const { articles, loading } = usePublishedArticles({ limit: 1, section: section?.section });
  return (
    <MarketUpdateStrip section={section} articles={articles} loading={loading} />
  );
}

export default function EditorialHome() {
  const { articles: research, loading: researchLoading } = usePublishedArticles({
    limit: 6,
    section: null,
  });

  const featuredResearch = research.filter(
    (a) =>
      a.section?.includes('Research') ||
      a.category?.includes('Research') ||
      !a.section?.includes('Update')
  ).slice(0, 4);

  const companyUpdates = research.filter(
    (a) => a.section === 'Company Updates' || a.category === 'Company Updates'
  ).slice(0, 3);

  const macroArticles = research.filter(
    (a) =>
      a.section?.includes('Macro') ||
      (Array.isArray(a.tags) && a.tags.some((t) => /macro|global/i.test(t)))
  ).slice(0, 3);

  return (
    <div className="bg-white min-h-screen">
      <div className="max-w-[1280px] mx-auto px-4">
        <MorningBriefHero />
        <IndexSentimentTicker />
        <TodayDashboard />
        <ResearchNotesPreview />

        {/* Market update cadence */}
        <section className="py-8 border-b border-[#dddddd]">
          <SectionHeader
            title="Trading Day Updates"
            subtitle="Published throughout the session"
            href="/market-updates"
          />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <MarketUpdateSectionLoader sectionId="pre-market" />
            <MarketUpdateSectionLoader sectionId="midday" />
            <MarketUpdateSectionLoader sectionId="market-close" />
          </div>
        </section>

        {/* Featured research */}
        <section className="py-8 border-b border-[#dddddd]">
          <SectionHeader
            title="Research Notes & Featured Analysis"
            subtitle="Independent perspectives from the AGI research desk"
            href="/research"
          />
          {researchLoading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-64 bg-[#eee] animate-pulse" />
              ))}
            </div>
          ) : featuredResearch.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {featuredResearch.map((a) => (
                <InstitutionalResearchCard key={a.id} article={a} />
              ))}
            </div>
          ) : (
            <p className="text-sm text-[#767676]">
              Publish research notes in CMS to populate this section.{' '}
              <Link to="/research" className="font-bold text-[#111] hover:text-[#ff6600]">
                Browse research →
              </Link>
            </p>
          )}
        </section>

        {/* Company updates */}
        <section className="py-8 border-b border-[#dddddd]">
          <SectionHeader title="Latest Company Updates" href="/company-updates" />
          {companyUpdates.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {companyUpdates.map((a) => (
                <InstitutionalResearchCard key={a.id} article={a} showImage={false} />
              ))}
            </div>
          ) : (
            <p className="text-sm text-[#767676]">
              Tag articles with section &ldquo;Company Updates&rdquo; in CMS.
            </p>
          )}
        </section>

        {/* Sector research */}
        <section className="py-8 border-b border-[#dddddd]">
          <SectionHeader
            title="Sector Research"
            subtitle="Deep-dive coverage across key sectors"
            href="/research"
          />
          <SectorGrid />
        </section>

        {/* Macro */}
        <section className="py-8 border-b border-[#dddddd]">
          <SectionHeader title="Macro & Global Markets" href="/research" />
          {macroArticles.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {macroArticles.map((a) => (
                <InstitutionalResearchCard key={a.id} article={a} showImage={false} />
              ))}
            </div>
          ) : (
            <p className="text-sm text-[#767676]">
              Publish macro articles with tags like &ldquo;Macro&rdquo; or &ldquo;Global Markets&rdquo;.
            </p>
          )}
        </section>
      </div>

      <NewsletterSection />
    </div>
  );
}
