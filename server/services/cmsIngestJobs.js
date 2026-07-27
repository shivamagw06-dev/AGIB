/**
 * CMS → Intelligence ingest job queue (hardened).
 * Soft layer only — Architecture v1.0.1 LOCKED.
 *
 * Modes:
 * - embedded (default): API process runs the worker loop + reclaim/watchdog
 * - external: API only enqueues; run `node server/workers/cmsIngestWorker.js`
 *
 * Content policy: same article_id + same content_hash → idempotent (already queued).
 * Same article_id + different content_hash → new version job (re-ingest).
 */

import { createHash, randomUUID } from 'crypto';
import os from 'os';
import { markArticleIntelligenceIngest } from './cmsArticleLearning.js';

const ACTIVE_STATUSES = ['pending', 'waking', 'processing'];
const TERMINAL_STATUSES = ['completed', 'failed', 'failed_permanent'];
const JOB_STATUSES = new Set([...ACTIVE_STATUSES, ...TERMINAL_STATUSES]);

const MAX_ATTEMPTS_DEFAULT = Number(process.env.CMS_INGEST_MAX_ATTEMPTS || 6);
const KEEP_WARM_MS = Number(process.env.CMS_INGEST_KEEP_WARM_MS || 5 * 60 * 1000);
const WORKER_TICK_MS = Number(process.env.CMS_INGEST_TICK_MS || 2_000);
const STALL_MS = Number(process.env.CMS_INGEST_STALL_MS || 15 * 60 * 1000);
const QUEUED_ALERT_MS = Number(process.env.CMS_INGEST_QUEUED_ALERT_MS || 30 * 60 * 1000);
const WORKER_ID =
  process.env.CMS_INGEST_WORKER_ID ||
  `worker_${(os.hostname() || 'host').slice(0, 24)}_${process.pid}`;

/** @type {Map<string, object>} */
const memoryJobs = new Map();

let workerStarted = false;
let workerBusy = false;
let keepWarmStarted = false;
let reclaimDone = false;
/** @type {null | ((path:string, init?:object)=>Promise<{ok:boolean,status:number,data:any}>)} */
let engineFetchRef = null;

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function nowIso() {
  return new Date().toISOString();
}

function workerMode() {
  const mode = String(process.env.CMS_INGEST_WORKER_MODE || 'embedded').toLowerCase();
  return mode === 'external' ? 'external' : 'embedded';
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
  return Math.min(30_000, 1000 * 2 ** Math.max(0, attempt - 1));
}

/**
 * Classify failures so permanent errors are not retried forever.
 * @returns {'transient'|'permanent'}
 */
export function classifyIngestFailure(error, status) {
  const code = Number(status || error?.status || 0);
  const msg = String(error?.message || error || '').toLowerCase();

  if ([400, 401, 403, 404, 422].includes(code)) return 'permanent';
  if (
    /title and content are required|insufficient content|malformed|validation|invalid article|unauthorized|forbidden|schema|unprocessable|not found/.test(
      msg
    )
  ) {
    return 'permanent';
  }
  if ([408, 425, 429, 500, 502, 503, 504].includes(code)) return 'transient';
  if (
    /timeout|timed out|econnreset|econnrefused|enotfound|socket|network|fetch failed|502|503|504|cold|unavailable|aborted|temporarily/.test(
      msg
    )
  ) {
    return 'transient';
  }
  // Default: retry — most production failures here are cold-start / gateway.
  return 'transient';
}

function publicJob(job) {
  if (!job) return null;
  const terminal = TERMINAL_STATUSES.includes(job.status);
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
    failure_class: job.failure_class || null,
    worker_id: job.worker_id || null,
    wake_time_ms: job.wake_time_ms ?? null,
    engine_latency_ms: job.engine_latency_ms ?? null,
    queued_at: job.queued_at || job.created_at,
    created_at: job.created_at,
    started_at: job.started_at || null,
    finished_at: job.finished_at || null,
    updated_at: job.updated_at,
    next_attempt_at: job.next_attempt_at,
    queued: ACTIVE_STATUSES.includes(job.status),
    pending: ACTIVE_STATUSES.includes(job.status),
    completed: job.status === 'completed',
    failed: job.status === 'failed' || job.status === 'failed_permanent',
    failed_permanent: job.status === 'failed_permanent',
    terminal,
    content_policy:
      'same article_id + same content_hash = idempotent; content change = new version job',
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
    failure_class: row.failure_class || null,
    worker_id: row.worker_id || null,
    wake_time_ms: row.wake_time_ms ?? null,
    engine_latency_ms: row.engine_latency_ms ?? null,
    queued_at: row.queued_at || row.created_at,
    created_at: row.created_at,
    started_at: row.started_at,
    finished_at: row.finished_at,
    updated_at: row.updated_at,
    next_attempt_at: row.next_attempt_at,
  };
}

function jobDbPatch(job) {
  return {
    status: job.status,
    phase: job.phase,
    attempt: job.attempt,
    max_attempts: job.max_attempts,
    document_id: job.document_id,
    error: job.error,
    failure_class: job.failure_class,
    worker_id: job.worker_id,
    wake_time_ms: job.wake_time_ms,
    engine_latency_ms: job.engine_latency_ms,
    queued_at: job.queued_at || job.created_at,
    started_at: job.started_at,
    finished_at: job.finished_at,
    next_attempt_at: job.next_attempt_at,
    updated_at: nowIso(),
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
    failure_class: job.failure_class,
    worker_id: job.worker_id,
    wake_time_ms: job.wake_time_ms,
    engine_latency_ms: job.engine_latency_ms,
    queued_at: job.queued_at || job.created_at,
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
    .in('status', ACTIVE_STATUSES)
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

/**
 * Optimistic claim: UPDATE … WHERE status='pending' RETURNING *.
 * Zero rows ⇒ another worker already claimed it.
 */
async function dbClaimNextJob() {
  const admin = await createAdmin();
  if (!admin) return null;
  const now = nowIso();
  const { data: candidates, error } = await admin
    .from('cms_intelligence_ingest_jobs')
    .select('*')
    .eq('status', 'pending')
    .lte('next_attempt_at', now)
    .order('next_attempt_at', { ascending: true })
    .limit(8);
  if (error || !Array.isArray(candidates) || !candidates.length) return null;

  for (const row of candidates) {
    if (Number(row.attempt || 0) >= Number(row.max_attempts || MAX_ATTEMPTS_DEFAULT)) {
      // Dead-letter stranded pending jobs that somehow exceeded attempts.
      await admin
        .from('cms_intelligence_ingest_jobs')
        .update({
          status: 'failed_permanent',
          phase: 'dead_letter',
          failure_class: 'permanent',
          error: 'Exceeded max attempts while pending',
          finished_at: now,
          updated_at: now,
        })
        .eq('id', row.id)
        .eq('status', 'pending');
      continue;
    }
    const nextAttempt = Number(row.attempt || 0) + 1;
    const { data: claimed, error: claimErr } = await admin
      .from('cms_intelligence_ingest_jobs')
      .update({
        status: 'waking',
        phase: 'waking_engine',
        attempt: nextAttempt,
        worker_id: WORKER_ID,
        started_at: row.started_at || now,
        updated_at: now,
        error: null,
        failure_class: null,
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

/**
 * Reclaim jobs stuck in waking/processing after a crash/restart.
 */
export async function reclaimStalledJobs({ stallMs = STALL_MS } = {}) {
  const cutoff = new Date(Date.now() - stallMs).toISOString();
  let reclaimed = 0;

  for (const job of memoryJobs.values()) {
    if (
      ['waking', 'processing'].includes(job.status) &&
      job.updated_at &&
      Date.parse(job.updated_at) < Date.parse(cutoff)
    ) {
      job.status = 'pending';
      job.phase = 'reclaimed_after_stall';
      job.worker_id = null;
      job.error = `Reclaimed after stall (>${Math.round(stallMs / 1000)}s in ${job.phase || job.status})`;
      job.next_attempt_at = nowIso();
      job.updated_at = nowIso();
      memoryJobs.set(job.id, job);
      reclaimed += 1;
    }
  }

  const admin = await createAdmin();
  if (admin) {
    const { data: stuck } = await admin
      .from('cms_intelligence_ingest_jobs')
      .select('*')
      .in('status', ['waking', 'processing'])
      .lt('updated_at', cutoff)
      .limit(50);
    for (const row of stuck || []) {
      const { data: updated } = await admin
        .from('cms_intelligence_ingest_jobs')
        .update({
          status: 'pending',
          phase: 'reclaimed_after_stall',
          worker_id: null,
          error: `Reclaimed after stall (>${Math.round(stallMs / 1000)}s)`,
          next_attempt_at: nowIso(),
          updated_at: nowIso(),
        })
        .eq('id', row.id)
        .in('status', ['waking', 'processing'])
        .select('*')
        .maybeSingle();
      if (updated) {
        memoryJobs.set(updated.id, rowToJob(updated));
        reclaimed += 1;
      }
    }
  }

  if (reclaimed) {
    console.warn('[cms-ingest-jobs] reclaimed stalled jobs', { reclaimed, stallMs, worker: WORKER_ID });
  }
  return { ok: true, reclaimed, stall_ms: stallMs, worker_id: WORKER_ID };
}

export async function getStuckIngestJobs({
  processingOlderThanMs = STALL_MS,
  queuedOlderThanMs = QUEUED_ALERT_MS,
} = {}) {
  const processingCutoff = new Date(Date.now() - processingOlderThanMs).toISOString();
  const queuedCutoff = new Date(Date.now() - queuedOlderThanMs).toISOString();
  const stuck = [];

  for (const job of memoryJobs.values()) {
    if (
      ['waking', 'processing'].includes(job.status) &&
      job.updated_at &&
      job.updated_at < processingCutoff
    ) {
      stuck.push({ ...publicJob(job), alert: 'stalled_processing' });
    } else if (
      job.status === 'pending' &&
      (job.queued_at || job.created_at) < queuedCutoff
    ) {
      stuck.push({ ...publicJob(job), alert: 'stalled_queued' });
    }
  }

  const admin = await createAdmin();
  if (admin) {
    const { data: processing } = await admin
      .from('cms_intelligence_ingest_jobs')
      .select('*')
      .in('status', ['waking', 'processing'])
      .lt('updated_at', processingCutoff)
      .limit(50);
    for (const row of processing || []) {
      stuck.push({ ...publicJob(rowToJob(row)), alert: 'stalled_processing' });
    }
    const { data: queued } = await admin
      .from('cms_intelligence_ingest_jobs')
      .select('*')
      .eq('status', 'pending')
      .lt('created_at', queuedCutoff)
      .limit(50);
    for (const row of queued || []) {
      stuck.push({ ...publicJob(rowToJob(row)), alert: 'stalled_queued' });
    }
  }

  // Dedupe by job id
  const byId = new Map();
  for (const item of stuck) byId.set(item.job_id || item.id, item);
  const items = [...byId.values()];
  return {
    ok: true,
    count: items.length,
    alert: items.length > 0,
    processing_older_than_ms: processingOlderThanMs,
    queued_older_than_ms: queuedOlderThanMs,
    worker_id: WORKER_ID,
    jobs: items,
  };
}

function memoryFindActive(articleId, contentHash) {
  if (!articleId) return null;
  for (const job of memoryJobs.values()) {
    if (
      job.article_id === articleId &&
      job.content_hash === contentHash &&
      ACTIVE_STATUSES.includes(job.status)
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
  job.worker_id = WORKER_ID;
  job.started_at = job.started_at || nowIso();
  job.updated_at = nowIso();
  job.error = null;
  job.failure_class = null;
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
 * Content change ⇒ new version job.
 */
export async function enqueueCmsIngestJob(payloadInput = {}) {
  const title = String(payloadInput.title || '').trim();
  const content = String(payloadInput.content || payloadInput.content_md || '').trim();
  if (!title || !content) {
    const err = new Error('title and content are required');
    err.status = 400;
    throw err;
  }
  if (content.length < 40) {
    const err = new Error('Insufficient content for intelligence ingest');
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
      version: 'same',
      message: 'Ingest already queued for this article version (same content hash).',
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
    failure_class: null,
    worker_id: null,
    wake_time_ms: null,
    engine_latency_ms: null,
    queued_at: createdAt,
    created_at: createdAt,
    started_at: null,
    finished_at: null,
    updated_at: createdAt,
    next_attempt_at: createdAt,
  };

  memoryJobs.set(job.id, job);
  const inserted = await dbInsertJob(job);
  if (!inserted.ok && !inserted.skipped) {
    const raced = await dbFindActiveByHash(articleId, hash);
    if (raced) {
      memoryJobs.set(raced.id, raced);
      return {
        ...publicJob(raced),
        already_queued: true,
        version: 'same',
        message: 'Ingest already queued for this article version (same content hash).',
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

  setImmediate(() => {
    processIngestQueue().catch((err) =>
      console.error('[cms-ingest-jobs] kick error', err?.message || err)
    );
  });

  return {
    ...publicJob(job),
    already_queued: false,
    version: 'new',
    message:
      'Ingest job accepted. Worker will wake the engine and finish in the background. Content changes create a new version job.',
  };
}

async function persistJob(job) {
  memoryJobs.set(job.id, job);
  await dbUpdateJob(job.id, jobDbPatch(job));
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
  job.worker_id = WORKER_ID;
  job.updated_at = nowIso();
  await persistJob(job);

  const wake = await wakeEngineUntilReady(engineFetch, 120_000);
  job.wake_time_ms = wake.waitedMs;
  if (!wake.ok) {
    const err = new Error(
      `Engine did not become ready after ${wake.waitedMs}ms (attempt ${job.attempt})`
    );
    err.status = 503;
    throw err;
  }

  job.status = 'processing';
  job.phase = 'ingesting';
  job.updated_at = nowIso();
  await persistJob(job);

  const ingestStarted = Date.now();
  const result = await engineFetch('/v1/kip/ingest/agi', {
    method: 'POST',
    body: job.payload,
    timeoutMs: 120_000,
  });
  job.engine_latency_ms = Date.now() - ingestStarted;

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
  job.failure_class = null;
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
    wake_time_ms: job.wake_time_ms,
    engine_latency_ms: job.engine_latency_ms,
    worker_id: WORKER_ID,
  });
}

async function failOrReschedule(job, error) {
  const message = error?.message || String(error);
  const klass = classifyIngestFailure(error, error?.status);
  job.failure_class = klass;

  if (klass === 'permanent') {
    job.status = 'failed_permanent';
    job.phase = 'dead_letter';
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
    console.warn('[cms-ingest-jobs] permanent failure (dead-letter)', {
      job_id: job.id,
      error: job.error,
    });
    return;
  }

  const canRetry = job.attempt < job.max_attempts;
  if (canRetry) {
    job.status = 'pending';
    job.phase = 'retry_scheduled';
    job.error = message.slice(0, 500);
    job.worker_id = null;
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

  job.status = 'failed_permanent';
  job.phase = 'dead_letter';
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
  console.warn('[cms-ingest-jobs] dead-letter after max attempts', {
    job_id: job.id,
    error: job.error,
    attempts: job.attempt,
  });
}

export async function processIngestQueue() {
  if (workerBusy || !engineFetchRef) return { processed: 0 };
  workerBusy = true;
  let processed = 0;
  try {
    await reclaimStalledJobs();
    while (true) {
      let job = memoryClaimNext();
      if (!job) job = await dbClaimNextJob();
      if (!job) break;
      memoryJobs.set(job.id, job);
      try {
        await runOneJob(job, engineFetchRef);
        processed += 1;
      } catch (error) {
        await failOrReschedule(job, error);
        processed += 1;
      }
    }
  } finally {
    workerBusy = false;
  }
  return { processed, worker_id: WORKER_ID };
}

function startKeepWarm(engineFetch) {
  if (keepWarmStarted) return;
  keepWarmStarted = true;
  if (KEEP_WARM_MS <= 0) return;
  setInterval(() => {
    engineFetch('/v1/health', { timeoutMs: 20_000 }).catch(() => null);
  }, KEEP_WARM_MS);
  setTimeout(() => {
    engineFetch('/v1/health', { timeoutMs: 20_000 }).catch(() => null);
  }, 15_000);
}

/**
 * Start worker loop. Safe to call multiple times.
 * In external mode, the API should call startCmsIngestJobWorker only from the
 * dedicated worker process — set CMS_INGEST_WORKER_MODE=external on the API.
 */
export function startCmsIngestJobWorker(engineFetch, { force = false } = {}) {
  engineFetchRef = engineFetch;
  if (!force && workerMode() === 'external' && process.env.CMS_INGEST_IS_WORKER !== '1') {
    console.info(
      '[cms-ingest-jobs] embedded worker disabled (CMS_INGEST_WORKER_MODE=external); API enqueue-only'
    );
    return { mode: 'external', started: false };
  }

  startKeepWarm(engineFetch);

  if (!reclaimDone) {
    reclaimDone = true;
    reclaimStalledJobs()
      .then((r) => {
        if (r.reclaimed) {
          return processIngestQueue();
        }
        return null;
      })
      .catch((err) => console.error('[cms-ingest-jobs] startup reclaim failed', err?.message || err));
  }

  if (workerStarted) return { mode: workerMode(), started: true, already: true };
  workerStarted = true;
  setInterval(() => {
    processIngestQueue().catch((err) =>
      console.error('[cms-ingest-jobs] tick error', err?.message || err)
    );
  }, WORKER_TICK_MS);
  // Watchdog: reclaim stalls even when queue is idle.
  setInterval(() => {
    reclaimStalledJobs().catch(() => null);
  }, Math.min(STALL_MS, 60_000));

  console.info('[cms-ingest-jobs] worker started', {
    tick_ms: WORKER_TICK_MS,
    keep_warm_ms: KEEP_WARM_MS,
    stall_ms: STALL_MS,
    max_attempts: MAX_ATTEMPTS_DEFAULT,
    worker_id: WORKER_ID,
    mode: workerMode(),
    hostname: os.hostname(),
  });
  return { mode: workerMode(), started: true, worker_id: WORKER_ID };
}

export function isValidJobStatus(status) {
  return JOB_STATUSES.has(status);
}

export function getWorkerInfo() {
  return {
    worker_id: WORKER_ID,
    mode: workerMode(),
    embedded_running: workerStarted,
    max_attempts: MAX_ATTEMPTS_DEFAULT,
    stall_ms: STALL_MS,
    queued_alert_ms: QUEUED_ALERT_MS,
  };
}
