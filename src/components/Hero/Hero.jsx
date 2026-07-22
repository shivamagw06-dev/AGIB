// Place this file at: src/components/Hero/Hero.jsx
import React, { useMemo } from "react";
import { motion } from "framer-motion";
import useMarketData from "@/hooks/useMarketData";
import useFeaturedArticle from "@/hooks/useFeaturedArticle";
import {
  ArrowRight,
  Building2,
  Clock3,
  Globe2,
  TrendingUp,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";

const focusTopics = [
  "RBI",
  "GDP",
  "Inflation",
  "Earnings",
  "Oil",
  "Gold",
  "Banking",
  "FII Flows",
];

const economicEvents = [
  { title: "India CPI", detail: "Inflation data", timing: "Watch calendar" },
  { title: "RBI Policy", detail: "Monetary policy", timing: "Watch calendar" },
  { title: "US FOMC", detail: "Interest-rate decision", timing: "Watch calendar" },
];

function formatNumber(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "—";

  return new Intl.NumberFormat("en-IN", {
    maximumFractionDigits: 2,
  }).format(number);
}

function formatChange(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "—";

  return `${number > 0 ? "+" : ""}${number.toFixed(2)}%`;
}

export default function Hero() {
  const navigate = useNavigate();
  const { indices = [], commodities = [], loading } = useMarketData();
  const { article: featuredArticle, loading: articleLoading } = useFeaturedArticle();

  const marketSnapshot = useMemo(() => {
    const priority = ["NIFTY 50", "SENSEX", "NIFTY BANK", "BANK NIFTY"];

    return priority
      .map((name) => indices.find((index) => index.name?.toUpperCase() === name))
      .filter(Boolean)
      .slice(0, 4)
      .map((index) => ({
        name: index.name,
        value: formatNumber(index.price),
        change: formatChange(index.percentChange),
        isPositive: Number(index.percentChange) >= 0,
        updatedAt: [index.date, index.time].filter(Boolean).join(" "),
      }));
  }, [indices]);

  const commoditySnapshot = useMemo(
    () =>
      commodities
        .filter((item) => /gold|silver|crude|copper/i.test(item.product || ""))
        .slice(0, 3)
        .map((item) => ({
          name: item.product,
          value: formatNumber(item.last_traded_price),
          change: formatChange(item.per_change),
          isPositive: Number(item.per_change) >= 0,
        })),
    [commodities]
  );

  const lastUpdated = marketSnapshot.find((item) => item.updatedAt)?.updatedAt;

  return (
    <section className="bg-white border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-6 lg:px-8 py-12">
        <div className="grid lg:grid-cols-12 gap-12">
          <motion.div
            initial={{ opacity: 0, y: 25 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="lg:col-span-8"
          >
            <div className="inline-flex items-center gap-2 rounded-full bg-blue-50 text-blue-700 px-4 py-2 text-sm font-semibold">
              <TrendingUp size={16} />
              {featuredArticle ? "Featured Research" : "Research Platform"}
            </div>

            {articleLoading ? (
              <div className="mt-6 space-y-4 animate-pulse">
                <div className="h-12 bg-slate-100 rounded-lg w-3/4" />
                <div className="h-12 bg-slate-100 rounded-lg w-full" />
                <div className="h-6 bg-slate-100 rounded-lg w-1/2" />
                <div className="h-24 bg-slate-100 rounded-lg w-full mt-8" />
              </div>
            ) : featuredArticle ? (
              <>
                <h1 className="mt-6 text-4xl md:text-5xl lg:text-6xl font-bold leading-tight tracking-tight text-slate-900">
                  {featuredArticle.title}
                </h1>

                <div className="mt-6 flex flex-wrap items-center gap-5 text-sm text-slate-500">
                  <span className="flex items-center gap-2">
                    <Clock3 size={16} /> {featuredArticle.publishedLabel}
                  </span>
                  <span className="flex items-center gap-2">
                    <Building2 size={16} /> {featuredArticle.category}
                  </span>
                  {Array.isArray(featuredArticle.tags) && featuredArticle.tags[0] && (
                    <span className="flex items-center gap-2">
                      <Globe2 size={16} /> {featuredArticle.tags[0]}
                    </span>
                  )}
                </div>

                <p className="mt-8 max-w-3xl text-lg md:text-xl leading-9 text-slate-600">
                  {featuredArticle.excerpt || "Read our latest institutional research and market analysis."}
                </p>

                <div className="mt-10 flex flex-wrap gap-4">
                  <Button
                    size="lg"
                    className="rounded-lg h-12 px-7 bg-blue-700 hover:bg-blue-800"
                    onClick={() => navigate(`/article/${featuredArticle.slug}`)}
                  >
                    Read full research <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="lg"
                    className="rounded-lg h-12 px-7 border-slate-300 text-slate-800 hover:bg-slate-50"
                    onClick={() => navigate("/sections/live-articles")}
                  >
                    Browse research library
                  </Button>
                </div>
              </>
            ) : (
              <>
                <h1 className="mt-6 text-4xl md:text-5xl lg:text-6xl font-bold leading-tight tracking-tight text-slate-900">
                  Independent Research for Serious Investors
                </h1>

                <p className="mt-8 max-w-3xl text-lg md:text-xl leading-9 text-slate-600">
                  Publish your first research article and it will appear here automatically
                  as the featured story on your homepage.
                </p>

                <div className="mt-10 flex flex-wrap gap-4">
                  <Button
                    size="lg"
                    className="rounded-lg h-12 px-7 bg-blue-700 hover:bg-blue-800"
                    onClick={() => navigate("/write")}
                  >
                    Write your first article <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="lg"
                    className="rounded-lg h-12 px-7 border-slate-300 text-slate-800 hover:bg-slate-50"
                    onClick={() => navigate("/sections/live-articles")}
                  >
                    Browse research library
                  </Button>
                </div>
              </>
            )}

            <div className="grid md:grid-cols-3 gap-5 mt-14">
              {[
                ["Markets", "Daily analysis of equities, bonds, commodities, currencies and global markets."],
                ["Economy", "GDP, inflation, RBI policy, macro indicators and global outlook."],
                ["Private Markets", "M&A, venture capital, private equity and strategic transactions."],
              ].map(([title, description]) => (
                <div key={title} className="rounded-xl border border-slate-200 p-6">
                  <h2 className="font-semibold text-slate-900">{title}</h2>
                  <p className="mt-3 text-sm leading-7 text-slate-600">{description}</p>
                </div>
              ))}
            </div>
          </motion.div>

          <motion.aside
            initial={{ opacity: 0, x: 25 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.15 }}
            className="lg:col-span-4"
          >
            <div className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
              <div className="border-b border-slate-200 p-6">
                <div className="flex items-center justify-between gap-4">
                  <h2 className="text-xl font-bold text-slate-900">Market Snapshot</h2>
                  <span className="rounded-full bg-green-100 px-3 py-1 text-xs font-semibold text-green-700">Delayed live</span>
                </div>
                <p className="mt-2 text-sm text-slate-500">
                  {lastUpdated ? `Last updated ${lastUpdated}` : "Updating market data…"}
                </p>
              </div>

              <div className="divide-y divide-slate-200">
                {loading && marketSnapshot.length === 0 ? (
                  <p className="px-6 py-5 text-sm text-slate-500">Loading live indices…</p>
                ) : marketSnapshot.length > 0 ? (
                  marketSnapshot.map((item) => (
                    <div key={item.name} className="flex items-center justify-between px-6 py-4 hover:bg-slate-50">
                      <div>
                        <p className="text-sm text-slate-500">{item.name}</p>
                        <p className="font-semibold text-slate-900">{item.value}</p>
                      </div>
                      <span className={`text-sm font-semibold ${item.isPositive ? "text-green-600" : "text-red-600"}`}>
                        {item.change}
                      </span>
                    </div>
                  ))
                ) : (
                  <p className="px-6 py-5 text-sm text-slate-500">Live index data is temporarily unavailable.</p>
                )}
              </div>

              {commoditySnapshot.length > 0 && (
                <div className="border-t border-slate-200 p-6">
                  <h3 className="font-semibold text-slate-900">Commodities</h3>
                  <div className="mt-4 space-y-3">
                    {commoditySnapshot.map((item) => (
                      <div key={item.name} className="flex items-center justify-between text-sm">
                        <span className="text-slate-600">{item.name}</span>
                        <span className="flex items-center gap-2">
                          <strong className="text-slate-900">{item.value}</strong>
                          <span className={item.isPositive ? "text-green-600" : "text-red-600"}>{item.change}</span>
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="border-t border-slate-200 p-6">
                <h3 className="font-semibold text-slate-900 mb-4">Today&apos;s Focus</h3>
                <div className="flex flex-wrap gap-2">
                  {focusTopics.map((topic) => (
                    <button
                      type="button"
                      key={topic}
                      className="rounded-full border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-100"
                      onClick={() => navigate("/sections/live-articles")}
                    >
                      {topic}
                    </button>
                  ))}
                </div>
              </div>

              <div className="border-t border-slate-200 p-6">
                <h3 className="font-semibold text-slate-900 mb-4">Economic Calendar</h3>
                <div className="space-y-4">
                  {economicEvents.map((event) => (
                    <div className="flex items-start justify-between gap-4" key={event.title}>
                      <div>
                        <p className="font-medium text-slate-800">{event.title}</p>
                        <p className="text-sm text-slate-500">{event.detail}</p>
                      </div>
                      <span className="shrink-0 text-sm text-blue-700">{event.timing}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="border-t border-slate-200 p-6">
                <Button className="w-full h-11 rounded-lg bg-blue-700 hover:bg-blue-800" onClick={() => navigate("/sections/research-notes")}>
                  Read morning brief
                </Button>
              </div>
            </div>
          </motion.aside>
        </div>
      </div>
    </section>
  );
}
