import { useEffect, useState } from 'react';
import { fetchEntity, searchEntities } from '@/lib/intelligencePlatformApi';

export function useIntelligenceEntity(slug, { refresh = false } = {}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(Boolean(slug));
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!slug) return;
    let mounted = true;
    setLoading(true);
    setError(null);
    fetchEntity(slug, { refresh })
      .then((payload) => {
        if (mounted) setData(payload);
      })
      .catch((e) => {
        if (mounted) setError(e.message);
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, [slug, refresh]);

  return { data, loading, error };
}

export function useUniversalSearch(query, { limit = 8, debounceMs = 250 } = {}) {
  const [result, setResult] = useState({ groups: [], total: 0, query: '' });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const q = String(query || '').trim();
    if (q.length < 2) {
      setResult({ groups: [], total: 0, query: q });
      return;
    }
    let mounted = true;
    const timer = setTimeout(() => {
      setLoading(true);
      searchEntities(q, { limit })
        .then((payload) => {
          if (mounted) setResult(payload);
        })
        .catch(() => {
          if (mounted) setResult({ groups: [], total: 0, query: q });
        })
        .finally(() => {
          if (mounted) setLoading(false);
        });
    }, debounceMs);
    return () => {
      mounted = false;
      clearTimeout(timer);
    };
  }, [query, limit, debounceMs]);

  return { ...result, loading };
}
