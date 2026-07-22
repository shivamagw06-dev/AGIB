import { createContext, useContext, useEffect, useRef, useState } from 'react';
import { getMarketIntelligence } from '@/api/marketApi';

const EMPTY = {
  pulse: null,
  outlook: null,
  insightStrip: [],
  summary: '',
  sectors: [],
  stocksInFocus: [],
  breadth: { label: 'Neutral', advancing: 0, declining: 0 },
  disclaimer: '',
};

const MarketDataContext = createContext(null);

/** Single fetch for AGI Market Intelligence — no raw exchange data */
export function MarketDataProvider({ children, pollMs = 300_000 }) {
  const [intelligence, setIntelligence] = useState(EMPTY);
  const [loading, setLoading] = useState(true);
  const busy = useRef(false);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      if (busy.current) return;
      busy.current = true;
      try {
        const data = await getMarketIntelligence();
        if (!cancelled && data) setIntelligence({ ...EMPTY, ...data });
      } catch {
        /* keep last good data */
      } finally {
        busy.current = false;
        if (!cancelled) setLoading(false);
      }
    }

    load();
    const id = setInterval(load, pollMs);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [pollMs]);

  return (
    <MarketDataContext.Provider value={{ intelligence, loading }}>
      {children}
    </MarketDataContext.Provider>
  );
}

export function useMarketDataContext() {
  const ctx = useContext(MarketDataContext);
  if (!ctx) throw new Error('useMarketDataContext requires MarketDataProvider');
  return ctx;
}
