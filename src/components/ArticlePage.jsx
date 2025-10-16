// src/components/ArticlePage.jsx
import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async'; // <- use react-helmet-async
import DOMPurify from 'dompurify';
import { supabase } from '@/lib/supabaseClient';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';

function readingTimeFromHTML(html = '') {
  const text = String(html).replace(/<[^>]*>/g, ' ');
  const words = text.split(/\s+/).filter(Boolean).length;
  return Math.max(3, Math.round(words / 200));
}

export default function ArticlePage() {
  const { slug: rawSlug } = useParams();
  const slug = decodeURIComponent((rawSlug || '').trim());
  const { user } = useAuth();
  const navigate = useNavigate();

  const [article, setArticle] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let ignore = false;
    (async () => {
      setLoading(true);

      const baseSelect =
        'id, title, slug, section, excerpt, cover_url, content, content_md, tags, status, published_at, author_id, created_at';

      let { data, error } = await supabase
        .from('articles')
        .select(baseSelect)
        .eq('slug', slug)
        .eq('status', 'published')
        .maybeSingle();

      if ((!data || error) && user?.id) {
        const { data: authorData } = await supabase
          .from('articles')
          .select(baseSelect)
          .eq('slug', slug)
          .eq('author_id', user.id)
          .maybeSingle();
        if (authorData) data = authorData;
      }

      if (!ignore) {
        setArticle(data || null);
        setLoading(false);
      }
    })();

    return () => {
      ignore = true;
    };
  }, [slug, user?.id]);

  const htmlToUse = article ? (article.content ?? article.content_md ?? '') : '';
  const minutes = useMemo(() => readingTimeFromHTML(htmlToUse), [htmlToUse]);

  async function deleteArticle() {
    if (!article) return;
    if (!window.confirm('Delete this article? This cannot be undone.')) return;

    const { error } = await supabase
      .from('articles')
      .delete()
      .eq('id', article.id)
      .eq('author_id', user?.id);

    if (error) alert('Delete failed: ' + error.message);
    else navigate('/');
  }

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-16">
        <p className="text-muted-foreground">Loading…</p>
      </div>
    );
  }

  if (!article) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-16">
        <p className="mb-4 font-semibold">Article not found</p>
        <p className="text-sm text-muted-foreground mb-4">
          Tried slug: <code>{slug}</code>
        </p>
        <Button onClick={() => navigate('/')}>Go Home</Button>
      </div>
    );
  }

  const pubDate = article.published_at ?? article.created_at;
  const isoPubDate = pubDate ? new Date(pubDate).toISOString() : null;
  const niceDate = pubDate
    ? new Date(pubDate).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      })
    : '';
  // build a canonical share URL (works client-side)
  const shareUrl = typeof window !== 'undefined'
    ? window.location.href
    : `https://agarwalglobalinvestments.com/article/${article.slug}`;

  const title = article.title || 'Article';
  const description = article.excerpt || (htmlToUse ? String(htmlToUse).replace(/<[^>]*>/g, ' ').slice(0, 160) : 'AGI article');
  const image = article.cover_url || 'https://agarwalglobalinvestments.com/assets/og-image.png';
  const siteName = 'Agarwal Global Investments';
  const canonical = `https://agarwalglobalinvestments.com/article/${article.slug}`;

  const sanitizedHtml = DOMPurify.sanitize(htmlToUse);

  // JSON-LD for Article schema (helps SEO & some crawlers)
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Article",
    "mainEntityOfPage": {
      "@type": "WebPage",
      "@id": canonical
    },
    "headline": title,
    "image": [image],
    "datePublished": isoPubDate,
    "author": {
      "@type": "Person",
      "name": "Shivam Agarwal"
    },
    "publisher": {
      "@type": "Organization",
      "name": siteName,
      "logo": {
        "@type": "ImageObject",
        "url": "https://agarwalglobalinvestments.com/assets/logo.png"
      }
    },
    "description": description
  };

  return (
    <div className="min-h-screen bg-background">
      <Helmet>
        {/* Basic */}
        <title>{title} • AGI</title>
        <meta name="description" content={description} />
        <link rel="canonical" href={canonical} />

        {/* Open Graph */}
        <meta property="og:site_name" content={siteName} />
        <meta property="og:type" content="article" />
        <meta property="og:url" content={shareUrl} />
        <meta property="og:title" content={`${title} | ${siteName}`} />
        <meta property="og:description" content={description} />
        <meta property="og:image" content={image} />
        {isoPubDate && <meta property="article:published_time" content={isoPubDate} />}
        {Array.isArray(article.tags) &&
          article.tags.map((t, i) => (
            <meta key={i} property="article:tag" content={t} />
          ))}

        {/* Twitter */}
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content={`${title} | ${siteName}`} />
        <meta name="twitter:description" content={description} />
        <meta name="twitter:image" content={image} />

        {/* Fallback image */}
        {image && <meta property="og:image:alt" content={title} />}
        {/* JSON-LD */}
        <script type="application/ld+json">{JSON.stringify(jsonLd)}</script>
      </Helmet>

      <div className="max-w-3xl mx-auto px-4 py-8">
        <Link to="/" className="text-sm text-muted-foreground hover:text-foreground">
          ← Back
        </Link>

        <h1 className="mt-3 text-3xl md:text-4xl font-extrabold tracking-tight leading-tight">
          {article.title}
        </h1>

        <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-muted-foreground">
          <span>{niceDate}</span>
          <span>•</span>
          <span>{minutes} min read</span>

          {Array.isArray(article.tags) && article.tags.length > 0 && (
            <>
              <span>•</span>
              <div className="flex flex-wrap gap-2">
                {article.tags.map((t, i) => (
                  <span
                    key={i}
                    className="rounded-full bg-accent px-2 py-0.5 text-xs text-foreground"
                  >
                    #{t}
                  </span>
                ))}
              </div>
            </>
          )}

          {article.status === 'draft' && (
            <>
              <span>•</span>
              <span className="text-orange-500">Draft</span>
            </>
          )}
        </div>

        {image && (
          <div className="mt-6">
            <img src={image} alt="" className="w-full rounded-xl border object-cover" />
          </div>
        )}

        <article
          className="prose prose-neutral dark:prose-invert max-w-none mt-8
                     prose-img:rounded-lg prose-img:border
                     prose-h1:font-extrabold prose-h2:font-bold prose-p:leading-7"
          dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
        />

        <div className="mt-10 flex flex-wrap gap-3">
          <Button
            variant="outline"
            onClick={() =>
              window.open(
                `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(shareUrl)}`,
                '_blank'
              )
            }
          >
            Share on LinkedIn
          </Button>

          <Button
            variant="outline"
            onClick={() =>
              window.open(
                `https://twitter.com/intent/tweet?url=${encodeURIComponent(shareUrl)}&text=${encodeURIComponent(title)}`,
                '_blank'
              )
            }
          >
            Share on X
          </Button>

          <Button variant="outline" onClick={() => navigator.clipboard.writeText(shareUrl)}>
            Copy link
          </Button>

          {user?.id === article.author_id && (
            <>
              <Button variant="outline" onClick={() => navigate(`/write?edit=${encodeURIComponent(article.slug)}`)}>
                Edit
              </Button>
              <Button variant="destructive" onClick={deleteArticle}>
                Delete
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
