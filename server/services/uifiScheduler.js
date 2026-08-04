/**
 * UIFI schedules — weekly profile/competitors; monthly coverage audit tick.
 * Daily key-ratios remain on valuationRatiosScheduler (Phase 7.4D).
 */

import { refreshUpstoxFundamentals, getUifiCoverage } from './upstoxFundamentalsRefresh.js';

let timer = null;
let lastTick = null;
let lastResult = null;

function enabled() {
  return String(process.env.UIFI_SCHEDULER || 'true').toLowerCase() !== 'false';
}

function istParts(d = new Date()) {
  const fmt = new Intl.DateTimeFormat('en-GB', {
    timeZone: 'Asia/Kolkata',
    weekday: 'short',
    hour: '2-digit',
    minute: '2-digit',
    day: '2-digit',
    hour12: false,
  });
  const parts = Object.fromEntries(fmt.formatToParts(d).map((p) => [p.type, p.value]));
  return {
    weekday: parts.weekday,
    hour: Number(parts.hour),
    minute: Number(parts.minute),
    day: Number(parts.day),
  };
}

async function runWeekly() {
  const profile = await refreshUpstoxFundamentals({ dataset: 'profile', limit: 80, concurrency: 3 });
  const competitors = await refreshUpstoxFundamentals({
    dataset: 'competitors', limit: 60, concurrency: 2,
  });
  return { profile, competitors };
}

async function runMonthlyAudit() {
  const coverage = await getUifiCoverage();
  return { coverage };
}

export function startUifiScheduler() {
  if (!enabled() || timer) return getUifiSchedulerStatus();
  let lastWeeklyKey = '';
  let lastMonthlyKey = '';

  timer = setInterval(async () => {
    const p = istParts();
    // Sunday 08:00 IST — weekly profile + competitors
    const weeklyKey = `${p.weekday}-${p.hour}`;
    if (p.weekday === 'Sun' && p.hour === 8 && weeklyKey !== lastWeeklyKey) {
      lastWeeklyKey = weeklyKey;
      lastTick = new Date().toISOString();
      try {
        lastResult = { kind: 'weekly', ...(await runWeekly()) };
      } catch (err) {
        lastResult = { kind: 'weekly', ok: false, error: err?.message || String(err) };
      }
    }
    // 1st of month 11:00 IST — coverage audit
    const monthlyKey = `${p.day}-${p.hour}`;
    if (p.day === 1 && p.hour === 11 && monthlyKey !== lastMonthlyKey) {
      lastMonthlyKey = monthlyKey;
      lastTick = new Date().toISOString();
      try {
        lastResult = { kind: 'monthly', ...(await runMonthlyAudit()) };
      } catch (err) {
        lastResult = { kind: 'monthly', ok: false, error: err?.message || String(err) };
      }
    }
  }, 60_000);

  if (typeof timer.unref === 'function') timer.unref();
  return getUifiSchedulerStatus();
}

export function getUifiSchedulerStatus() {
  return {
    ok: true,
    enabled: enabled(),
    running: Boolean(timer),
    schedules: {
      weekly: 'Sunday 08:00 IST — profile + competitors',
      monthly: '1st 11:00 IST — coverage audit',
      daily_key_ratios: '18:15 IST via valuationRatiosScheduler',
    },
    lastTick,
    lastResult,
  };
}
