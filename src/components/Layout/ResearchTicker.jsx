import { ChevronRight } from "lucide-react";
import { useMarketOverviewContext } from "@/contexts/MarketOverviewContext";
import { formatPct, pctClass } from "@/lib/marketFormat";

export default function ResearchTicker() {
  const { gainers, commodities, news, loading } = useMarketOverviewContext();

  const commodityTags = commodities
    .filter((c) => /gold|silver|crude|copper|natural/i.test(c.product || ""))
    .slice(0, 3)
    .map((c) => `${c.product?.replace(/MIC$/i, "")} ${formatPct(c.per_change)}`);

  const moverTags = gainers.slice(0, 4).map((g) => `${g.name?.split(" ")[0]} ${formatPct(g.change)}`);

  const newsTags = news.slice(0, 2).map((n) => n.topics?.[0] || n.source).filter(Boolean);

  const items = loading
    ? ["Markets", "Economy", "RBI Policy", "Inflation", "IPO Watch"]
    : [...moverTags, ...commodityTags, ...newsTags, "IPO Watch", "Mutual Funds"];

  return (
    <section className="border-b border-slate-200 bg-white">
      <div className="max-w-7xl mx-auto flex items-center overflow-x-auto whitespace-nowrap px-6 py-3 scrollbar-hide">
        <span className="mr-5 font-semibold text-blue-700 shrink-0">Live Markets</span>

        {items.map((item) => (
          <div key={item} className="flex items-center text-sm text-slate-700 shrink-0">
            <span
              className={`px-3 hover:text-blue-700 cursor-default transition-colors ${
                item.includes("%") ? pctClass(parseFloat(item.match(/-?\d+\.?\d*/)?.[0])) : ""
              }`}
            >
              {item}
            </span>
            <ChevronRight className="h-3 w-3 text-slate-300" />
          </div>
        ))}
      </div>
    </section>
  );
}
