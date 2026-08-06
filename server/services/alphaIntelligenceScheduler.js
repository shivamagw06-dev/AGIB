/**
 * Alpha Focus scheduler.
 *
 * Runs after the Indian market close and derives factors / a research monitor
 * from data already in the warehouse. It never calls vendors and never starts
 * a historical backfill. Intraday prices remain the responsibility of the
 * small Hedge Fund live-quote scheduler.
 */

let timer = null;
let lastRun = null;
let lastSuccessDate = null;

function enabled() {
  return String(process.env.ALPHA_INTELLIGENCE_SCHEDULER || 'false').toLowerCase() === 'true';
}

function istParts(d = new Date()) {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', hour12: false, weekday: 'short',
  }).formatToParts(d);
  const get = (type) => parts.find((part) => part.type === type)?.value;
  return {
    date: `${get('year')}-${get('month')}-${get('day')}`,
    hour: Number(get('hour')), minute: Number(get('minute')), weekday: get('weekday'),
  };
}

function due(parts) {
  return !['Sat', 'Sun'].includes(String(parts.weekday || ''))
    && (parts.hour > 18 || (parts.hour === 18 && parts.minute >= 50));
}

function engineConfig() {
  let baseUrl = String(process.env.INTELLIGENCE_ENGINE_URL || 'http://127.0.0.1:8100').replace(/\/$/, '');
  if (baseUrl && !/^https?:\/\//i.test(baseUrl)) baseUrl = `https://${baseUrl}`;
  return { baseUrl, token: String(process.env.INTELLIGENCE_ENGINE_TOKEN || 'dev-intelligence-token').trim() };
}

export function getAlphaIntelligenceSchedulerStatus() {
  return {
    enabled: Boolean(timer),
    lastRun,
    lastSuccessDate,
    target: '18:50 IST weekdays after the live EOD feeds complete',
    policy: 'derived Alpha factors only; no vendor collection or historical backfill',
  };
}

export async function triggerAlphaIntelligenceRefresh({ force = false } = {}) {
  const now = istParts();
  if (!force && lastSuccessDate === now.date) return { ok: true, skipped: true, reason: 'already_ran_today', date: now.date };
  if (!force && !due(now)) return { ok: true, skipped: true, reason: 'outside_post_close_window', now };
  const { baseUrl, token } = engineConfig();
  try {
    const response = await fetch(`${baseUrl}/v1/hedge-fund-lab/alpha-refresh`, {
      method: 'POST',
      headers: { Accept: 'application/json', 'Content-Type': 'application/json', Authorization: `Bearer ${token}`, 'X-AGI-Intelligence-Token': token },
      body: JSON.stringify({ snapshot_limit: Number(process.env.ALPHA_SNAPSHOT_LIMIT || 25) }),
      signal: AbortSignal.timeout(240_000),
    });
    const data = await response.json().catch(() => ({}));
    const ok = Boolean(response.ok && data.ok !== false);
    lastRun = { at: new Date().toISOString(), ok, date: now.date, result: data };
    if (ok) lastSuccessDate = now.date;
    if (ok) console.info('[alpha-intelligence] stored-data factor refresh complete', now.date);
    else console.warn('[alpha-intelligence] refresh failed', data.error || response.status);
    return { ...data, ok, date: now.date, forced: force };
  } catch (error) {
    lastRun = { at: new Date().toISOString(), ok: false, date: now.date, error: error.message };
    console.warn('[alpha-intelligence] refresh error:', error.message);
    return { ok: false, error: error.message, date: now.date };
  }
}

export function startAlphaIntelligenceScheduler() {
  if (timer || !enabled()) {
    if (!enabled()) console.info('[alpha-intelligence] scheduler disabled (ALPHA_INTELLIGENCE_SCHEDULER=false)');
    return getAlphaIntelligenceSchedulerStatus();
  }
  const tick = () => triggerAlphaIntelligenceRefresh().catch(() => {});
  setTimeout(tick, 90_000);
  timer = setInterval(tick, 60_000);
  timer.unref?.();
  console.info('[alpha-intelligence] scheduler active — stored-data refresh after 18:50 IST');
  return getAlphaIntelligenceSchedulerStatus();
}
