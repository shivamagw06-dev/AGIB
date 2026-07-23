import { createContext, useContext, useEffect, useRef, useState } from 'react';
import { getMarketIntelligence } from '@/api/marketApi';
import {
  MARKET_REFRESH_MS,
  readMarketCache,
  writeMarketCache,
  msUntilNextRefresh,
} from '@/lib/marketCache';

const EMPTY = {
  pulse: null,
  outlook: null,
  insightStrip: [],
  summary: '',
  sectors: [],
  stocksInFocus: [],
  breadth: { label: 'Neutral', advancing: 0, declining: 0 },
  indexSentiments: [],
  disclaimer: '',
};

const MarketDataContext = createContext(null);

/**
 * Market intelligence refreshes every 10 minutes.
 * Session cache prevents API calls on every page load / login within that window.
 */
export function MarketDataProvider({ children, pollMs = MARKET_REFRESH_MS }) {
  const cached = readMarketCache();
  const [intelligence, setIntelligence] = useState(cached ? { ...EMPTY, ...cached } : EMPTY);
  const [loading, setLoading] = useState(!cached);
  const busy = useRef(false);

  useEffect(() => {
    let cancelled = false;
    let intervalId = null;

    async function load(force = false) {
      if (busy.current) return;

      if (!force) {
        const fresh = readMarketCache();
        if (fresh) {
          if (!cancelled) {
            setIntelligence({ ...EMPTY, ...fresh });
            setLoading(false);
          }
          return;
        }
      }

      busy.current = true;
      try {
        const data = await getMarketIntelligence();
        if (!cancelled && data) {
          writeMarketCache(data);
          setIntelligence({ ...EMPTY, ...data });
        }
      } catch {
        /* keep last good data */
      } finally {
        busy.current = false;
        if (!cancelled) setLoading(false);
      }
    }

    const wait = msUntilNextRefresh();
    if (wait > 0) {
      setLoading(false);
      const timeoutId = setTimeout(() => load(true), wait);
      intervalId = setInterval(() => load(true), pollMs);
      return () => {
        cancelled = true;
        clearTimeout(timeoutId);
        clearInterval(intervalId);
      };
    }

    load(true);
    intervalId = setInterval(() => load(true), pollMs);
    return () => {
      cancelled = true;
      clearInterval(intervalId);
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
