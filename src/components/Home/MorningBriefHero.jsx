import { Link } from 'react-router-dom';
import { Clock, BookOpen } from 'lucide-react';
import useMorningBrief from '@/hooks/useMorningBrief';
import useMarketDashboard from '@/hooks/useMarketDashboard';

function OutlookBadge({ outlook }) {
  if (!outlook) return null;
  const key = String(outlook).toLowerCase();
  const bullish = key.includes('bullish') && !key.includes('bear');
  const bearish = key.includes('bearish');
  const cls = bullish
    ? 'bg-[#e8f5e9] text-[#1b5e20] border-[#a5d6a7]'
    : bearish
      ? 'bg-[#ffebee] text-[#b71c1c] border-[#ef9a9a]'
      : 'bg-[#fff8e1] text-[#f57f17] border-[#ffe082]';

  return (
    <span className={`inline-flex items-center text-[11px] font-bold uppercase tracking-wide px-2.5 py-1 border ${cls}`}>
      {outlook}
    </span>
  );
}

export default function MorningBriefHero() {
  const { brief, loading } = useMorningBrief();
  const { outlook, loading: dashLoading } = useMarketDashboard();

  const link = brief?.slug ? `/article/${brief.slug}` : '/updates/pre-market';
  const label = brief?.heroLabel || "Today's Market Brief";

  return (
    <section className="border-b border-[#dddddd] py-8 lg:py-10">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        <div className="lg:col-span-7">
          {loading ? (
            <div className="animate-pulse space-y-4">
              <div className="h-4 w-32 bg-[#eee]" />
              <div className="h-12 bg-[#eee]" />
              <div className="h-24 bg-[#eee]" />
            </div>
          ) : (
            <>
              <span className="text-[11px] font-bold uppercase tracking-wider text-[#ff6600]">
                {label}
              </span>

              <h1 className="mt-3 text-3xl md:text-4xl lg:text-[2.75rem] font-bold text-[#111111] leading-[1.1] tracking-tight">
                {brief?.title}
              </h1>

              <div className="flex flex-wrap items-center gap-3 mt-4 text-xs text-[#767676]">
                {brief?.published_at && (
                  <span className="flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" />
                    {brief.publishedLabel || brief.timeAgo}
                  </span>
                )}
                <span className="flex items-center gap-1">
                  <BookOpen className="w-3.5 h-3.5" />
                  {brief?.readTime || 5} min read
                </span>
                {!dashLoading && outlook?.outlook && (
                  <OutlookBadge outlook={outlook.outlook} />
                )}
              </div>

              <p className="mt-5 text-base md:text-lg text-[#444444] leading-relaxed max-w-2xl">
                {brief?.excerpt}
              </p>

              <Link
                to={link}
                className="inline-flex mt-6 bg-[#111111] text-white text-sm font-bold px-6 py-3 hover:bg-[#333333] transition-colors"
              >
                Read Full Report →
              </Link>
            </>
          )}
        </div>

        <div className="lg:col-span-5">
          <Link to={link} className="block group">
            <div className="aspect-[16/10] bg-[#f0f0f0] overflow-hidden">
              <img
                src={brief?.cover_url || 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1200&q=80'}
                alt={brief?.title || "Today's market brief"}
                className="w-full h-full object-cover group-hover:scale-[1.02] transition-transform duration-500"
              />
            </div>
            <p className="text-[11px] text-[#767676] mt-2">
              Updated every trading day · Agarwal Global Investments
            </p>
          </Link>
        </div>
      </div>
    </section>
  );
}
