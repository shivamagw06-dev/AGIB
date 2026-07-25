import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Search, X } from 'lucide-react';
import AskAgiBar from '@/components/Home/AskAgiBar';
import { getRecentSearches } from '@/lib/searchHistory';

const EXAMPLES = [
  'Should I invest in ICICI Bank?',
  "What is AGI's current market view?",
  'Which sectors benefit from lower interest rates?',
  'Compare HDFC Bank vs ICICI Bank.',
];

export default function ResearchSearch({ onClose }) {
  const navigate = useNavigate();
  const [recent, setRecent] = useState([]);

  useEffect(() => {
    setRecent(getRecentSearches());
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

  return (
    <div className="fixed inset-0 z-[100] bg-black/40 backdrop-blur-sm" onClick={onClose}>
      <div
        className="absolute top-0 inset-x-0 bg-white border-b border-[#ddd] shadow-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="max-w-[720px] mx-auto px-4 py-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Search className="w-4 h-4 text-[#ff6600]" />
              <p className="text-[11px] font-bold uppercase tracking-wider text-[#ff6600]">Ask AGI</p>
            </div>
            <button type="button" onClick={onClose} aria-label="Close search">
              <X className="w-5 h-5 text-[#767676]" />
            </button>
          </div>

          <AskAgiBar
            autoFocus
            examples={EXAMPLES}
            placeholder="Ask AGI anything about markets, companies, sectors, investing or the economy..."
          />

          <div className="mt-5">
            <p className="text-[10px] font-bold uppercase tracking-wide text-[#767676] mb-2">
              Popular questions
            </p>
            <div className="flex flex-wrap gap-2">
              {EXAMPLES.map((q) => (
                <button
                  key={q}
                  type="button"
                  onClick={() => {
                    onClose();
                    navigate(`/ask?q=${encodeURIComponent(q)}`);
                  }}
                  className="text-[11px] border border-[#ddd] px-3 py-1.5 hover:border-[#111] hover:text-[#ff6600]"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>

          {recent.length > 0 && (
            <div className="mt-5">
              <p className="text-[10px] font-bold uppercase tracking-wide text-[#767676] mb-2">
                Recent searches
              </p>
              <div className="flex flex-wrap gap-2">
                {recent.map((q) => (
                  <button
                    key={q}
                    type="button"
                    onClick={() => {
                      onClose();
                      navigate(`/ask?q=${encodeURIComponent(q)}`);
                    }}
                    className="text-[11px] border border-[#ddd] px-3 py-1.5 hover:border-[#111]"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          <p className="text-xs text-[#767676] mt-5">
            Browse the library instead?{' '}
            <Link to="/research" onClick={onClose} className="font-bold text-[#111] hover:text-[#ff6600]">
              All research →
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
