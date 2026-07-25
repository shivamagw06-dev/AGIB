import { useEffect, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import AskAgiBar from '@/components/Home/AskAgiBar';
import InstitutionalAnswer from '@/components/Search/InstitutionalAnswer';
import { postUiSearch } from '@/lib/uiApi';
import { pushSearch, saveSearch } from '@/lib/searchHistory';

export default function AskAgiPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const question = (params.get('q') || '').trim();
  const [state, setState] = useState({ loading: false, pack: null, error: null });

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
    navigate(`/ask?q=${encodeURIComponent(q)}`);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

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
        <div className="max-w-[900px] mx-auto px-4 sm:px-6 py-3">
          <AskAgiBar size="compact" initialQuery={question} autoFocus={!question} />
        </div>
      </div>

      <div className="max-w-[900px] mx-auto px-4 sm:px-6 py-8">
        <div className="flex items-center justify-between gap-3 mb-6">
          <Link to="/" className="text-xs font-bold text-[#111] hover:text-[#ff6600]">
            ← Home
          </Link>
          {question && (
            <button
              type="button"
              onClick={() => saveSearch(question)}
              className="text-xs font-bold border border-[#ddd] px-3 py-1.5 hover:border-[#111]"
            >
              Save search
            </button>
          )}
        </div>

        {!question && (
          <div className="border border-[#dddddd] p-8 text-center">
            <p className="text-[11px] font-bold uppercase tracking-wider text-[#ff6600]">Ask AGI</p>
            <h1 className="mt-2 text-2xl font-bold text-[#111]">Talk to the Investment Office</h1>
            <p className="mt-2 text-sm text-[#767676] max-w-lg mx-auto">
              Ask about companies, sectors, themes, macro policy, valuation or today&apos;s market.
              Every answer is an evidence pack — not a chatbot reply.
            </p>
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
          <InstitutionalAnswer pack={state.pack} onFollowUp={onFollowUp} />
        )}
      </div>
    </div>
  );
}
