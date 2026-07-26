/**
 * CMS Article Learning — read uploaded articles into KIP/KF/KC (soft-wire).
 * Architecture v1.0.1 LOCKED — additive only; never redesign engines.
 */

function stripHtml(html = '') {
  return String(html)
    .replace(/<script[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

const KNOWN_TICKERS = new Set([
  'ICICIBANK',
  'HDFCBANK',
  'RELIANCE',
  'TCS',
  'INFY',
  'SBIN',
  'AXISBANK',
  'KOTAKBANK',
  'BHARTIARTL',
  'LT',
  'ITC',
  'WIPRO',
  'MARUTI',
  'TATAMOTORS',
  'HINDUNILVR',
  'HCLTECH',
  'AAPL',
  'MSFT',
  'GOOGL',
  'AMZN',
  'NVDA',
]);

function extractTickers(...parts) {
  const text = parts.filter(Boolean).join(' ').toUpperCase();
  const matches = text.match(/\b[A-Z]{2,12}\b/g) || [];
  return [...new Set(matches.filter((t) => KNOWN_TICKERS.has(t) || t.endsWith('BANK')))].slice(0, 12);
}

function learningDateIST(d = new Date()) {
  // Asia/Kolkata calendar date — knowledge updates run every day
  return d.toLocaleDateString('en-CA', { timeZone: 'Asia/Kolkata' });
}

function learnedOnISTDate(iso, dateStr) {
  if (!iso || !dateStr) return false;
  return learningDateIST(new Date(iso)) === dateStr;
}

function getAdminClient() {
  const supabaseUrl = (process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL || '').trim();
  const serviceKey = (process.env.SUPABASE_SERVICE_ROLE_KEY || '').trim();
  if (!supabaseUrl || !serviceKey) return null;
  return { supabaseUrl, serviceKey };
}

async function createAdmin() {
  const creds = getAdminClient();
  if (!creds) return null;
  const { createClient } = await import('@supabase/supabase-js');
  return createClient(creds.supabaseUrl, creds.serviceKey, {
    auth: { autoRefreshToken: false, persistSession: false },
  });
}

/**
 * @param {object} opts
 * @param {(path:string, init?:object)=>Promise<{status:number,data:any}>} opts.engineFetch
 */
export async function learnCmsArticles({
  engineFetch,
  limit = 50,
  onlyUnlearned = false,
  sinceDate = null,
  mode = null,
  compound = true,
} = {}) {
  const admin = await createAdmin();
  if (!admin) {
    return {
      ok: false,
      skipped: true,
      reason: 'Supabase admin credentials unavailable on API (SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY).',
    };
  }

  const learningDate = learningDateIST();
  const dailyMode = mode === 'daily' || Boolean(sinceDate === 'today');
  const effectiveOnlyUnlearned = onlyUnlearned && !dailyMode;

  let query = admin
    .from('articles')
    .select(
      'id,title,slug,section,tags,status,content,content_md,excerpt,published_at,created_at,intelligence_document_id,intelligence_ingested_at,last_learned_at,learn_status,learn_count'
    )
    .in('status', ['published', 'intelligence'])
    .order('published_at', { ascending: false, nullsFirst: false })
    .limit(Math.min(Math.max(Number(limit) || 50, 1), 200));

  if (effectiveOnlyUnlearned) {
    query = query.is('last_learned_at', null);
  }

  const { data: articles, error } = await query;
  if (error) {
    return { ok: false, error: error.message || String(error) };
  }

  let rows = Array.isArray(articles) ? articles : [];
  if (dailyMode) {
    // Daily knowledge update: skip articles already learned on today's IST date
    rows = rows.filter((a) => !learnedOnISTDate(a.last_learned_at, learningDate));
  } else if (sinceDate && sinceDate !== 'today') {
    const cutoff = String(sinceDate).slice(0, 10);
    rows = rows.filter((a) => !a.last_learned_at || String(a.last_learned_at).slice(0, 10) < cutoff);
  }
  const results = [];
  let learned = 0;
  let failed = 0;
  let skipped = 0;

  for (const article of rows) {
    const title = String(article.title || '').trim();
    const content = stripHtml(article.content_md || article.content || article.excerpt || '');
    if (!title || content.length < 40) {
      skipped += 1;
      results.push({
        article_id: article.id,
        title,
        status: 'skipped',
        error: 'Insufficient content',
      });
      await admin
        .from('articles')
        .update({ learn_status: 'skipped', last_learn_error: 'Insufficient content' })
        .eq('id', article.id);
      continue;
    }

    const destination = article.status === 'published' ? 'website' : 'intelligence';
    const payload = {
      title,
      content,
      author: 'AGI Research Desk',
      source: 'agi',
      document_type: destination === 'website' ? 'agi_research' : 'agi_note',
      language: 'en',
      tickers: extractTickers(title, ...(article.tags || []), content.slice(0, 1200)),
      themes: Array.isArray(article.tags) ? article.tags.slice(0, 8) : [],
      sectors: [],
      article_id: article.id || article.slug,
      research_type: article.section || '',
      metadata: {
        cms_status: article.status,
        slug: article.slug || null,
        section: article.section || null,
        destination,
        learning_date: learningDate,
        cms_bulk_learn: true,
      },
    };

    try {
      const result = await engineFetch('/v1/kip/ingest/agi', { method: 'POST', body: payload });
      if (result.status >= 400) {
        throw new Error(result.data?.error || result.data?.detail || `Ingest failed (${result.status})`);
      }
      const documentId =
        result.data?.document_id ||
        result.data?.id ||
        result.data?.document?.id ||
        article.intelligence_document_id ||
        null;
      const learnedAt = new Date().toISOString();
      const nextCount = Number(article.learn_count || 0) + 1;

      await admin
        .from('articles')
        .update({
          intelligence_document_id: documentId,
          intelligence_ingested_at: learnedAt,
          last_learned_at: learnedAt,
          learn_status: 'learned',
          last_learn_error: null,
          learn_count: nextCount,
        })
        .eq('id', article.id);

      await admin.from('cms_article_learn_events').insert({
        article_id: article.id,
        learned_at: learnedAt,
        learning_date: learningDate,
        document_id: documentId,
        status: 'learned',
        title,
        slug: article.slug || null,
        destination,
      });

      learned += 1;
      results.push({
        article_id: article.id,
        title,
        slug: article.slug,
        status: 'learned',
        document_id: documentId,
        learned_at: learnedAt,
        learning_date: learningDate,
        learn_count: nextCount,
      });
    } catch (err) {
      failed += 1;
      const message = err?.message || String(err);
      await admin
        .from('articles')
        .update({ learn_status: 'failed', last_learn_error: message.slice(0, 500) })
        .eq('id', article.id);
      await admin.from('cms_article_learn_events').insert({
        article_id: article.id,
        learning_date: learningDate,
        status: 'failed',
        title,
        slug: article.slug || null,
        destination,
        error: message.slice(0, 500),
      });
      results.push({
        article_id: article.id,
        title,
        status: 'failed',
        error: message,
      });
    }
  }

  let compoundResult = null;
  if (compound && learned > 0) {
    try {
      const populated = await engineFetch('/v1/kc/populate?rebuild_kip=false', {
        method: 'POST',
        body: {},
      });
      compoundResult = {
        ok: populated.status < 400,
        status: populated.status,
        summary: populated.data?.metrics || populated.data?.message || null,
      };
    } catch (err) {
      compoundResult = { ok: false, error: err?.message || String(err) };
    }
  }

  return {
    ok: true,
    learning_date: learningDate,
    timezone: 'Asia/Kolkata',
    mode: dailyMode ? 'daily' : effectiveOnlyUnlearned ? 'unlearned' : 'bulk',
    scanned: rows.length,
    learned,
    failed,
    skipped,
    compound: compoundResult,
    results,
    architecture_status: 'v1.0.1 LOCKED',
    note: 'Soft-wire CMS → KIP → KF/KC. Re-run daily so learning_date stays current.',
  };
}

export async function cmsLearningStatus({ days = 14 } = {}) {
  const admin = await createAdmin();
  if (!admin) {
    return {
      ok: false,
      skipped: true,
      reason: 'Supabase admin credentials unavailable on API.',
    };
  }

  const dayCount = Math.min(Math.max(Number(days) || 14, 1), 90);
  const since = new Date(Date.now() - dayCount * 86400000).toISOString();

  const [{ data: events, error: eventsError }, { data: pending, error: pendingError }, { count, error: countError }] =
    await Promise.all([
      admin
        .from('cms_article_learn_events')
        .select('id,article_id,learned_at,learning_date,document_id,status,title,slug,error')
        .gte('learned_at', since)
        .order('learned_at', { ascending: false })
        .limit(200),
      admin
        .from('articles')
        .select('id,title,slug,status,last_learned_at,learn_status,published_at')
        .in('status', ['published', 'intelligence'])
        .is('last_learned_at', null)
        .limit(100),
      admin
        .from('articles')
        .select('id', { count: 'exact', head: true })
        .in('status', ['published', 'intelligence']),
    ]);

  if (eventsError || pendingError || countError) {
    return {
      ok: false,
      error: eventsError?.message || pendingError?.message || countError?.message,
    };
  }

  const byDate = {};
  for (const ev of events || []) {
    const d = ev.learning_date || String(ev.learned_at || '').slice(0, 10);
    if (!d) continue;
    if (!byDate[d]) byDate[d] = { learning_date: d, learned: 0, failed: 0, titles: [] };
    if (ev.status === 'learned') byDate[d].learned += 1;
    if (ev.status === 'failed') byDate[d].failed += 1;
    if (ev.title && byDate[d].titles.length < 8) byDate[d].titles.push(ev.title);
  }

  const calendar = Object.values(byDate).sort((a, b) => String(b.learning_date).localeCompare(String(a.learning_date)));

  return {
    ok: true,
    today: learningDateIST(),
    timezone: 'Asia/Kolkata',
    articles_total: count || 0,
    pending_unlearned: pending || [],
    pending_count: (pending || []).length,
    recent_events: events || [],
    learning_calendar: calendar,
    scheduler: getCmsLearningSchedulerStatus(),
    architecture_status: 'v1.0.1 LOCKED',
  };
}

export function cmsLearningConfigured() {
  return Boolean(getAdminClient());
}

let cmsLearnScheduler = null;
let cmsLearnLastRun = null;
let cmsLearnLastDate = null;

export function getCmsLearningSchedulerStatus() {
  return {
    enabled: Boolean(cmsLearnScheduler),
    last_run: cmsLearnLastRun,
    last_learning_date: cmsLearnLastDate,
    interval_ms: Number(process.env.CMS_ARTICLE_LEARN_INTERVAL_MS || 60 * 60 * 1000),
  };
}

/**
 * Soft daily learner — once per IST calendar day, read CMS articles into KIP/KF/KC.
 * Disable with CMS_ARTICLE_LEARN_DAILY=false.
 */
export function startCmsArticleLearningScheduler(engineFetch) {
  if (cmsLearnScheduler) return;
  if ((process.env.CMS_ARTICLE_LEARN_DAILY || 'true').toLowerCase() === 'false') return;
  if (!cmsLearningConfigured()) {
    console.info('[cms-learn] scheduler idle — Supabase admin credentials missing');
    return;
  }
  if (typeof engineFetch !== 'function') {
    console.warn('[cms-learn] scheduler skipped — engineFetch required');
    return;
  }

  const intervalMs = Number(process.env.CMS_ARTICLE_LEARN_INTERVAL_MS || 60 * 60 * 1000);
  const tick = async () => {
    const today = learningDateIST();
    if (cmsLearnLastDate === today && cmsLearnLastRun?.ok) return;
    try {
      const result = await learnCmsArticles({
        engineFetch,
        mode: 'daily',
        limit: Number(process.env.CMS_ARTICLE_LEARN_LIMIT || 50),
        compound: true,
      });
      cmsLearnLastRun = {
        at: new Date().toISOString(),
        ok: Boolean(result?.ok),
        learning_date: result?.learning_date || today,
        learned: result?.learned ?? 0,
        failed: result?.failed ?? 0,
        skipped: result?.skipped ?? 0,
        reason: result?.reason || result?.error || null,
      };
      if (result?.ok) cmsLearnLastDate = result.learning_date || today;
      console.info(
        '[cms-learn] daily run',
        cmsLearnLastRun.learning_date,
        `learned=${cmsLearnLastRun.learned}`,
        `failed=${cmsLearnLastRun.failed}`
      );
    } catch (err) {
      cmsLearnLastRun = {
        at: new Date().toISOString(),
        ok: false,
        error: err?.message || String(err),
      };
      console.warn('[cms-learn] scheduled run failed:', err?.message || err);
    }
  };

  setTimeout(() => {
    tick().catch(() => {});
  }, 45_000);
  cmsLearnScheduler = setInterval(() => {
    tick().catch(() => {});
  }, intervalMs);
  cmsLearnScheduler.unref?.();
  console.info(`[cms-learn] daily scheduler active every ${Math.round(intervalMs / 60000)}m (IST dates)`);
}
