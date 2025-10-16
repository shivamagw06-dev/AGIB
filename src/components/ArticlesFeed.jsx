import React, { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { Calendar, Clock, ArrowRight, Bookmark } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/use-toast';
import { useAuth } from '@/contexts/AuthContext';
import { supabase } from '@/lib/supabaseClient';

const DEFAULT_CATEGORIES = ['All', 'Finance', 'Economics', 'Private Equity', 'M&A', 'Global Markets'];

/**
 * Props:
 *   section?: string  -> filters by articles.section in DB (e.g., 'Research Notes')
 */
export default function ArticlesFeed({ section }) {
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);

  const { toast } = useToast();
  const { user } = useAuth();

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setLoading(true);
      // Build the query
      let query = supabase
        .from('articles')
        .select('id,title,slug,excerpt,cover_url,tags,published_at,section,status')
        .eq('status', 'published')
        .order('published_at', { ascending: false })
        .limit(36);

      if (section) query = query.eq('section', section);

      const { data, error } = await query;
      if (cancelled) return;

      if (error) {
        console.error(error);
        toast({ title: 'Failed to load articles', description: error.message, variant: 'destructive' });
        setArticles([]);
      } else {
        // Normalize for UI
        const mapped = (data || []).map((a) => ({
          id: a.id,
          title: a.title,
          excerpt: a.excerpt,
          slug: a.slug,
          image: a.cover_url || 'https://images.unsplash.com/photo-1595872018818-97555653a011',
          // Use first tag as the “category chip”; otherwise fallback to section
          category: Array.isArray(a.tags) && a.tags.length ? a.tags[0] : a.section || 'General',
          date: a.published_at,
          readTime: estimateReadTime(a.excerpt), // quick estimate from excerpt length
        }));
        setArticles(mapped);
      }
      setLoading(false);
    };

    load();
    return () => { cancelled = true; };
  }, [section, toast]);

  // Build categories set from data + defaults
  const categories = useMemo(() => {
    const set = new Set(DEFAULT_CATEGORIES);
    articles.forEach((a) => set.add(a.category));
    return Array.from(set);
  }, [articles]);

  const filteredArticles =
    selectedCategory === 'All'
      ? articles
      : articles.filter((a) => a.category === selectedCategory);

  const handleAction = (feature) => {
    if (!user) {
      toast({
        title: 'Authentication Required',
        description: 'Please log in to use this feature.',
        duration: 5000,
      });
      return;
    }
    toast({
      title: `🚧 ${feature} coming soon`,
      description: 'We’ll wire this next.',
      duration: 3000,
    });
  };

  return (
    <section id="articles" className="py-20 bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Heading */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-12"
        >
          <h2 className="text-3xl sm:text-4xl font-bold text-foreground mb-4">
            Latest Insights & Analysis
          </h2>
          <p className="text-lg text-foreground/70 max-w-2xl mx-auto">
            Stay informed with our expert commentary on global finance and investment trends
          </p>
        </motion.div>

        {/* Category chips */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.2 }}
          className="flex flex-wrap justify-center gap-3 mb-12"
        >
          {categories.map((category) => (
            <Button
              key={category}
              variant={selectedCategory === category ? 'default' : 'outline'}
              onClick={() => setSelectedCategory(category)}
              className="transition-all"
            >
              {category}
            </Button>
          ))}
        </motion.div>

        {/* Grid */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-72 rounded-lg bg-muted animate-pulse" />
            ))}
          </div>
        ) : filteredArticles.length === 0 ? (
          <p className="text-center text-muted-foreground">No articles yet.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {filteredArticles.map((article, index) => (
              <motion.article
                key={article.id}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.05 }}
                className="bg-card border border-border rounded-lg overflow-hidden hover:shadow-lg transition-shadow group flex flex-col"
              >
                <a href={`/article/${article.slug}`} className="block">
                  <div className="aspect-video bg-muted relative overflow-hidden">
                    <img
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      alt={article.title}
                      src={article.image}
                    />
                    <div className="absolute top-4 left-4">
                      <span className="bg-primary text-primary-foreground text-xs font-semibold px-3 py-1 rounded-full">
                        {article.category}
                      </span>
                    </div>
                  </div>
                </a>

                <div className="p-6 flex flex-col flex-grow">
                  <div className="flex items-center gap-4 text-sm text-muted-foreground mb-3">
                    <div className="flex items-center gap-1">
                      <Calendar className="h-4 w-4" />
                      <span>{formatDate(article.date)}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Clock className="h-4 w-4" />
                      <span>{article.readTime}</span>
                    </div>
                  </div>

                  <a href={`/article/${article.slug}`} className="group">
                    <h3 className="text-xl font-bold text-card-foreground mb-3 group-hover:text-primary transition-colors">
                      {article.title}
                    </h3>
                  </a>

                  <p className="text-muted-foreground mb-4 line-clamp-3 flex-grow">
                    {article.excerpt}
                  </p>

                  <div className="mt-auto flex justify-between items-center">
                    <a
                      href={`/article/${article.slug}`}
                      className="text-primary hover:text-primary/90 hover:bg-accent p-0 h-auto font-semibold inline-flex items-center"
                    >
                      Read More
                      <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
                    </a>
                    <Button variant="ghost" size="icon" onClick={() => handleAction('Bookmark')}>
                      <Bookmark className="h-5 w-5 text-muted-foreground hover:text-primary transition-colors" />
                    </Button>
                  </div>
                </div>
              </motion.article>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

/* —— utils —— */
function formatDate(d) {
  try {
    return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  } catch {
    return '';
  }
}
function estimateReadTime(text = '') {
  const words = (text || '').split(/\s+/).filter(Boolean).length;
  const mins = Math.max(3, Math.round(words / 200)); // ~200 wpm, min 3 mins
  return `${mins} min read`;
}
