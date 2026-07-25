import { Router } from 'express';
import rateLimit from 'express-rate-limit';

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function siteUrl() {
  return (process.env.PUBLIC_SITE_URL || process.env.BASE_URL || 'https://agarwalglobalinvestments.com').replace(
    /\/$/,
    ''
  );
}

function newsletterFrom() {
  return (
    process.env.NEWSLETTER_FROM_EMAIL ||
    process.env.UPDATES_FROM_EMAIL ||
    'AGI Updates <updates@agarwalglobalinvestments.com>'
  );
}

function escapeHtml(value = '') {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function excerptFromHtml(html = '', maxChars = 280) {
  const txt = String(html)
    .replace(/<\/?[^>]+(>|$)/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
  if (txt.length <= maxChars) return txt;
  return `${txt.slice(0, maxChars).trim()}…`;
}

async function getSupabaseAdmin() {
  const supabaseUrl = (process.env.SUPABASE_URL || '').trim();
  const serviceKey = (process.env.SUPABASE_SERVICE_ROLE_KEY || '').trim();
  if (!supabaseUrl || !serviceKey) {
    const err = new Error('Supabase admin credentials unavailable.');
    err.code = 'SUPABASE_ADMIN_MISSING';
    throw err;
  }
  const { createClient } = await import('@supabase/supabase-js');
  return createClient(supabaseUrl, serviceKey, {
    auth: { autoRefreshToken: false, persistSession: false },
  });
}

async function sendWithResend(payload) {
  const key = (process.env.RESEND_API_KEY || '').trim();
  if (!key) {
    const err = new Error('RESEND_API_KEY is not configured.');
    err.code = 'RESEND_MISSING';
    throw err;
  }
  const resp = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${key}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  const text = await resp.text().catch(() => '');
  let json = null;
  try {
    json = text ? JSON.parse(text) : null;
  } catch {
    json = null;
  }
  if (!resp.ok) {
    const err = new Error(json?.message || text.slice(0, 200) || `Resend failed (${resp.status})`);
    err.status = resp.status;
    throw err;
  }
  return json;
}

async function sendBatchWithResend(items) {
  const key = (process.env.RESEND_API_KEY || '').trim();
  if (!key) {
    const err = new Error('RESEND_API_KEY is not configured.');
    err.code = 'RESEND_MISSING';
    throw err;
  }
  const resp = await fetch('https://api.resend.com/emails/batch', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${key}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(items),
  });
  const text = await resp.text().catch(() => '');
  let json = null;
  try {
    json = text ? JSON.parse(text) : null;
  } catch {
    json = null;
  }
  if (!resp.ok) {
    const err = new Error(json?.message || text.slice(0, 200) || `Resend batch failed (${resp.status})`);
    err.status = resp.status;
    throw err;
  }
  return json;
}

function articleHtml({ title, summary, slug, email }) {
  const site = siteUrl();
  const url = `${site}/article/${encodeURIComponent(slug)}`;
  const unsub = `${site}/unsubscribe?email=${encodeURIComponent(email)}`;
  return `<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f5f7fa;font-family:Arial,sans-serif;color:#18202b;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f5f7fa;padding:28px 12px;">
    <tr><td align="center">
      <table role="presentation" width="100%" style="max-width:560px;background:#ffffff;border:1px solid #dce1e7;">
        <tr>
          <td style="background:#0d1d33;color:#ffffff;padding:22px 26px;">
            <div style="font-size:12px;letter-spacing:0.12em;text-transform:uppercase;color:#a7c5ec;">AGI Updates</div>
            <div style="margin-top:8px;font-size:22px;font-weight:700;">${escapeHtml(title)}</div>
          </td>
        </tr>
        <tr>
          <td style="padding:26px;">
            ${summary ? `<p style="margin:0 0 18px;font-size:15px;line-height:1.6;color:#445066;">${escapeHtml(summary)}</p>` : ''}
            <p style="margin:0 0 22px;">
              <a href="${escapeHtml(url)}" style="display:inline-block;background:#0d1d33;color:#ffffff;text-decoration:none;padding:12px 18px;font-size:14px;font-weight:700;">
                Read the article
              </a>
            </p>
            <p style="margin:0;font-size:12px;line-height:1.6;color:#7b8491;">
              You receive AGI Updates because you subscribed at ${escapeHtml(site)}.
              <a href="${escapeHtml(unsub)}" style="color:#274c77;">Unsubscribe</a>
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>`;
}

function welcomeHtml(email) {
  const site = siteUrl();
  const unsub = `${site}/unsubscribe?email=${encodeURIComponent(email)}`;
  return `<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f5f7fa;font-family:Arial,sans-serif;color:#18202b;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f5f7fa;padding:28px 12px;">
    <tr><td align="center">
      <table role="presentation" width="100%" style="max-width:560px;background:#ffffff;border:1px solid #dce1e7;">
        <tr>
          <td style="background:#0d1d33;color:#ffffff;padding:22px 26px;">
            <div style="font-size:12px;letter-spacing:0.12em;text-transform:uppercase;color:#a7c5ec;">AGI Updates</div>
            <div style="margin-top:8px;font-size:22px;font-weight:700;">Welcome to AGI Updates</div>
          </td>
        </tr>
        <tr>
          <td style="padding:26px;">
            <p style="margin:0 0 14px;font-size:15px;line-height:1.6;">Thanks for subscribing.</p>
            <p style="margin:0 0 18px;font-size:15px;line-height:1.6;color:#445066;">
              You will receive Agarwal Global Investments research and market updates when we publish new articles.
            </p>
            <p style="margin:0 0 18px;">
              <a href="${escapeHtml(site)}" style="display:inline-block;background:#0d1d33;color:#ffffff;text-decoration:none;padding:12px 18px;font-size:14px;font-weight:700;">
                Visit AGI
              </a>
            </p>
            <p style="margin:0;font-size:12px;line-height:1.6;color:#7b8491;">
              <a href="${escapeHtml(unsub)}" style="color:#274c77;">Unsubscribe</a>
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>`;
}

export default function createNewsletterRouter() {
  const router = Router();

  const notifyLimiter = rateLimit({
    windowMs: 15 * 60 * 1000,
    max: 20,
    standardHeaders: true,
    legacyHeaders: false,
    message: { error: 'Too many newsletter notify requests. Try again later.' },
  });

  const welcomeLimiter = rateLimit({
    windowMs: 15 * 60 * 1000,
    max: 40,
    standardHeaders: true,
    legacyHeaders: false,
    message: { error: 'Too many welcome email requests. Try again later.' },
  });

  router.get('/health', (_req, res) => {
    res.json({
      ok: true,
      resend: Boolean((process.env.RESEND_API_KEY || '').trim()),
      from: newsletterFrom(),
      supabaseAdmin: Boolean(
        (process.env.SUPABASE_URL || '').trim() &&
          (process.env.SUPABASE_SERVICE_ROLE_KEY || '').trim()
      ),
    });
  });

  router.post('/welcome', welcomeLimiter, async (req, res) => {
    try {
      const email = String(req.body?.email || '').trim().toLowerCase();
      if (!EMAIL_RE.test(email)) {
        return res.status(400).json({ error: 'Valid email is required.' });
      }

      await sendWithResend({
        from: newsletterFrom(),
        to: email,
        subject: 'Welcome to AGI Updates',
        html: welcomeHtml(email),
      });

      return res.json({ ok: true });
    } catch (err) {
      console.error('[newsletter/welcome]', err?.message || err);
      if (err?.code === 'RESEND_MISSING') {
        return res.status(503).json({ ok: false, skipped: true, reason: err.message });
      }
      return res.status(500).json({ error: 'Failed to send welcome email.' });
    }
  });

  router.post('/notify-subscribers', notifyLimiter, async (req, res) => {
    try {
      const title = String(req.body?.title || '').trim();
      const slug = String(req.body?.slug || '').trim();
      const summary = String(
        req.body?.summary || req.body?.excerpt || excerptFromHtml(req.body?.body || '')
      ).trim();

      if (!title || !slug) {
        return res.status(400).json({ error: 'title and slug are required.' });
      }

      const admin = await getSupabaseAdmin();
      const { data: list, error } = await admin
        .from('subscribers')
        .select('email')
        .eq('is_active', true);

      if (error) throw error;
      const emails = (list || [])
        .map((row) => String(row.email || '').trim().toLowerCase())
        .filter((email) => EMAIL_RE.test(email));

      if (!emails.length) {
        return res.json({ ok: true, sent: 0, skipped: true, reason: 'No active subscribers.' });
      }

      const from = newsletterFrom();
      let sent = 0;

      for (let i = 0; i < emails.length; i += 50) {
        const chunk = emails.slice(i, i + 50);
        const items = chunk.map((email) => ({
          from,
          to: [email],
          subject: `New from AGI: ${title}`,
          html: articleHtml({ title, summary, slug, email }),
        }));
        await sendBatchWithResend(items);
        sent += chunk.length;
      }

      return res.json({ ok: true, sent, from });
    } catch (err) {
      console.error('[newsletter/notify-subscribers]', err?.message || err);
      if (err?.code === 'RESEND_MISSING' || err?.code === 'SUPABASE_ADMIN_MISSING') {
        return res.status(503).json({ ok: false, skipped: true, reason: err.message });
      }
      return res.status(500).json({ error: 'Failed to notify subscribers.' });
    }
  });

  return router;
}
