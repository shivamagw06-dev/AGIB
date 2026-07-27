/**
 * CMS → Intelligence ingest job queue.
 * HTTP only enqueues; a Node worker wakes the engine, retries, and completes.
 * Soft layer only — Architecture v1.0.1 LOCKED.
 */

import { createHash, randomUUID } from 'crypto';
import { markArticleIntelligenceIngest } from './cmsArticleLearning.js';

const JOB_STATUSES = new Set(['pending', 'waking', 'processing', 'completed', 'failed']);
const MAX_ATTEMPTS_DEFAULT = 6;
const KEEP_WARM_MS = 5 * 60 * 1000;
const WORKER_TICK_MS = 2_000;

/** @type {Map<string, object>} */
const memoryJobs = new Map();

let workerStarted = false;
let workerBusy = false;
let keepWarmStarted = false;
/** @type {null | ((path:string, init?:object)=>Promise<{ok:boolean,status:number,data:any}>)} */
let engineFetchRef = null;

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function nowIso() {
  return new Date().toISOString();
}

export function contentHashForIngest({ title, content, article_id, slug } = {}) {
  return createHash('sha256')
    .update(
      JSON.stringify({
        title: String(title || '').trim(),
        content: String(content || '').trim(),
        article_id: article_id || null,
        slug: slug || null,
      })
    )
    .digest('hex')
    .slice(0, 32);
}

function newJobId() {
  return `job_${randomUUID().replace(/-/g, '').slice(0, 16)}`;
}

function backoffMs(attempt) {
  // 1s, 2s, 4s, 8s, 16s, 30s (capped)
  return Math.min(30_000, 1000 * 2 ** Math.max(0, attempt - 1));
}

function publicJob(job) {
  if (!job) return null;
  return {
    job_id: job.id,
    id: job.id,
    article_id: job.article_id || null,
    slug: job.slug || null,
    content_hash: job.content_hash,
    status: job.status,
    phase: job.phase,
    attempt: job.attempt,
    max_attempts: job.max_attempts,
    document_id: job.document_id || null,
    error: job.error || null,
    created_at: job.created_at,
    started_at: job.started_at || null,
    finished_at: job.finished_at || null,
    updated_at: job.updated_at,
    next_attempt_at: job.next_attempt_at,
    queued: ['pending', 'waking', 'processing'].includes(job.status),
    pending: ['pending', 'waking', 'processing'].includes(job.status),
    completed: job.status === 'completed',
    failed: job.status === 'failed',
  };
}

async function createAdmin() {
  const supabaseUrl = (process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL || '').trim();
  const serviceKey = (process.env.SUPABASE_SERVICE_ROLE_KEY || '').trim();
  if (!supabaseUrl || !serviceKey) return null;
  const { createClient } = await import('@supabase/supabase-js');
  return createClient(supabaseUrl, serviceKey, {
    auth: { autoRefreshToken: false, persistSession: false },
  });
}

function rowToJob(row) {
  if (!row) return null;
  return {
    id: row.id,
    article_id: row.article_id,
    slug: row.slug,
    content_hash: row.content_hash,
    status: row.status,
    phase: row.phase,
    attempt: Number(row.attempt || 0),
    max_attempts: Number(row.max_attempts || MAX_ATTEMPTS_DEFAULT),
    payload: row.payload || {},
    document_id: row.document_id,
    error: row.error,
    created_at: row.created_at,
    started_at: row.started_at,
    finished_at: row.finished_at,
    updated_at: row.updated_at,
    next_attempt_at: row.next_attempt_at,
  };
}

async function dbInsertJob(job) {
  const admin = await createAdmin();
  if (!admin) return { ok: false, skipped: true };
  const { error } = await admin.from('cms_intelligence_ingest_jobs').insert({
    id: job.id,
    article_id: job.article_id,
    slug: job.slug,
    content_hash: job.content_hash,
    status: job.status,
    phase: job.phase,
    attempt: job.attempt,
    max_attempts: job.max_attempts,
    payload: job.payload,
    document_id: job.document_id,
    error: job.error,
    created_at: job.created_at,
    started_at: job.started_at,
    finished_at: job.finished_at,
    updated_at: job.updated_at,
    next_attempt_at: job.next_attempt_at,
  });
  if (error) return { ok: false, error: error.message || String(error) };
  return { ok: true };
}

async function dbUpdateJob(id, patch) {
  const admin = await createAdmin();
  if (!admin) return { ok: false, skipped: true };
  const { error } = await admin
    .from('cms_intelligence_ingest_jobs')
    .update({ ...patch, updated_at: nowIso() })
    .eq('id', id);
  if (error) return { ok: false, error: error.message || String(error) };
  return { ok: true };
}

async function dbFindActiveByHash(articleId, contentHash) {
  const admin = await createAdmin();
  if (!admin || !articleId) return null;
  const { data, error } = await admin
    .from('cms_intelligence_ingest_jobs')
    .select('*')
    .eq('article_id', articleId)
    .eq('content_hash', contentHash)
    .in('status', ['pending', 'waking', 'processing'])
    .order('created_at', { ascending: false })
    .limit(1)
    .maybeSingle();
  if (error) return null;
  return rowToJob(data);
}

async function dbGetJob(id) {
  const admin = await createAdmin();
  if (!admin) return null;
  const { data, error } = await admin
    .from('cms_intelligence_ingest_jobs')
    .select('*')
    .eq('id', id)
    .maybeSingle();
  if (error) return null;
  return rowToJob(data);
}

async function dbClaimNextJob() {
  const admin = await createAdmin();
  if (!admin) return null;
  const now = nowIso();
  // Retries are re-queued as status=pending with next_attempt_at in the future.
  const { data: candidates, error } = await admin
    .from('cms_intelligence_ingest_jobs')
    .select('*')
    .eq('status', 'pending')
    .lte('next_attempt_at', now)
    .order('next_attempt_at', { ascending: true })
    .limit(5);
  if (error || !Array.isArray(candidates) || !candidates.length) return null;

  for (const row of candidates) {
    if (Number(row.attempt || 0) >= Number(row.max_attempts || MAX_ATTEMPTS_DEFAULT)) {
      continue;
    }
    const nextAttempt = Number(row.attempt || 0) + 1;
    const { data: claimed, error: claimErr } = await admin
      .from('cms_intelligence_ingest_jobs')
      .update({
        status: 'waking',
        phase: 'waking_engine',
        attempt: nextAttempt,
        started_at: row.started_at || now,
        updated_at: now,
        error: null,
      })
      .eq('id', row.id)
      .eq('status', 'pending')
      .eq('attempt', row.attempt)
      .select('*')
      .maybeSingle();
    if (!claimErr && claimed) return rowToJob(claimed);
  }
  return null;
}

function memoryFindActive(articleId, contentHash) {
  if (!articleId) return null;
  for (const job of memoryJobs.values()) {
    if (
      job.article_id === articleId &&
      job.content_hash === contentHash &&
      ['pending', 'waking', 'processing'].includes(job.status)
    ) {
      return job;
    }
  }
  return null;
}

function memoryClaimNext() {
  const now = Date.now();
  const candidates = [...memoryJobs.values()]
    .filter((j) => {
      if (j.status !== 'pending') return false;
      if (j.attempt >= j.max_attempts) return false;
      const next = j.next_attempt_at ? Date.parse(j.next_attempt_at) : 0;
      return next <= now;
    })
    .sort((a, b) => Date.parse(a.next_attempt_at) - Date.parse(b.next_attempt_at));

  const job = candidates[0];
  if (!job) return null;

  job.status = 'waking';
  job.phase = 'waking_engine';
  job.attempt += 1;
  job.started_at = job.started_at || nowIso();
  job.updated_at = nowIso();
  job.error = null;
  memoryJobs.set(job.id, job);
  return job;
}

export async function getIngestJob(jobId) {
  if (!jobId) return null;
  const fromMem = memoryJobs.get(jobId);
  if (fromMem) return publicJob(fromMem);
  const fromDb = await dbGetJob(jobId);
  if (fromDb) {
    memoryJobs.set(fromDb.id, fromDb);
    return publicJob(fromDb);
  }
  return null;
}

/**
 * Enqueue ingest. Idempotent on article_id + content_hash while a job is active.
 * Always returns quickly — never talks to the intelligence engine on this path.
 */
export async function enqueueCmsIngestJob(payloadInput = {}) {
  const title = String(payloadInput.title || '').trim();
  const content = String(payloadInput.content || payloadInput.content_md || '').trim();
  if (!title || !content) {
    const err = new Error('title and content are required');
    err.status = 400;
    throw err;
  }

  const payload = {
    title,
    content,
    author: payloadInput.author || 'AGI Research Desk',
    source: 'agi',
    document_type: payloadInput.document_type || 'agi_research',
    language: 'en',
    tickers: Array.isArray(payloadInput.tickers) ? payloadInput.tickers : [],
    themes: Array.isArray(payloadInput.themes) ? payloadInput.themes : [],
    sectors: Array.isArray(payloadInput.sectors) ? payloadInput.sectors : [],
    article_id: payloadInput.article_id || payloadInput.slug || null,
    research_type: payloadInput.research_type || payloadInput.section || '',
    metadata: {
      cms_status: payloadInput.cms_status || payloadInput.status || null,
      slug: payloadInput.slug || null,
      section: payloadInput.section || null,
      destination: payloadInput.destination || 'intelligence',
      ...(payloadInput.metadata && typeof payloadInput.metadata === 'object'
        ? payloadInput.metadata
        : {}),
    },
  };

  const articleId = payload.article_id ? String(payload.article_id) : null;
  const slug = payload.metadata?.slug || payloadInput.slug || null;
  const hash = contentHashForIngest({
    title: payload.title,
    content: payload.content,
    article_id: articleId,
    slug,
  });

  const existing =
    memoryFindActive(articleId, hash) || (await dbFindActiveByHash(articleId, hash));
  if (existing) {
    memoryJobs.set(existing.id, existing);
    return {
      ...publicJob(existing),
      already_queued: true,
      message: 'Ingest already queued for this article version.',
    };
  }

  const createdAt = nowIso();
  const job = {
    id: newJobId(),
    article_id: articleId,
    slug,
    content_hash: hash,
    status: 'pending',
    phase: 'queued',
    attempt: 0,
    max_attempts: MAX_ATTEMPTS_DEFAULT,
    payload,
    document_id: null,
    error: null,
    created_at: createdAt,
    started_at: null,
    finished_at: null,
    updated_at: createdAt,
    next_attempt_at: createdAt,
  };

  memoryJobs.set(job.id, job);
  const inserted = await dbInsertJob(job);
  if (!inserted.ok && !inserted.skipped) {
    // Unique race — reload active job
    const raced = await dbFindActiveByHash(articleId, hash);
    if (raced) {
      memoryJobs.set(raced.id, raced);
      return {
        ...publicJob(raced),
        already_queued: true,
        message: 'Ingest already queued for this article version.',
      };
    }
    console.warn('[cms-ingest-jobs] db insert failed, using memory only', inserted.error);
  }

  if (articleId) {
    try {
      await markArticleIntelligenceIngest({
        articleId,
        status: 'pending',
        error: `Queued job ${job.id}`,
      });
    } catch {
      /* non-fatal */
    }
  }

  // Kick the worker without blocking the HTTP response.
  setImmediate(() => {
    processIngestQueue().catch((err) =>
      console.error('[cms-ingest-jobs] kick error', err?.message || err)
    );
  });

  return {
    ...publicJob(job),
    already_queued: false,
    message: 'Ingest job accepted. Worker will wake the engine and finish in the background.',
  };
}

async function persistJob(job) {
  memoryJobs.set(job.id, job);
  await dbUpdateJob(job.id, {
    status: job.status,
    phase: job.phase,
    attempt: job.attempt,
    document_id: job.document_id,
    error: job.error,
    started_at: job.started_at,
    finished_at: job.finished_at,
    next_attempt_at: job.next_attempt_at,
  });
}

async function wakeEngineUntilReady(engineFetch, maxWaitMs = 100_000) {
  const started = Date.now();
  let attempt = 0;
  let last = null;
  while (Date.now() - started < maxWaitMs) {
    attempt += 1;
    try {
      last = await engineFetch('/v1/health', { timeoutMs: 25_000 });
      if (last.ok && last.data && last.data.ok !== false) {
        return { ok: true, attempt, waitedMs: Date.now() - started, last };
      }
    } catch (error) {
      last = { ok: false, status: 503, data: { error: error.message } };
    }
    const remaining = maxWaitMs - (Date.now() - started);
    if (remaining <= 0) break;
    await sleep(Math.min(remaining, Math.min(8_000, 1_500 + attempt * 750)));
  }
  return { ok: false, attempt, waitedMs: Date.now() - started, last };
}

async function runOneJob(job, engineFetch) {
  job.status = 'waking';
  job.phase = 'waking_engine';
  job.updated_at = nowIso();
  await persistJob(job);

  const wake = await wakeEngineUntilReady(engineFetch, 120_000);
  if (!wake.ok) {
    throw new Error(
      `Engine did not become ready after ${wake.waitedMs}ms (attempt ${job.attempt})`
    );
  }

  job.status = 'processing';
  job.phase = 'ingesting';
  job.updated_at = nowIso();
  await persistJob(job);

  const result = await engineFetch('/v1/kip/ingest/agi', {
    method: 'POST',
    body: job.payload,
    timeoutMs: 120_000,
  });

  if (!result.ok) {
    const msg =
      result.data?.error ||
      result.data?.detail ||
      `Ingest failed (${result.status || 503})`;
    const err = new Error(String(msg));
    err.status = result.status;
    throw err;
  }

  const documentId =
    result.data?.document_id || result.data?.id || result.data?.document?.id || null;

  job.status = 'completed';
  job.phase = 'completed';
  job.document_id = documentId;
  job.error = null;
  job.finished_at = nowIso();
  job.updated_at = job.finished_at;
  await persistJob(job);

  if (job.article_id) {
    await markArticleIntelligenceIngest({
      articleId: job.article_id,
      documentId,
      status: 'learned',
    });
  }

  console.info('[cms-ingest-jobs] completed', {
    job_id: job.id,
    article_id: job.article_id,
    document_id: documentId,
    attempt: job.attempt,
  });
}

async function failOrReschedule(job, error) {
  const message = error?.message || String(error);
  const canRetry = job.attempt < job.max_attempts;
  if (canRetry) {
    job.status = 'pending';
    job.phase = 'retry_scheduled';
    job.error = message.slice(0, 500);
    job.next_attempt_at = new Date(Date.now() + backoffMs(job.attempt)).toISOString();
    job.updated_at = nowIso();
    await persistJob(job);
    console.warn('[cms-ingest-jobs] retry scheduled', {
      job_id: job.id,
      attempt: job.attempt,
      next_attempt_at: job.next_attempt_at,
      error: message,
    });
    return;
  }

  job.status = 'failed';
  job.phase = 'failed';
  job.error = message.slice(0, 500);
  job.finished_at = nowIso();
  job.updated_at = job.finished_at;
  await persistJob(job);

  if (job.article_id) {
    try {
      await markArticleIntelligenceIngest({
        articleId: job.article_id,
        status: 'failed',
        error: job.error,
      });
    } catch {
      /* ignore */
    }
  }
  console.warn('[cms-ingest-jobs] failed', { job_id: job.id, error: job.error });
}

export async function processIngestQueue() {
  if (workerBusy || !engineFetchRef) return;
  workerBusy = true;
  try {
    while (true) {
      let job = memoryClaimNext();
      if (!job) job = await dbClaimNextJob();
      if (!job) break;
      memoryJobs.set(job.id, job);
      try {
        await runOneJob(job, engineFetchRef);
      } catch (error) {
        await failOrReschedule(job, error);
      }
    }
  } finally {
    workerBusy = false;
  }
}

function startKeepWarm(engineFetch) {
  if (keepWarmStarted) return;
  keepWarmStarted = true;
  setInterval(() => {
    engineFetch('/v1/health', { timeoutMs: 20_000 }).catch(() => null);
  }, KEEP_WARM_MS);
  // First ping shortly after boot.
  setTimeout(() => {
    engineFetch('/v1/health', { timeoutMs: 20_000 }).catch(() => null);
  }, 15_000);
}

/**
 * Start the in-process worker + optional keep-warm pings.
 * Safe to call multiple times.
 */
export function startCmsIngestJobWorker(engineFetch) {
  engineFetchRef = engineFetch;
  startKeepWarm(engineFetch);
  if (workerStarted) return;
  workerStarted = true;
  setInterval(() => {
    processIngestQueue().catch((err) =>
      console.error('[cms-ingest-jobs] tick error', err?.message || err)
    );
  }, WORKER_TICK_MS);
  console.info('[cms-ingest-jobs] worker started', {
    tick_ms: WORKER_TICK_MS,
    keep_warm_ms: KEEP_WARM_MS,
  });
}

export function isValidJobStatus(status) {
  return JOB_STATUSES.has(status);
}
