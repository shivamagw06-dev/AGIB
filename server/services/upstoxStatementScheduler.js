/**
 * Daily post-close Upstox statement refresh.
 *
 * Statements change only on results, so this deliberately runs once after
 * market close and rotates a small, rate-safe batch through the ISIN universe.
 * It never runs on page requests and never shares the web engine process.
 */

import { refreshUpstoxFundamentals } from './upstoxFundamentalsRefresh.js';

let timer = null;
let inFlight = false;
let lastRun = null;
let lastSuccessDate = null;

function enabled() {
  return String(process.env.UPSTOX_STATEMENT_SCHEDULER || 'true').toLowerCase() !== 'false';
}

function istParts(d = new Date()) {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', hour12: false, weekday: 'short',
  }).formatToParts(d);
  const get = (type) => parts.find((part) => part.type === type)?.value;
  return { date: `${get('year')}-${get('month')}-${get('day')}`, hour: Number(get('hour')), minute: Number(get('minute')), weekday: get('weekday') };
}

function due(parts) {
  return !['Sat', 'Sun'].includes(String(parts.weekday || '')) && parts.hour === 18 && parts.minute >= 35;
}

function dayNumber(date) {
  return Math.floor(Date.parse(`${date}T00:00:00Z`) / 86_400_000);
}

export function getUpstoxStatementSchedulerStatus() {
  return {
    enabled: enabled(),
    running: Boolean(timer),
    inFlight,
    lastRun,
    lastSuccessDate,
    target: '18:35 IST weekdays',
    batchSize: Number(process.env.UPSTOX_STATEMENT_INCREMENTAL_BATCH || 12),
    note: 'One small rotating batch per weekday; full statements are normalized into the warehouse.',
  };
}

export async function triggerUpstoxStatementRefresh({ force = false } = {}) {
  const now = istParts();
  if (inFlight) return { ok: true, skipped: true, reason: 'already_running' };
  if (!force && lastSuccessDate === now.date) return { ok: true, skipped: true, reason: 'already_ran_today', date: now.date };
  if (!force && !due(now)) return { ok: true, skipped: true, reason: 'outside_post_close_window', now };
  inFlight = true;
  try {
    const batchSize = Math.max(1, Number(process.env.UPSTOX_STATEMENT_INCREMENTAL_BATCH || 12));
    const result = await refreshUpstoxFundamentals({
      dataset: 'statements', limit: batchSize,
      concurrency: Math.max(1, Number(process.env.UPSTOX_STATEMENT_CONCURRENCY || 1)),
      offset: dayNumber(now.date) * batchSize,
    });
    lastRun = { at: new Date().toISOString(), date: now.date, ok: Boolean(result.ok), fetched: result.fetched || 0, errors: (result.errors || []).length, selection: result.selection || null, error: result.error || null };
    if (result.ok) lastSuccessDate = now.date;
    return { ...result, date: now.date, forced: force };
  } catch (error) {
    lastRun = { at: new Date().toISOString(), date: now.date, ok: false, error: error.message };
    return { ok: false, error: error.message, date: now.date };
  } finally {
    inFlight = false;
  }
}

export function startUpstoxStatementScheduler() {
  if (timer || !enabled()) return getUpstoxStatementSchedulerStatus();
  const tick = () => triggerUpstoxStatementRefresh().catch(() => {});
  setTimeout(tick, 60_000);
  timer = setInterval(tick, 60_000);
  timer.unref?.();
  console.info('[upstox-statements] scheduler active — 18:35 IST weekdays, rotating batches');
  return getUpstoxStatementSchedulerStatus();
}
