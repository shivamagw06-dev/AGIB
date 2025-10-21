// src/components/ResearchNotes.jsx
import React, { useEffect, useState, useCallback, useRef } from "react";
import { motion } from "framer-motion";
import { Download, FileText, RefreshCw, UploadCloud, Search as SearchIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/use-toast";
import { supabase } from "@/lib/supabaseClient";

/**
 * ResearchNotes component
 *
 * Features:
 * - Default tab = "notes" (your authored/retrieved research notes)
 * - Tabs: Notes | Deals | News
 * - Notes: list from Supabase `research_notes` table (schema described earlier)
 * - Upload (admin): upload PDF/MD to Supabase Storage and create research_notes row
 * - Search + tag filter + pagination (simple "load more")
 * - Download file when available
 * - Optional: fetch deals/news from backend proxy endpoints:
 *     /api/perplexity/deals (deals)
 *     /api/news (IndianAPI, proxied)
 *
 * Requirements:
 * - supabase client exported from '@/lib/supabaseClient'
 * - toast UI hook
 * - backend proxy endpoints for deals/news (optional)
 */

const PAGE_SIZE = 8;
const API_BASE = import.meta.env.VITE_API_URL || window?.API_URL || "";

export default function ResearchNotes() {
  const { toast } = useToast();
  const [tab, setTab] = useState("notes"); // 'notes' | 'deals' | 'news'
  const [notes, setNotes] = useState([]);
  const [deals, setDeals] = useState([]);
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [query, setQuery] = useState("");
  const [tagFilter, setTagFilter] = useState("all");
  const [uploading, setUploading] = useState(false);
  const [fileInput, setFileInput] = useState(null);
  const mounted = useRef(false);

  // Admin fields for upload
  const titleRef = useRef();
  const descRef = useRef();
  const tagsRef = useRef();

  // Basic fetch for research notes from Supabase
  const fetchNotes = useCallback(async ({ reset = false } = {}) => {
    try {
      if (!mounted.current) return;
      if (reset) {
        setPage(0);
        setHasMore(true);
        setNotes([]);
      }
      const nextPage = reset ? 0 : page;
      setLoading(nextPage === 0);
      setLoadingMore(nextPage > 0);
      // simple full-text candidate: filter title/description with ilike
      let q = supabase
        .from("research_notes")
        .select("id,title,summary,body,source_name,source_url,image_url,tags,published_at,file_path,created_at")
        .order("published_at", { ascending: false })
        .range(nextPage * PAGE_SIZE, nextPage * PAGE_SIZE + PAGE_SIZE - 1);

      // apply search
      if (query && query.trim()) {
        const like = `%${query.trim()}%`;
        q = q.or(`title.ilike.${like},summary.ilike.${like},body.ilike.${like}`);
      }

      // apply tag filter (tags is stored as text[] in Postgres)
      if (tagFilter && tagFilter !== "all") {
        q = q.contains("tags", [tagFilter]);
      }

      const { data, error, count } = await q;
      if (error) throw error;

      const normalized = (data || []).map((r) => ({
        id: r.id,
        title: r.title,
        summary: r.summary,
        description: r.body || r.summary,
        source_name: r.source_name,
        source_url: r.source_url,
        image: r.image_url,
        tags: r.tags || [],
        published_at: r.published_at || r.created_at,
        file_url: r.file_path ? supabase.storage.from("research-files").getPublicUrl(r.file_path).publicURL : null,
        raw: r,
      }));

      if (reset) setNotes(normalized);
      else setNotes((prev) => [...prev, ...normalized]);

      // update hasMore
      if (!normalized.length || normalized.length < PAGE_SIZE) setHasMore(false);
      else setHasMore(true);

      setPage(nextPage + 1);
    } catch (err) {
      console.error("fetchNotes error:", err);
      toast({ title: "Error", description: "Failed to load research notes. See console.", variant: "destructive" });
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, [page, query, tagFilter, toast]);

  // Optional: fetch deals from backend proxy
  const fetchDeals = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/api/perplexity/deals?region=global&limit=12`);
      if (!res.ok) {
        const t = await res.text().catch(() => "");
        throw new Error(t || res.statusText);
      }
      const json = await res.json();
      const arr = Array.isArray(json) ? json : json.parsed ?? json.data ?? [];
      setDeals((arr || []).map((it, i) => ({
        id: it.id ?? `deal-${i}`,
        acquirer: it.acquirer ?? it.buyer ?? "—",
        target: it.target ?? it.company ?? "—",
        sector: it.sector,
        value: it.value,
        region: it.region,
        date: it.date,
        source: it.source,
        raw: it,
      })));
    } catch (err) {
      console.error("fetchDeals error:", err);
      toast({ title: "Deals load failed", description: "Check server logs", variant: "destructive" });
      setDeals([]);
    } finally {
      setLoading(false);
    }
  }, [toast]);

  // Optional: fetch IndianAPI news via your backend
  const fetchNews = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/api/news`);
      if (!res.ok) {
        const t = await res.text().catch(() => "");
        throw new Error(t || res.statusText);
      }
      const json = await res.json();
      let arr = Array.isArray(json) ? json : json.data ?? json.articles ?? [];
      arr = arr || [];
      setNews(arr.map((it, i) => ({
        id: it.id ?? `news-${i}`,
        title: it.title ?? it.headline ?? "Untitled",
        snippet: it.description ?? it.summary ?? it.snippet ?? "",
        image: it.image || it.thumbnail || null,
        source: it.source || (it.url ? new URL(it.url).hostname : "source"),
        sourceUrl: it.url || it.link,
        publishedAt: it.publishedAt || it.date,
        raw: it,
      })));
    } catch (err) {
      console.error("fetchNews error:", err);
      toast({ title: "News load failed", description: "Check server logs", variant: "destructive" });
      setNews([]);
    } finally {
      setLoading(false);
    }
  }, [toast]);

  // initial load
  useEffect(() => {
    mounted.current = true;
    // default: notes (your requirement). But we fetch news as well so tab switch is instant.
    fetchNotes({ reset: true });
    fetchNews();
    // don't auto-fetch deals to avoid extra calls (optional)
    return () => { mounted.current = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // reload when filters/search change
  useEffect(() => {
    // reset pagination and fetch
    setPage(0);
    setHasMore(true);
    fetchNotes({ reset: true });
  }, [query, tagFilter]); // eslint-disable-line

  // upload handler (admin)
  const handleFileChange = (e) => {
    setFileInput(e.target.files?.[0] ?? null);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!fileInput) {
      toast({ title: "No file", description: "Choose a file first", variant: "destructive" });
      return;
    }
    const title = titleRef.current?.value?.trim() ?? "";
    const description = descRef.current?.value?.trim() ?? "";
    const tags = (tagsRef.current?.value ?? "").split(",").map(s => s.trim()).filter(Boolean);
    if (!title) {
      toast({ title: "Title required", description: "Provide a title for the report", variant: "destructive" });
      return;
    }

    try {
      setUploading(true);
      const filePath = `reports/${Date.now()}_${fileInput.name}`;
      const { data: uploadData, error: uploadError } = await supabase.storage
        .from("research-files")
        .upload(filePath, fileInput, { cacheControl: "3600", upsert: false });
      if (uploadError) throw uploadError;

      // insert row in research_notes table
      const payload = {
        title,
        summary: description?.slice(0, 600),
        body: description,
        source_type: "UPLOAD",
        source_name: "AGI",
        source_url: null,
        image_url: null,
        tags,
        published_at: new Date().toISOString(),
        file_path: filePath,
      };

      const { data: insertData, error: insertError } = await supabase.from("research_notes").insert([payload]).select();
      if (insertError) throw insertError;

      toast({ title: "Uploaded", description: "Report uploaded and saved." });
      // refresh list
      fetchNotes({ reset: true });
      // clear form
      e.target.reset?.();
      setFileInput(null);
    } catch (err) {
      console.error("upload failed", err);
      toast({ title: "Upload failed", description: err?.message || "See console", variant: "destructive" });
    } finally {
      setUploading(false);
    }
  };

  const handleDownload = (note) => {
    if (!note?.file_url) {
      toast({ title: "No file", description: "This note has no file to download.", variant: "destructive" });
      return;
    }
    window.open(note.file_url, "_blank", "noopener,noreferrer");
    toast({ title: "Opening file", description: note.title ?? "Report" });
  };

  // UI helpers: gather tag set for filter dropdown
  const availableTags = React.useMemo(() => {
    const s = new Set();
    notes.forEach(n => (n.tags || []).forEach(t => s.add(t)));
    return ["all", ...Array.from(s).slice(0, 30)];
  }, [notes]);

  // Render
  return (
    <section className="py-20 bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="flex items-start justify-between gap-6 mb-6">
          <div>
            <h1 className="text-3xl md:text-4xl font-extrabold text-foreground">In-Depth Research</h1>
            <p className="mt-1 text-muted-foreground max-w-xl">
              Download deep-dive reports, browse curated deals and the latest market news. Default view shows Notes.
            </p>
            <div className="mt-3 flex items-center gap-2 text-sm text-gray-500">
              <span className="inline-flex items-center gap-2"><FileText className="w-4 h-4" /> Notes</span>
              <span>•</span>
              <span className="inline-flex items-center gap-2"><RefreshCw className="w-4 h-4" /> Updated live</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <select value={tab} onChange={e => setTab(e.target.value)} className="border px-3 py-2 rounded bg-white">
              <option value="notes">Notes</option>
              <option value="deals">Deals</option>
              <option value="news">News</option>
            </select>

            <Button onClick={() => {
              // refresh active tab
              if (tab === "notes") fetchNotes({ reset: true });
              else if (tab === "deals") fetchDeals();
              else fetchNews();
              toast({ title: "Refreshing", description: "Fetching latest content..." });
            }} className="inline-flex items-center gap-2">
              <RefreshCw className="w-4 h-4" />
              Refresh
            </Button>
          </div>
        </motion.div>

        {/* Search / filters */}
        <div className="mb-6 flex flex-col sm:flex-row items-start sm:items-center gap-3">
          <div className="relative flex-1">
            <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={tab === "news" ? "Search news..." : "Search title, summary..."}
              className="pl-10 pr-3 py-2 border rounded w-full"
            />
          </div>

          {tab === "notes" && (
            <div className="flex items-center gap-3">
              <label className="text-sm text-gray-600">Tag:</label>
              <select value={tagFilter} onChange={(e) => setTagFilter(e.target.value)} className="border px-3 py-2 rounded">
                {availableTags.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
          )}
        </div>

        {/* CONTENT AREA */}
        <div>
          {/* NOTES */}
          {tab === "notes" && (
            <>
              {loading && notes.length === 0 ? (
                <div className="grid gap-4">
                  {Array.from({ length: 4 }).map((_, i) => (
                    <div key={i} className="animate-pulse bg-card border border-border rounded-lg p-6 flex items-center gap-6" />
                  ))}
                </div>
              ) : notes.length === 0 ? (
                <div className="bg-card border border-border rounded-lg p-6 text-center text-muted-foreground">
                  No research notes available yet. You can upload reports (admin).
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {notes.map((n) => (
                    <motion.article key={n.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="bg-card border border-border rounded-lg p-4 flex flex-col">
                      <div className="flex items-start gap-4">
                        <div className="w-20 h-20 rounded bg-gray-50 overflow-hidden flex items-center justify-center">
                          {n.image ? <img src={n.image} alt={n.title} className="object-cover w-full h-full" /> : <FileText className="w-8 h-8 text-gray-400" />}
                        </div>

                        <div className="flex-1 min-w-0">
                          <div className="text-xs text-muted-foreground mb-1">{n.published_at ? new Date(n.published_at).toLocaleDateString() : "—"}</div>
                          <h3 className="text-lg font-semibold truncate">{n.title}</h3>
                          <p className="mt-2 text-sm text-gray-600 line-clamp-3">{n.summary || n.description}</p>

                          <div className="mt-3 flex items-center gap-2 flex-wrap">
                            {(n.tags || []).slice(0, 5).map(t => <span key={t} className="text-xs bg-gray-100 px-2 py-1 rounded-full">{t}</span>)}
                          </div>
                        </div>
                      </div>

                      <div className="mt-4 flex items-center justify-between">
                        <div className="text-sm text-gray-500">{n.source_name ?? (n.raw?.source_name) ?? ""}</div>
                        <div className="flex items-center gap-2">
                          <Button onClick={() => handleDownload(n)} className="inline-flex items-center gap-2">
                            <Download className="w-4 h-4" /> Download
                          </Button>
                          <a href={n.source_url || "#"} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-600 hover:underline">View source</a>
                        </div>
                      </div>
                    </motion.article>
                  ))}
                </div>
              )}

              {/* Load more */}
              <div className="mt-6 flex justify-center">
                {hasMore ? (
                  <Button onClick={() => fetchNotes({ reset: false })} className="px-4 py-2">
                    {loadingMore ? "Loading..." : "Load more"}
                  </Button>
                ) : (
                  <div className="text-sm text-gray-500">No more reports</div>
                )}
              </div>

              {/* Upload form (admin) */}
              <div className="mt-8 bg-card border border-border rounded-lg p-4">
                <h4 className="font-semibold mb-2">Upload new research (admin)</h4>
                <form onSubmit={handleUpload} className="grid grid-cols-1 md:grid-cols-3 gap-3 items-end">
                  <div className="md:col-span-2 flex flex-col gap-2">
                    <input ref={titleRef} placeholder="Title" className="border px-3 py-2 rounded" />
                    <input ref={descRef} placeholder="Short description / summary" className="border px-3 py-2 rounded" />
                    <input ref={tagsRef} placeholder="Tags (comma separated)" className="border px-3 py-2 rounded" />
                  </div>

                  <div className="flex items-center gap-2">
                    <input type="file" accept=".pdf,.md,.docx" onChange={handleFileChange} />
                    <Button type="submit" disabled={uploading} className="inline-flex items-center gap-2">
                      <UploadCloud className="w-4 h-4" /> {uploading ? "Uploading..." : "Upload"}
                    </Button>
                  </div>
                </form>
              </div>
            </>
          )}

          {/* DEALS */}
          {tab === "deals" && (
            <>
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-lg font-semibold">Latest deals</h3>
                <div className="text-sm text-gray-500">{deals.length} items</div>
              </div>

              {loading ? (
                <div className="grid gap-4">
                  {Array.from({ length: 6 }).map((_, i) => <div key={i} className="animate-pulse bg-card border border-border rounded-lg p-6" />)}
                </div>
              ) : deals.length === 0 ? (
                <div className="bg-card border border-border rounded-lg p-6 text-center text-muted-foreground">No deals found.</div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {deals.map(d => (
                    <article key={d.id} className="bg-card border border-border rounded-lg p-4">
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="text-sm text-gray-500">{d.date ? new Date(d.date).toLocaleDateString() : "—"}</div>
                          <h4 className="text-lg font-semibold">{d.acquirer} <span className="text-gray-400 mx-1">→</span> {d.target}</h4>
                          <div className="mt-2 text-sm text-gray-600">{d.sector} • {d.region}</div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm text-gray-500">Value</div>
                          <div className="font-bold">{d.value ?? "Undisclosed"}</div>
                        </div>
                      </div>
                      <div className="mt-3 flex items-center justify-between">
                        <div className="text-sm text-gray-500">{d.source ? (new URL(d.source).hostname) : ""}</div>
                        {d.source ? <a className="text-sm text-blue-600" href={d.source} target="_blank" rel="noopener noreferrer">Read</a> : <span className="text-sm text-gray-400">No source</span>}
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </>
          )}

          {/* NEWS */}
          {tab === "news" && (
            <>
              {loading ? (
                <div className="grid gap-4">
                  {Array.from({ length: 6 }).map((_, i) => <div key={i} className="animate-pulse bg-card border border-border rounded-lg p-6" />)}
                </div>
              ) : news.length === 0 ? (
                <div className="bg-card border border-border rounded-lg p-6 text-center text-muted-foreground">No news items found.</div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {news.map(n => (
                    <article key={n.id} className="bg-card border border-border rounded-lg p-3 flex flex-col">
                      <div className="flex gap-3">
                        <div className="w-28 h-20 rounded overflow-hidden bg-gray-50 flex items-center justify-center">
                          {n.image ? <img src={n.image} alt={n.title} className="object-cover w-full h-full" /> : <FileText className="w-6 h-6 text-gray-400" />}
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className="text-sm font-semibold truncate">{n.title}</h4>
                          <p className="mt-2 text-sm text-gray-600 line-clamp-3">{n.snippet}</p>
                          <div className="mt-3 flex items-center justify-between">
                            <div className="text-xs text-gray-500">{n.source} • {n.publishedAt ? new Date(n.publishedAt).toLocaleString() : "—"}</div>
                            <div className="flex items-center gap-2">
                              <a href={n.sourceUrl || `https://duckduckgo.com/?q=${encodeURIComponent(n.title)}`} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-600">Read</a>
                              <Button size="sm" variant="ghost" onClick={() => toast({ title: "Raw", description: "Open console to view raw data" })}>Raw</Button>
                            </div>
                          </div>
                        </div>
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </>
          )}
        </div>

        <div className="mt-12 text-center text-xs text-gray-500">
          Data sources: Supabase (notes), Perplexity (deals, proxied), IndianAPI (news, proxied). Manage keys on server environment.
        </div>
      </div>
    </section>
  );
}
