import { useEffect, useState } from 'react';
import { getMarketDashboard } from '@/api/marketApi';

const EMPTY = {
  pulse: null,
  outlook: null,
  gainers: [],
  losers: [],
  breadth: { gainers: 0, losers: 0, label: 'Mixed' },
  stocksInFocus: [],
};

export default function useMarketDashboard(pollMs = 120_000) {
  const [data, setData] = useState(EMPTY);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const dashboard = await getMarketDashboard();
        if (cancelled) return;
        setData({ ...EMPTY, ...dashboard });
      } catch {
        if (!cancelled) setData(EMPTY);
      } finally {
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

  return { ...data, loading };
}
