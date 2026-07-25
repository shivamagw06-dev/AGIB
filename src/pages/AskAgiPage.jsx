import { useEffect, useMemo, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import AskAgiBar from '@/components/Home/AskAgiBar';
import InstitutionalAnswer from '@/components/Search/InstitutionalAnswer';
import { postUiSearch } from '@/lib/uiApi';
import {
  getFavouriteCompanies,
  getRecentSearches,
  getSavedAnswers,
  pushSearch,
  saveAnswer,
  saveSearch,
} from '@/lib/searchHistory';

export default function AskAgiPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const question = (params.get('q') || '').trim();
  const [state, setState] = useState({ loading: false, pack: null, error: null });
  const [savedFlash, setSavedFlash] = useState(false);

  useEffect(() => {
    if (!question) {
      setState({ loading: false, pack: null, error: null });
      return;
    }
    let active = true;
    setState({ loading: true, pack: null, error: null });
    pushSearch(question);
    postUiSearch(question)
      .then((pack) => active && setState({ loading: false, pack, error: null }))
      .catch((error) => active && setState({ loading: false, pack: null, error }));
    return () => {
      active = false;
    };
  }, [question]);

  const onFollowUp = (q) => {
    const next = String(q || '').trim();
    if (!next) return;
    navigate(`/ask?q=${encodeURIComponent(next)}`);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const onSaveAnswer = () => {
    if (!state.pack) return;
    saveAnswer({
      question: state.pack.question || question,
      stance: state.pack.house_view_card?.stance || state.pack.answer?.house_view_label || '',
      summary: state.pack.executive_summary || '',
      href: `/ask?q=${encodeURIComponent(state.pack.question || question)}`,
    });
    saveSearch(state.pack.question || question);
    setSavedFlash(true);
    window.setTimeout(() => setSavedFlash(false), 1600);
  };

  const personalised = useMemo(() => {
    const favs = getFavouriteCompanies().slice(0, 3);
    const recent = getRecentSearches(4);
    const saved = getSavedAnswers(3);
    const recommended = [
      ...favs.map((t) => `What is AGI’s current house view on ${t}?`),
      ...recent.filter((q) => q.toLowerCase() !== question.toLowerCase()).slice(0, 2),
    ].slice(0, 6);
    return { favs, recent, saved, recommended };
  }, [question, state.pack]);

  return (
    <div className="bg-white min-h-screen">
      <Helmet>
        <title>{question ? `${question} | Ask AGI` : 'Ask AGI | Agarwal Global Investments'}</title>
        <meta
          name="description"
          content="Ask AGI — institutional investment intelligence powered by AGI research, knowledge and reasoning."
        />
      </Helmet>

      <div className="sticky top-0 z-20 bg-white/95 backdrop-blur border-b border-[#dddddd]">
        <div className="max-w-[1100px] mx-auto px-4 sm:px-6 py-3">
          <AskAgiBar
            size="compact"
            initialQuery={question}
            autoFocus={!question}
            onAsk={onFollowUp}
            placeholder="Ask a follow-up or a new institutional question…"
          />
        </div>
      </div>

      <div className="max-w-[1100px] mx-auto px-4 sm:px-6 py-8">
        <div className="flex items-center justify-between gap-3 mb-6">
          <Link to="/" className="text-xs font-bold text-[#111] hover:text-[#ff6600]">
            ← Home
          </Link>
          <div className="flex items-center gap-2">
            {savedFlash && (
              <span className="text-[11px] font-bold text-[#087443]">Answer saved</span>
            )}
            {question && (
              <button
                type="button"
                onClick={() => (state.pack ? onSaveAnswer() : saveSearch(question))}
                className="text-xs font-bold border border-[#ddd] px-3 py-1.5 hover:border-[#111]"
              >
                {state.pack ? 'Save answer' : 'Save search'}
              </button>
            )}
          </div>
        </div>

        {!question && (
          <div className="space-y-6">
            <div className="border border-[#dddddd] p-8 text-center">
              <p className="text-[11px] font-bold uppercase tracking-wider text-[#ff6600]">Ask AGI</p>
              <h1 className="mt-2 text-2xl font-bold text-[#111]">Institutional Answer Workspace</h1>
              <p className="mt-2 text-sm text-[#767676] max-w-lg mx-auto">
                Every answer is an investment-committee briefing — house view, evidence, what changed,
                and what to explore next.
              </p>
            </div>

            {(personalised.recommended.length > 0 || personalised.saved.length > 0) && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <section className="border border-[#dddddd] p-5">
                  <p className="text-[10px] font-bold uppercase tracking-wide text-[#767676]">
                    Recommended for you
                  </p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {personalised.recommended.map((q) => (
                      <button
                        key={q}
                        type="button"
                        onClick={() => onFollowUp(q)}
                        className="text-[11px] border border-[#ddd] px-2.5 py-1.5 text-left hover:border-[#111] hover:text-[#ff6600]"
                      >
                        {q}
                      </button>
                    ))}
                    {personalised.recommended.length === 0 && (
                      <p className="text-xs text-[#929292]">Ask a company or theme to personalise this desk.</p>
                    )}
                  </div>
                </section>
                <section className="border border-[#dddddd] p-5">
                  <p className="text-[10px] font-bold uppercase tracking-wide text-[#767676]">
                    Recent & saved
                  </p>
                  <div className="mt-3 space-y-2">
                    {personalised.recent.slice(0, 4).map((q) => (
                      <button
                        key={`r-${q}`}
                        type="button"
                        onClick={() => onFollowUp(q)}
                        className="block w-full text-left text-sm border-b border-[#eee] pb-2 hover:text-[#ff6600]"
                      >
                        {q}
                      </button>
                    ))}
                    {personalised.saved.map((item) => (
                      <button
                        key={item.id}
                        type="button"
                        onClick={() => onFollowUp(item.question)}
                        className="block w-full text-left text-sm border-b border-[#eee] pb-2 hover:text-[#ff6600]"
                      >
                        <span className="text-[10px] font-bold uppercase text-[#ff6600]">Saved · </span>
                        {item.question}
                      </button>
                    ))}
                    {!personalised.recent.length && !personalised.saved.length && (
                      <p className="text-xs text-[#929292]">Your briefing history will appear here.</p>
                    )}
                  </div>
                </section>
              </div>
            )}
          </div>
        )}

        {question && state.loading && (
          <div className="space-y-3" aria-live="polite" aria-busy="true">
            <div className="h-24 bg-[#eee] animate-pulse" />
            <div className="h-40 bg-[#eee] animate-pulse" />
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="h-24 bg-[#eee] animate-pulse" />
              <div className="h-24 bg-[#eee] animate-pulse" />
              <div className="h-24 bg-[#eee] animate-pulse" />
            </div>
          </div>
        )}

        {question && state.error && (
          <div className="border border-[#dddddd] p-6">
            <p className="text-sm font-bold text-[#111]">Desk temporarily unavailable</p>
            <p className="text-xs text-[#767676] mt-2">
              Please try again shortly. Your question was saved in recent searches.
            </p>
          </div>
        )}

        {question && state.pack && (
          <InstitutionalAnswer
            pack={state.pack}
            onFollowUp={onFollowUp}
            onContinue={onFollowUp}
            onSave={onSaveAnswer}
          />
        )}
      </div>
    </div>
  );
}
