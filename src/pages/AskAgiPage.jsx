import { useEffect, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { useNavigate, useSearchParams } from 'react-router-dom';
import ResearchWorkspace from '@/components/AskAgi/ResearchWorkspace';
import { postUiSearch } from '@/lib/uiApi';
import { pushSearch, saveAnswer, saveSearch } from '@/lib/searchHistory';
import { trackProductEvent } from '@/lib/productAnalytics';

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
    trackProductEvent('question_asked', { question });
    postUiSearch(question)
      .then((pack) => {
        if (!active) return;
        setState({ loading: false, pack, error: null });
        trackProductEvent('search_success', { question });
      })
      .catch((error) => active && setState({ loading: false, pack: null, error }));
    return () => {
      active = false;
    };
  }, [question]);

  const onAsk = (q) => {
    const next = String(q || '').trim();
    if (!next) return;
    trackProductEvent('follow_up_question', { question: next });
    navigate(`/ask?q=${encodeURIComponent(next)}`);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const onSaveAnswer = () => {
    if (!state.pack) {
      if (question) saveSearch(question);
      return;
    }
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

  return (
    <>
      <Helmet>
        <title>{question ? `${question} | Ask AGI` : 'Ask AGI | Agarwal Global Investments'}</title>
        <meta
          name="description"
          content="Ask AGI — institutional investment research workspace powered by AGI intelligence."
        />
      </Helmet>
      <ResearchWorkspace
        pack={state.pack}
        loading={Boolean(question && state.loading)}
        error={state.error}
        question={question}
        onAsk={onAsk}
        onSave={onSaveAnswer}
        savedFlash={savedFlash}
      />
    </>
  );
}
