import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { Clock3, ArrowLeft } from 'lucide-react';
import { supabase } from '@/lib/supabaseClient';
import useCategories from '@/hooks/useCategories';
import { formatArticleDate } from '@/lib/articleUtils';

export default function CategoryPage() {
  const { slug } = useParams();
  const { categories } = useCategories();
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);

  const category = categories.find((c) => c.slug === slug);

  useEffect(() => {
    if (!slug) return;
    let cancelled = false;

    (async () => {
      setLoading(true);
      const categoryName = category?.name || slug.replace(/-/g, ' ');

      const { data, error } = await supabase
        .from('articles')
        .select('id, title, slug, excerpt, cover_url, section, tags, published_at')
        .eq('status', 'published')
        .eq('section', categoryName)
        .order('published_at', { ascending: false })
        .limit(48);

      if (cancelled) return;

      if (!error && data?.length) {
        setArticles(data);
      } else {
        const { data: fallback } = await supabase
          .from('articles')
          .select('id, title, slug, excerpt, cover_url, section, tags, published_at')
          .eq('status', 'published')
          .ilike('section', `%${categoryName}%`)
          .order('published_at', { ascending: false })
          .limit(48);

        if (!cancelled) setArticles(fallback || []);
      }

      setLoading(false);
    })();

    return () => {
      cancelled = true;
    };
  }, [slug, category?.name]);

  const title = category?.name || slug?.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <div className="bg-slate-950 min-h-screen">
      <Helmet>
        <title>{title} | Agarwal Global Investments</title>
        <meta name="description" content={category?.description || `Browse ${title} articles and market updates.`} />
      </Helmet>

      <div className="max-w-7xl mx-auto px-6 py-16">
        <Link to="/" className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white mb-8 transition-colors">
          <ArrowLeft size={16} /> Back to Home
        </Link>

        <span className="text-blue-400 text-sm font-semibold uppercase tracking-widest">{title}</span>
        <h1 className="mt-3 text-4xl md:text-5xl font-bold text-white">{title}</h1>
        {category?.description && (
          <p className="mt-4 text-slate-400 text-lg max-w-3xl">{category.description}</p>
        )}

        {loading ? (
          <p className="mt-16 text-slate-500 text-center">Loading articles…</p>
        ) : articles.length === 0 ? (
          <div className="mt-16 text-center py-16 rounded-2xl border border-white/10 bg-white/5">
            <p className="text-slate-400">No published articles in this category yet.</p>
            <p className="text-slate-500 text-sm mt-2">Check back soon for new updates.</p>
          </div>
        ) : (
          <div className="mt-12 grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {articles.map((article) => (
              <Link
                key={article.id}
                to={`/article/${article.slug}`}
                className="group rounded-2xl border border-white/10 bg-white/5 overflow-hidden hover:border-blue-500/40 transition-all"
              >
                {article.cover_url && (
                  <img src={article.cover_url} alt="" className="w-full h-44 object-cover" />
                )}
                <div className="p-6">
                  <span className="text-blue-400 text-xs font-medium">{article.section}</span>
                  <h2 className="mt-2 text-xl font-semibold text-white group-hover:text-blue-300 transition-colors line-clamp-2">
                    {article.title}
                  </h2>
                  {article.excerpt && (
                    <p className="mt-3 text-slate-400 text-sm line-clamp-3 leading-relaxed">{article.excerpt}</p>
                  )}
                  <div className="mt-4 flex items-center gap-1.5 text-xs text-slate-500">
                    <Clock3 size={13} />
                    {formatArticleDate(article.published_at)}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
