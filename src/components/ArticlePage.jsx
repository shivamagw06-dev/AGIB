// src/components/ArticlePage.jsx
import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
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
  const [author, setAuthor] = useState(null);

  // subscription states
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [checkingSubscription, setCheckingSubscription] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // UI messages
  const [message, setMessage] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  // --- Fetch article (published; if author is current user allow draft)
  useEffect(() => {
    let mounted = true;
    (async () => {
      setLoading(true);
      setMessage(null);
      setErrorMessage(null);

      try {
        const baseSelect =
          'id, title, slug, section, excerpt, cover_url, content, content_md, tags, status, published_at, author_id, created_at';

        let { data, error } = await supabase
          .from('articles')
          .select(baseSelect)
          .eq('slug', slug)
          .eq('status', 'published')
          .maybeSingle();

        // if not found and user is the author, allow them to view their draft
        if ((!data || error) && user?.id) {
          const { data: authorData, error: authorErr } = await supabase
            .from('articles')
            .select(baseSelect)
            .eq('slug', slug)
            .eq('author_id', user.id)
            .maybeSingle();

          if (authorErr) {
            console.warn('Author fetch error for draft fallback', authorErr);
          }

          if (authorData) data = authorData;
        }

        if (mounted) {
          setArticle(data || null);
        }
      } catch (err) {
        console.error('Article fetch error', err);
        if (mounted) setErrorMessage('Failed to load article.');
      } finally {
        if (mounted) setLoading(false);
      }
    })();

    return () => {
      mounted = false;
    };
  }, [slug, user?.id]);

  // --- Fetch author profile once we have article
  useEffect(() => {
    let mounted = true;
    (async () => {
      setAuthor(null);
      if (!article?.author_id) return;

      try {
        const { data: aData, error } = await supabase
          .from('profiles') // your table (confirmed in screenshots)
          .select('id, full_name, display_name, handle, photo_url, is_public')
          .eq('id', article.author_id)
          .maybeSingle();

        if (error) {
          console.warn('Author lookup error', error);
        } else if (mounted) {
          setAuthor(aData || null);
        }
      } catch (err) {
        console.error('Author fetch failed', err);
      }
    })();

    return () => {
      mounted = false;
    };
  }, [article?.author_id]);

  // --- Check subscription status (subscriber -> author)
  useEffect(() => {
    let mounted = true;
    (async () => {
      setIsSubscribed(false);
      setCheckingSubscription(false);
      if (!user?.id || !article?.author_id) return;

      setCheckingSubscription(true);

      try {
        // adjust column names if different; expects `subscriber_id` & `author_id`
        const { data: subData, error } = await supabase
          .from('subscriptions')
          .select('id')
          .eq('subscriber_id', user.id)
          .eq('author_id', article.author_id)
          .maybeSingle();

        if (error) {
          console.warn('Subscription check error', error);
        } else if (mounted) {
          setIsSubscribed(!!subData);
        }
      } catch (err) {
        console.error('Subscription check failed', err);
      } finally {
        if (mounted) setCheckingSubscription(false);
      }
    })();

    return () => {
      mounted = false;
    };
  }, [user?.id, article?.author_id]);

  const htmlToUse = article ? (article.content ?? article.content_md ?? '') : '';
  const minutes = useMemo(() => readingTimeFromHTML(htmlToUse), [htmlToUse]);

  // delete article (author only)
  async function deleteArticle() {
    if (!article) return;
    const ok = window.confirm('Delete this article? This cannot be undone.');
    if (!ok) return;

    try {
      const { error } = await supabase
        .from('articles')
        .delete()
        .eq('id', article.id)
        .eq('author_id', user?.id);

      if (error) throw error;
      navigate('/');
    } catch (err) {
      console.error('Delete failed', err);
      setErrorMessage('Delete failed: ' + (err.message || 'unknown error'));
    }
  }

  // subscribe / unsubscribe toggle
  async function handleSubscribeToggle() {
    // require login
    if (!user?.id) {
      const next = typeof window !== 'undefined' ? window.location.pathname : `/article/${article?.slug}`;
      navigate(`/login?next=${encodeURIComponent(next)}`);
      return;
    }

    if (!article?.author_id) {
      setErrorMessage('Unable to subscribe to this author.');
      return;
    }

    if (user.id === article.author_id) {
      setMessage('You are the author of this article.');
      return;
    }

    setSubmitting(true);
    setErrorMessage(null);
    setMessage(null);

    try {
      if (!isSubscribed) {
        // create subscription — upsert to avoid duplicates if unique constraint exists
        const payload = {
          subscriber_id: user.id,
          author_id: article.author_id,
          created_at: new Date().toISOString()
        };

        // use upsert to avoid unique constraint errors (onConflict: subscriber_id,author_id not supported here — server-side constraint recommended)
        const { data, error } = await supabase
          .from('subscriptions')
          .insert(payload)
          .select()
          .maybeSingle();

        if (error) throw error;
        setIsSubscribed(true);
        setMessage('Subscribed successfully.');
      } else {
        // unsubscribe: delete the record(s)
        const { error } = await supabase
          .from('subscriptions')
          .delete()
          .eq('subscriber_id', user.id)
          .eq('author_id', article.author_id);

        if (error) throw error;
        setIsSubscribed(false);
        setMessage('Unsubscribed.');
      }
    } catch (err) {
      console.error('Subscription action error', err);
      setErrorMessage('Subscription action failed: ' + (err.message || 'unknown error'));
    } finally {
      setSubmitting(false);
    }
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

  const shareUrl =
    typeof window !== 'undefined'
      ? window.location.href
      : `https://agarwalglobalinvestments.com/article/${article.slug}`;

  const title = article.title || 'Article';
  const description =
    article.excerpt ||
    (htmlToUse ? String(htmlToUse).replace(/<[^>]*>/g, ' ').slice(0, 160) : 'AGI article');
  const image = article.cover_url || 'https://agarwalglobalinvestments.com/assets/og-image.png';
  const siteName = 'Agarwal Global Investments';
  const canonical = `https://agarwalglobalinvestments.com/article/${article.slug}`;

  const sanitizedHtml = DOMPurify.sanitize(htmlToUse);

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'Article',
    mainEntityOfPage: {
      '@type': 'WebPage',
      '@id': canonical
    },
    headline: title,
    image: [image],
    datePublished: isoPubDate,
    author: {
      '@type': 'Person',
      name: author?.full_name || author?.display_name || 'Author'
    },
    publisher: {
      '@type': 'Organization',
      name: siteName,
      logo: {
        '@type': 'ImageObject',
        url: 'https://agarwalglobalinvestments.com/assets/logo.png'
      }
    },
    description
  };

  return (
    <div className="min-h-screen bg-background">
      <Helmet>
        <title>{title} • AGI</title>
        <meta name="description" content={description} />
        <link rel="canonical" href={canonical} />
        <meta property="og:site_name" content={siteName} />
        <meta property="og:type" content="article" />
        <meta property="og:url" content={shareUrl} />
        <meta property="og:title" content={`${title} | ${siteName}`} />
        <meta property="og:description" content={description} />
        <meta property="og:image" content={image} />
        {isoPubDate && <meta property="article:published_time" content={isoPubDate} />}
        {Array.isArray(article.tags) &&
          article.tags.map((t, i) => <meta key={i} property="article:tag" content={t} />)}
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content={`${title} | ${siteName}`} />
        <meta name="twitter:description" content={description} />
        <meta name="twitter:image" content={image} />
        {image && <meta property="og:image:alt" content={title} />}
        <script type="application/ld+json">{JSON.stringify(jsonLd)}</script>
      </Helmet>

      <div className="max-w-3xl mx-auto px-4 py-8">
        <Link to="/" className="text-sm text-muted-foreground hover:text-foreground">
          ← Back
        </Link>

        <h1 className="mt-3 text-3xl md:text-4xl font-extrabold tracking-tight leading-tight">
          {article.title}
        </h1>

        {/* author + subscribe */}
        <div className="mt-4 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full overflow-hidden bg-gray-100">
              {author?.photo_url ? (
                <img src={author.photo_url} alt={author.full_name || 'author'} className="w-full h-full object-cover" />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-sm text-gray-400">
                  {author?.display_name ? author.display_name[0] : 'A'}
                </div>
              )}
            </div>

            <div className="text-sm">
              <div className="font-medium text-foreground">
                {author?.full_name || author?.display_name || author?.handle || 'Author'}
              </div>
              <div className="text-muted-foreground text-xs">
                {author?.handle ? `@${author.handle}` : ''}
              </div>
            </div>
          </div>

          <div>
            {article.author_id !== user?.id && (
              <div>
                <Button
                  onClick={handleSubscribeToggle}
                  disabled={checkingSubscription || submitting}
                  className="bg-yellow-500 hover:bg-yellow-600 text-white text-sm px-3 py-1 rounded-full"
                >
                  {checkingSubscription || submitting
                    ? 'Please wait...'
                    : isSubscribed
                    ? 'Unsubscribe'
                    : 'Subscribe'}
                </Button>
              </div>
            )}

            {article.author_id === user?.id && (
              <div className="text-sm text-muted-foreground">You are the author</div>
            )}
          </div>
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-muted-foreground">
          <span>{niceDate}</span>
          <span>•</span>
          <span>{minutes} min read</span>

          {Array.isArray(article.tags) && article.tags.length > 0 && (
            <>
              <span>•</span>
              <div className="flex flex-wrap gap-2">
                {article.tags.map((t, i) => (
                  <span key={i} className="rounded-full bg-accent px-2 py-0.5 text-xs text-foreground">
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
          className="prose prose-neutral dark:prose-invert max-w-none mt-8 prose-img:rounded-lg prose-img:border prose-h1:font-extrabold prose-h2:font-bold prose-p:leading-7"
          dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
        />

        {message && <div className="mt-6 text-sm text-green-700">{message}</div>}
        {errorMessage && <div className="mt-6 text-sm text-red-600">{errorMessage}</div>}

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
