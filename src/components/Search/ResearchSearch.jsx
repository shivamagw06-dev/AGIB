import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Search, X } from 'lucide-react';
import { supabase } from '@/lib/supabaseClient';

const FILTERS = ['All', 'Research Notes', 'Company Updates', 'Sector Reports', 'Macro'];

export default function ResearchSearch({ onClose }) {
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState('All');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKey);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = '';
    };
  }, [onClose]);

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      return;
    }

    let cancelled = false;
    const timer = setTimeout(async () => {
      setLoading(true);
      let q = supabase
        .from('articles')
        .select('id, title, slug, excerpt, section, tags, published_at')
        .eq('status', 'published')
        .or(`title.ilike.%${query}%,excerpt.ilike.%${query}%,section.ilike.%${query}%`)
        .order('published_at', { ascending: false })
        .limit(12);

      if (filter !== 'All') q = q.eq('section', filter);

      const { data } = await q;
      if (!cancelled) {
        setResults(data || []);
        setLoading(false);
      }
    }, 300);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [query, filter]);

  const go = (slug) => {
    navigate(`/article/${slug}`);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-[100] bg-black/40 backdrop-blur-sm" onClick={onClose}>
      <div
        className="absolute top-0 inset-x-0 bg-white border-b border-[#ddd] shadow-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="max-w-[720px] mx-auto px-4 py-5">
          <div className="flex items-center gap-3 border border-[#ccc] px-3 py-2.5 focus-within:border-[#111]">
            <Search className="w-5 h-5 text-[#767676] shrink-0" />
            <input
              autoFocus
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search stocks, companies, research, sectors, themes…"
              className="flex-1 text-sm outline-none bg-transparent text-[#111]"
            />
            <button type="button" onClick={onClose} aria-label="Close search">
              <X className="w-5 h-5 text-[#767676]" />
            </button>
          </div>

          <div className="flex flex-wrap gap-2 mt-3">
            {FILTERS.map((f) => (
              <button
                key={f}
                type="button"
                onClick={() => setFilter(f)}
                className={`text-xs px-3 py-1 border transition-colors ${
                  filter === f
                    ? 'bg-[#111] text-white border-[#111]'
                    : 'border-[#ddd] text-[#555] hover:border-[#999]'
                }`}
              >
                {f}
              </button>
            ))}
          </div>

          <div className="mt-4 max-h-[50vh] overflow-y-auto">
            {loading && <p className="text-sm text-[#767676] py-4">Searching…</p>}
            {!loading && query && results.length === 0 && (
              <p className="text-sm text-[#767676] py-4">No results for &ldquo;{query}&rdquo;</p>
            )}
            {results.map((r) => (
              <button
                key={r.id}
                type="button"
                onClick={() => go(r.slug)}
                className="block w-full text-left py-3 border-b border-[#eee] hover:bg-[#fafafa] px-1 group"
              >
                <span className="text-[10px] font-bold uppercase tracking-wide text-[#ff6600]">
                  {r.section || 'Research'}
                </span>
                <p className="text-sm font-bold text-[#111] group-hover:underline mt-0.5">{r.title}</p>
                {r.excerpt && (
                  <p className="text-xs text-[#767676] mt-1 line-clamp-1">{r.excerpt}</p>
                )}
              </button>
            ))}
            {!query && (
              <p className="text-xs text-[#767676] py-4">
                Tip: Search by company name, sector, or research theme.{' '}
                <Link to="/research" onClick={onClose} className="font-bold text-[#111] hover:text-[#ff6600]">
                  Browse all research →
                </Link>
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
