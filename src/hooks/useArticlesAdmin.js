import { useCallback, useEffect, useState } from 'react';
import { supabase } from '@/lib/supabaseClient';

export default function useArticlesAdmin() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);

    const { data, error: fetchError } = await supabase
      .from('articles')
      .select('id, title, slug, section, excerpt, status, published_at, created_at, cover_url, tags')
      .order('created_at', { ascending: false });

    if (fetchError) {
      setError(fetchError.message);
      setArticles([]);
    } else {
      setArticles(data || []);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const deleteArticle = async (id) => {
    const { error: deleteError } = await supabase.from('articles').delete().eq('id', id);
    if (deleteError) throw deleteError;
    await load();
  };

  const stats = {
    total: articles.length,
    published: articles.filter((a) => a.status === 'published').length,
    drafts: articles.filter((a) => a.status === 'draft').length,
  };

  return { articles, loading, error, reload: load, deleteArticle, stats };
}
