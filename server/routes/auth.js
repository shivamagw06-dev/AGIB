import { Router } from 'express';
import rateLimit from 'express-rate-limit';

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function escapeHtml(value = '') {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function brandedVerificationHtml({ fullName, actionLink, siteUrl }) {
  const name = escapeHtml(fullName || 'Investor');
  const link = escapeHtml(actionLink);
  const site = escapeHtml(siteUrl);
  const logo = `${siteUrl.replace(/\/$/, '')}/agi-logo.png`;
  return `<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f5f7fa;font-family:Arial,sans-serif;color:#18202b;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f5f7fa;padding:32px 12px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" style="max-width:560px;background:#ffffff;border:1px solid #dce1e7;">
          <tr>
            <td style="background:#0d1d33;color:#ffffff;padding:24px 28px;">
              <img src="${escapeHtml(logo)}" alt="Agarwal Global Investments" width="72" height="64" style="display:block;width:72px;height:auto;border:0;" />
              <div style="margin-top:14px;font-size:12px;letter-spacing:0.12em;text-transform:uppercase;color:#d4af37;">Agarwal Global Investments</div>
              <div style="margin-top:10px;font-size:24px;font-weight:700;">Verify your AGI account</div>
            </td>
          </tr>
          <tr>
            <td style="padding:28px;">
              <p style="margin:0 0 14px;font-size:15px;line-height:1.6;">Hello ${name},</p>
              <p style="margin:0 0 18px;font-size:15px;line-height:1.6;color:#445066;">
                Welcome to Agarwal Global Investments. Confirm your email to activate your secure research account.
              </p>
              <p style="margin:0 0 24px;">
                <a href="${link}" style="display:inline-block;background:#0d1d33;color:#ffffff;text-decoration:none;padding:12px 18px;font-size:14px;font-weight:700;">
                  Verify email address
                </a>
              </p>
              <p style="margin:0 0 10px;font-size:13px;line-height:1.6;color:#667085;">
                If the button does not work, copy and paste this link into your browser:
              </p>
              <p style="margin:0 0 18px;font-size:12px;word-break:break-all;color:#274c77;">${link}</p>
              <p style="margin:0;font-size:12px;line-height:1.6;color:#7b8491;">
                This link expires for your security. If you did not create an AGI account, you can ignore this email.
              </p>
            </td>
          </tr>
          <tr>
            <td style="border-top:1px solid #e8edf2;padding:16px 28px;font-size:11px;color:#7b8491;">
              Support: support@agarwalglobalinvestments.com · <a href="${site}" style="color:#274c77;">${site}</a>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>`;
}

async function sendEmail({ to, subject, html }) {
  const from =
    process.env.FROM_EMAIL ||
    process.env.AUTH_FROM_EMAIL ||
    'Agarwal Global Investments <support@agarwalglobalinvestments.com>';

  const sendgridKey = (process.env.SENDGRID_API_KEY || '').trim();
  if (sendgridKey) {
    const sgMail = (await import('@sendgrid/mail')).default;
    sgMail.setApiKey(sendgridKey);
    await sgMail.send({ to, from, subject, html });
    return { provider: 'sendgrid' };
  }

  const resendKey = (process.env.RESEND_API_KEY || '').trim();
  if (resendKey) {
    const resp = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${resendKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ from, to, subject, html }),
    });
    if (!resp.ok) {
      const body = await resp.text().catch(() => '');
      throw new Error(`Resend failed (${resp.status}): ${body.slice(0, 200)}`);
    }
    return { provider: 'resend' };
  }

  const err = new Error('No email provider configured (SENDGRID_API_KEY or RESEND_API_KEY).');
  err.code = 'EMAIL_PROVIDER_MISSING';
  throw err;
}

export default function createAuthRouter() {
  const router = Router();

  const authLimiter = rateLimit({
    windowMs: 15 * 60 * 1000,
    max: 12,
    standardHeaders: true,
    legacyHeaders: false,
    message: { error: 'Too many auth email requests. Try again later.' },
  });

  router.post('/send-verification', authLimiter, async (req, res) => {
    try {
      const email = String(req.body?.email || '').trim().toLowerCase();
      const fullName = String(req.body?.fullName || '').trim();
      const redirectTo = String(req.body?.redirectTo || '').trim();
      const siteUrl = (process.env.PUBLIC_SITE_URL || 'https://agarwalglobalinvestments.com').replace(/\/$/, '');

      if (!EMAIL_RE.test(email)) {
        return res.status(400).json({ error: 'Valid email is required.' });
      }

      const supabaseUrl = (process.env.SUPABASE_URL || '').trim();
      const serviceKey = (process.env.SUPABASE_SERVICE_ROLE_KEY || '').trim();
      if (!supabaseUrl || !serviceKey) {
        return res.status(503).json({
          ok: false,
          skipped: true,
          reason: 'Supabase admin credentials unavailable; relying on default Auth email.',
        });
      }

      const { createClient } = await import('@supabase/supabase-js');
      const admin = createClient(supabaseUrl, serviceKey, {
        auth: { autoRefreshToken: false, persistSession: false },
      });

      const { data, error } = await admin.auth.admin.generateLink({
        type: 'signup',
        email,
        options: {
          redirectTo: redirectTo || `${siteUrl}/verify-email`,
        },
      });
      if (error) throw error;

      const actionLink =
        data?.properties?.action_link ||
        data?.action_link ||
        null;
      if (!actionLink) {
        return res.status(502).json({ error: 'Unable to generate verification link.' });
      }

      try {
        const sent = await sendEmail({
          to: email,
          subject: 'Verify your Agarwal Global Investments account',
          html: brandedVerificationHtml({ fullName, actionLink, siteUrl }),
        });
        return res.json({ ok: true, provider: sent.provider });
      } catch (mailErr) {
        if (mailErr?.code === 'EMAIL_PROVIDER_MISSING') {
          return res.status(503).json({
            ok: false,
            skipped: true,
            reason: mailErr.message,
            note: 'Configure SENDGRID_API_KEY or RESEND_API_KEY, or use Supabase custom SMTP templates.',
          });
        }
        throw mailErr;
      }
    } catch (err) {
      console.error('[auth/send-verification]', err?.message || err);
      return res.status(500).json({ error: 'Failed to send verification email.' });
    }
  });

  router.get('/health', (_req, res) => {
    res.json({
      ok: true,
      sendgrid: Boolean((process.env.SENDGRID_API_KEY || '').trim()),
      resend: Boolean((process.env.RESEND_API_KEY || '').trim()),
      supabaseAdmin: Boolean(
        (process.env.SUPABASE_URL || '').trim() &&
          (process.env.SUPABASE_SERVICE_ROLE_KEY || '').trim()
      ),
    });
  });

  return router;
}
