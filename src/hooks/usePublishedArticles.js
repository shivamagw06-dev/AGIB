import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabaseClient';
import { mapArticleForCard } from '@/lib/articleUtils';

export default function usePublishedArticles({
  limit = 6,
  excludeSlug = null,
  section = null,
  offset = 0,
} = {}) {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);

      let query = supabase
        .from('articles')
        .select('id, title, slug, excerpt, cover_url, tags, published_at, section, status')
        .eq('status', 'published')
        .order('published_at', { ascending: false })
        .range(offset, offset + limit + (excludeSlug ? 1 : 0) - 1);

      if (section) query = query.eq('section', section);

      const { data, error: fetchError } = await query;
      if (cancelled) return;

      if (fetchError) {
        console.error('Failed to load articles:', fetchError);
        setArticles([]);
        setError(fetchError.message);
      } else {
        const mapped = (data || [])
          .filter((row) => !excludeSlug || row.slug !== excludeSlug)
          .slice(0, limit)
          .map(mapArticleForCard)
          .filter(Boolean);
        setArticles(mapped);
      }

      setLoading(false);
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [limit, excludeSlug, section, offset]);

  return { articles, loading, error };
}
