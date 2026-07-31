import { useEffect, useState } from 'react';
import { getUiHome } from '@/lib/uiApi';
import { getMarketCycleId, msUntilNextMarketCycle, MARKET_REFRESH_MS } from '@/lib/marketCache';

const STORAGE_KEY = 'agi_market_snapshot_v1';
const STORAGE_CYCLE_KEY = 'agi_market_snapshot_v1_cycle';

function readCache() {
  try {
    const cycleId = sessionStorage.getItem(STORAGE_CYCLE_KEY);
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw || !cycleId || cycleId !== getMarketCycleId()) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function writeCache(items) {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(items));
    sessionStorage.setItem(STORAGE_CYCLE_KEY, getMarketCycleId());
  } catch {
    /* quota / private mode */
  }
}

/**
 * Live market strip quotes from /api/ui/home market_snapshot
 * (Groww / NSE / Yahoo — real prices, not AGI sentiment scores).
 */
export default function useMarketSnapshot() {
  const cached = readCache();
  const [items, setItems] = useState(Array.isArray(cached) ? cached : []);
  const [loading, setLoading] = useState(!cached?.length);

  useEffect(() => {
    let cancelled = false;
    let timeoutId = null;

    async function load(force = false) {
      if (!force) {
        const fresh = readCache();
        if (fresh?.length) {
          if (!cancelled) {
            setItems(fresh);
            setLoading(false);
          }
          return;
        }
      }
      try {
        const data = await getUiHome();
        const snap = Array.isArray(data?.market_snapshot) ? data.market_snapshot : [];
        const live = snap.filter((row) => Number(row?.price) > 0);
        if (!cancelled) {
          writeCache(live);
          setItems(live);
        }
      } catch {
        /* keep last good */
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    function scheduleNext() {
      const wait = Math.max(250, Math.min(msUntilNextMarketCycle(), MARKET_REFRESH_MS));
      timeoutId = setTimeout(async () => {
        await load(true);
        if (!cancelled) scheduleNext();
      }, wait);
    }

    load(false).then(() => {
      if (!cancelled) scheduleNext();
    });

    return () => {
      cancelled = true;
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, []);

  return { items, loading };
}
