import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Search, X } from 'lucide-react';
import { supabase } from '@/lib/supabaseClient';
import { postUiSearch } from '@/lib/uiApi';

const FILTERS = ['All', 'Research Notes', 'Company Updates', 'Sector Reports', 'Macro'];

function looksLikeQuestion(q) {
  const t = (q || '').trim();
  if (!t) return false;
  if (/\?$/.test(t)) return true;
  return /\b(should i|buy|sell|hold|what is|house view|view on|risk|catalyst|compare)\b/i.test(t);
}

export default function ResearchSearch({ onClose }) {
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState('All');
  const [results, setResults] = useState([]);
  const [intel, setIntel] = useState(null);
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
      setIntel(null);
      return;
    }

    let cancelled = false;
    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const articlePromise = (async () => {
          let q = supabase
            .from('articles')
            .select('id, title, slug, excerpt, section, tags, published_at')
            .eq('status', 'published')
            .or(`title.ilike.%${query}%,excerpt.ilike.%${query}%,section.ilike.%${query}%`)
            .order('published_at', { ascending: false })
            .limit(12);
          if (filter !== 'All') q = q.eq('section', filter);
          const { data } = await q;
          return data || [];
        })();

        const intelPromise = looksLikeQuestion(query) || query.trim().length >= 3
          ? postUiSearch(query.trim()).catch(() => null)
          : Promise.resolve(null);

        const [articles, pack] = await Promise.all([articlePromise, intelPromise]);
        if (!cancelled) {
          setResults(articles);
          setIntel(pack);
          setLoading(false);
        }
      } catch {
        if (!cancelled) {
          setResults([]);
          setIntel(null);
          setLoading(false);
        }
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

  const goCompany = (ticker) => {
    navigate(`/research/stocks/${encodeURIComponent(ticker)}`);
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
              placeholder="Ask AGI — e.g. Should I buy ICICI Bank?"
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

          <div className="mt-4 max-h-[60vh] overflow-y-auto">
            {loading && <p className="text-sm text-[#767676] py-4">Searching institutional desk…</p>}

            {!loading && intel && (
              <div className="mb-4 border border-[#dddddd] p-4 bg-[#fafafa]">
                <p className="text-[10px] font-bold uppercase tracking-wide text-[#ff6600]">Institutional Answer Pack</p>
                <p className="text-sm text-[#333] mt-2 leading-relaxed">{intel.answer?.summary}</p>
                <div className="grid grid-cols-2 gap-3 mt-4">
                  <div className="border border-[#eeeeee] bg-white p-3">
                    <p className="text-[10px] font-bold uppercase text-[#767676]">House View</p>
                    <p className="text-sm font-bold text-[#111] mt-1">
                      {intel.answer?.house_view_label || intel.house_view?.current_view || intel.house_view?.stance || 'Under review'}
                    </p>
                  </div>
                  <div className="border border-[#eeeeee] bg-white p-3">
                    <p className="text-[10px] font-bold uppercase text-[#767676]">Confidence</p>
                    <p className="text-sm font-bold text-[#111] mt-1">
                      {intel.confidence != null ? `${Math.round(Number(intel.confidence) * (Number(intel.confidence) <= 1 ? 100 : 1))}%` : '—'}
                    </p>
                  </div>
                </div>

                {(intel.related_companies || []).length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {intel.related_companies.map((t) => (
                      <button
                        key={t}
                        type="button"
                        onClick={() => goCompany(t)}
                        className="text-[11px] font-bold border border-[#ddd] px-2 py-1 hover:border-[#111] hover:text-[#ff6600]"
                      >
                        {t}
                      </button>
                    ))}
                  </div>
                )}

                {(intel.supporting_research || []).length > 0 && (
                  <div className="mt-4">
                    <p className="text-[10px] font-bold uppercase text-[#767676] mb-2">Supporting Research</p>
                    <ul className="space-y-2">
                      {intel.supporting_research.slice(0, 4).map((r, idx) => (
                        <li key={r.id || r.title || idx} className="text-xs text-[#333] border-b border-[#eee] pb-1">
                          {r.title || r.id || String(r)}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {(intel.conflicting_opinions || []).length > 0 && (
                  <div className="mt-3">
                    <p className="text-[10px] font-bold uppercase text-[#767676] mb-1">Conflicting Opinions</p>
                    <p className="text-xs text-[#555]">
                      {intel.conflicting_opinions.length} conflicting items in evidence pack
                    </p>
                  </div>
                )}

                {(intel.follow_up_questions || []).length > 0 && (
                  <div className="mt-4 flex flex-wrap gap-2">
                    {intel.follow_up_questions.slice(0, 3).map((fq) => (
                      <button
                        key={fq}
                        type="button"
                        onClick={() => setQuery(fq)}
                        className="text-[11px] border border-[#ddd] px-2 py-1 text-[#555] hover:border-[#111]"
                      >
                        {fq}
                      </button>
                    ))}
                  </div>
                )}
                <p className="text-[10px] text-[#929292] mt-3">
                  Evidence pack only — not investment advice. Internal model names are never shown.
                </p>
              </div>
            )}

            {!loading && query && results.length === 0 && !intel && (
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
                Tip: Ask a research question, or search by company, sector, or theme.{' '}
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
