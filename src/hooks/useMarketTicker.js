import { useEffect, useState } from 'react';
import { getMarketTicker } from '@/api/marketApi';
import { getIndices } from '@/api/indianApi';

const FALLBACK = [
  { name: 'NIFTY 50', price: null, change: null, percentChange: null },
  { name: 'BANK NIFTY', price: null, change: null, percentChange: null },
  { name: 'USD/INR', price: null, change: null, percentChange: null },
  { name: 'GOLD', price: null, change: null, percentChange: null },
  { name: 'INDIA VIX', price: null, change: null, percentChange: null },
];

export default function useMarketTicker(pollMs = 60_000) {
  const [items, setItems] = useState(FALLBACK);
  const [loading, setLoading] = useState(true);
  const [source, setSource] = useState('fallback');

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const data = await getMarketTicker();
        if (cancelled) return;
        if (data?.items?.length) {
          setItems(data.items);
          setSource(data.source || 'market');
        }
      } catch {
        try {
          const legacy = await getIndices();
          if (cancelled) return;
          const list = (legacy?.indices || []).map((idx) => ({
            name: idx.name,
            price: idx.price ?? idx.value,
            change: idx.change,
            percentChange: idx.percentChange ?? idx.change,
          }));
          if (list.length) setItems(list);
        } catch {
          if (!cancelled) setItems(FALLBACK);
        }
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

  return { items, loading, source };
}
