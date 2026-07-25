/**
 * Keeps research articles connected to the knowledge graph.
 * Lazy-loaded companion panel — same editorial borders/type.
 */
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getUiArticle, getUiCopilot } from '@/lib/uiApi';

export default function ArticleKnowledgePanel({ researchId, ticker, title }) {
  const [pack, setPack] = useState(null);

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        if (researchId) {
          const data = await getUiArticle(researchId, ticker || undefined);
          if (active) setPack(data);
          return;
        }
        const ctx = await getUiCopilot({
          page: 'research',
          question: title || 'Related institutional context',
          ticker: ticker || undefined,
        });
        if (active) {
          setPack({
            related_companies: ctx.context?.house_view?.ticker
              ? [ctx.context.house_view.ticker]
              : ticker
                ? [ticker]
                : [],
            related_themes: [],
            related_research: [],
            related_sectors: [],
            latest_updates: ctx.context?.latest_news || [],
            previous_agi_articles: [],
            research_timeline: [],
            house_view: ctx.context?.house_view,
            confidence: ctx.context?.house_view?.confidence,
            supporting_evidence: [],
          });
        }
      } catch {
        if (active) setPack(null);
      }
    };
    load();
    return () => {
      active = false;
    };
  }, [researchId, ticker, title]);

  if (!pack) return null;

  const houseLabel =
    pack.house_view?.current_view ||
    pack.house_view?.stance ||
    pack.house_view?.label;

  return (
    <aside className="mt-10 border-t border-[#dddddd] pt-8">
      <h2 className="text-lg font-bold text-[#111111]">Institutional Context</h2>
      <p className="text-xs text-[#767676] mt-1">Every article is connected to the AGI knowledge graph.</p>

      <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="border border-[#dddddd] p-3">
          <p className="text-[10px] font-bold uppercase text-[#767676]">Current House View</p>
          <p className="mt-1 text-sm font-bold text-[#111]">{houseLabel || 'Under review'}</p>
        </div>
        <div className="border border-[#dddddd] p-3">
          <p className="text-[10px] font-bold uppercase text-[#767676]">Confidence</p>
          <p className="mt-1 text-sm font-bold text-[#111]">
            {pack.confidence != null
              ? `${Math.round(Number(pack.confidence) * (Number(pack.confidence) <= 1 ? 100 : 1))}%`
              : '—'}
          </p>
        </div>
        <div className="border border-[#dddddd] p-3">
          <Link
            to={`/ask?q=${encodeURIComponent(title ? `Summarise: ${title}` : 'Summarise today\'s research')}`}
            className="text-xs font-bold text-[#111] hover:text-[#ff6600]"
          >
            Ask AGI about this article →
          </Link>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {(pack.related_companies || []).map((t) => (
          <Link key={t} to={`/research/stocks/${encodeURIComponent(t)}`} className="text-[11px] font-bold border border-[#ddd] px-2 py-1 hover:text-[#ff6600]">
            {t}
          </Link>
        ))}
        {(pack.related_themes || []).map((t) => (
          <Link key={t} to={`/themes/${encodeURIComponent(t)}`} className="text-[11px] font-bold border border-[#ddd] px-2 py-1 hover:text-[#ff6600]">
            Theme: {t}
          </Link>
        ))}
      </div>

      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
        {[
          ['Previous AGI Articles', pack.previous_agi_articles],
          ['Latest Updates Since Publication', pack.latest_updates],
          ['Research Timeline', pack.research_timeline],
          ['Supporting Evidence', pack.supporting_evidence],
        ].map(([label, items]) => (
          <section key={label} className="border border-[#dddddd] p-4">
            <h3 className="text-xs font-bold uppercase tracking-wide text-[#767676]">{label}</h3>
            <ul className="mt-3 space-y-2">
              {(items || []).slice(0, 5).map((item, idx) => (
                <li key={item.id || item.title || idx} className="text-xs text-[#333] border-b border-[#eee] pb-1">
                  {item.title || item.id || String(item)}
                </li>
              ))}
              {(items || []).length === 0 && (
                <li className="text-xs text-[#929292]">No linked items yet.</li>
              )}
            </ul>
          </section>
        ))}
      </div>
    </aside>
  );
}
