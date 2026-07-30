import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import InstitutionalChatWorkspace from '@/components/AskAgi/InstitutionalChatWorkspace';
import { postUiSearch } from '@/lib/uiApi';
import { pushSearch, saveAnswer, saveSearch } from '@/lib/searchHistory';
import { trackProductEvent } from '@/lib/productAnalytics';
import { ASK_PROMPTS } from './helpers';

/**
 * Ask AGI — product homepage experience inside the AGI shell.
 * Reuses the institutional chat workspace; routes stay under /agi/ask.
 */
export default function AskAgiProductPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const question = (params.get('q') || '').trim();
  const [state, setState] = useState({ loading: false, pack: null, error: null });
  const [draft, setDraft] = useState('');
  const [savedFlash, setSavedFlash] = useState(false);

  useEffect(() => {
    if (!question) {
      setState({ loading: false, pack: null, error: null });
      return;
    }
    let active = true;
    setState({ loading: true, pack: null, error: null });
    pushSearch(question);
    trackProductEvent('question_asked', { question, surface: 'agi_product' });
    postUiSearch(question)
      .then((pack) => {
        if (!active) return;
        setState({ loading: false, pack, error: null });
        trackProductEvent('search_success', { question, surface: 'agi_product' });
      })
      .catch((error) => active && setState({ loading: false, pack: null, error }));
    return () => {
      active = false;
    };
  }, [question]);

  const onAsk = (q) => {
    const next = String(q || '').trim();
    if (!next) return;
    trackProductEvent('follow_up_question', { question: next, surface: 'agi_product' });
    navigate(`/agi/ask?q=${encodeURIComponent(next)}`);
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
      href: `/agi/ask?q=${encodeURIComponent(state.pack.question || question)}`,
    });
    saveSearch(state.pack.question || question);
    setSavedFlash(true);
    window.setTimeout(() => setSavedFlash(false), 1600);
  };

  if (!question) {
    return (
      <div className="agi-ask-hero">
        <h1 className="agi-greeting">Ask AGI</h1>
        <p className="agi-lede">
          Bloomberg command meets institutional chat — confidence, evidence, timeline, and drill-down in every
          answer.
        </p>
        <form
          className="agi-ask-input-wrap"
          onSubmit={(e) => {
            e.preventDefault();
            onAsk(draft);
          }}
        >
          <input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Ask about a company, market, or idea…"
            aria-label="Ask AGI"
            autoFocus
          />
          <button type="submit" className="agi-btn agi-btn-primary">
            Ask
          </button>
        </form>
        <div className="agi-prompts">
          {ASK_PROMPTS.map((p) => (
            <button key={p} type="button" onClick={() => onAsk(p)}>
              {p}
            </button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div style={{ margin: '0 -0.5rem' }}>
      <InstitutionalChatWorkspace
        pack={state.pack}
        loading={Boolean(question && state.loading)}
        error={state.error}
        question={question}
        onAsk={onAsk}
        onSave={onSaveAnswer}
        savedFlash={savedFlash}
        embedded
        basePath="/agi/ask"
      />
    </div>
  );
}
