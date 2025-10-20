// src/components/DealTracker.jsx
import React, { useEffect, useState, useRef } from "react";
import { RefreshCcw, ExternalLink } from "lucide-react"; // ✅ FIXED ICON IMPORT

const API_BASE = import.meta.env.VITE_API_URL || window?.API_URL || "";

export default function DealTracker() {
  const [region, setRegion] = useState("global");
  const [deals, setDeals] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const mounted = useRef(false);

  const fetchDeals = async (opts = {}) => {
    const limit = opts.limit || 12;
    try {
      setLoading(true);
      setError(null);
      const url = `${API_BASE}/api/perplexity/deals?region=${encodeURIComponent(region)}&limit=${limit}`;
      const res = await fetch(url, { credentials: "same-origin" });
      if (!res.ok) {
        const txt = await res.text().catch(() => "");
        throw new Error(`Upstream error ${res.status}: ${txt || res.statusText}`);
      }
      const json = await res.json();
      const arr = Array.isArray(json) ? json : json.parsed ?? json;
      if (!Array.isArray(arr)) {
        console.warn("[DealTracker] unexpected payload", json);
        setDeals([]);
        setError("Unexpected response from deals API (check server logs).");
        return;
      }

      const norm = arr.map((it) => ({
        acquirer: it.acquirer ?? it.buyer ?? "Unknown",
        target: it.target ?? it.company ?? "Unknown",
        value: it.value ?? "Undisclosed",
        sector: it.sector ?? it.industry ?? "N/A",
        type: it.type ?? "M&A",
        region: it.region ?? region,
        date: it.date ? new Date(it.date) : null,
        source: it.source ?? null,
      }));
      setDeals(norm);
    } catch (err) {
      console.error("[DealTracker] fetch error:", err);
      setError("Failed to load deals. Try refreshing or check server.");
    } finally {
      if (mounted.current) setLoading(false);
      else setLoading(false);
    }
  };

  useEffect(() => {
    mounted.current = true;
    fetchDeals();
    return () => {
      mounted.current = false;
    };
  }, [region]);

  return (
    <div className="max-w-6xl mx-auto px-6 py-12">
      <header className="text-center mb-8">
        <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-gray-900">
          Tracking the World of Deals
        </h1>
        <p className="mt-2 text-gray-600">
          Live updates on private equity, M&A, and buyout activity across sectors and regions.
        </p>

        <div className="flex items-center justify-center gap-3 mt-6">
          <select
            value={region}
            onChange={(e) => setRegion(e.target.value)}
            aria-label="Select region"
            className="border border-gray-300 rounded-lg px-3 py-2 bg-white text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-black"
          >
            <option value="global">🌍 Global</option>
            <option value="india">🇮🇳 India</option>
            <option value="asia">Asia</option>
            <option value="europe">Europe</option>
            <option value="usa">United States</option>
          </select>

          <button
            onClick={() => fetchDeals({ limit: 20 })}
            className="inline-flex items-center gap-2 bg-black text-white px-4 py-2 rounded-lg text-sm hover:bg-gray-800 transition"
            title="Refresh deals"
            aria-label="Refresh deals"
          >
            <RefreshCcw size={16} /> {/* ✅ FIXED ICON */}
            <span>Refresh</span>
          </button>
        </div>
      </header>

      <section>
        {loading ? (
          <div className="text-center text-gray-500 py-16">Loading latest deals…</div>
        ) : error ? (
          <div className="text-center text-red-600 py-12">{error}</div>
        ) : deals.length === 0 ? (
          <div className="text-center text-gray-500 py-12">
            No deals found for <strong>{region}</strong>. Try another region or refresh.
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {deals.map((d, i) => (
              <article
                key={`${d.acquirer}-${d.target}-${i}`}
                className="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm hover:shadow-md transition"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900">
                      {d.acquirer} <span className="text-gray-400">→</span> {d.target}
                    </h2>
                    <div className="mt-1 text-sm text-gray-600">
                      <span className="inline-block mr-2"><strong>Sector:</strong> {d.sector}</span>
                      <span className="inline-block mr-2"><strong>Type:</strong> {d.type}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-gray-500">{d.region}</div>
                    <div className="mt-2 text-sm font-medium text-gray-900">
                      {d.value ?? "Undisclosed"}
                    </div>
                  </div>
                </div>

                <div className="mt-4 text-sm text-gray-600 space-y-2">
                  <div>
                    <strong>Date:</strong>{" "}
                    {d.date ? d.date.toLocaleDateString() : "—"}
                  </div>

                  {d.source ? (
                    <div>
                      <a
                        href={d.source}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 text-blue-600 hover:underline"
                      >
                        Source
                        <ExternalLink size={14} />
                      </a>
                    </div>
                  ) : (
                    <div className="text-xs text-gray-400">Source not provided</div>
                  )}
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      <footer className="mt-10 text-center text-xs text-gray-500">
        Data provided by Perplexity (via your backend). Refreshes on demand and when region changes.
      </footer>
    </div>
  );
}
