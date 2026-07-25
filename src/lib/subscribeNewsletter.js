import { supabase } from '@/lib/supabaseClient';
import { sendWelcomeEmail } from '@/lib/newsletterClient';

/**
 * Insert/upsert subscriber and best-effort send welcome email via Resend.
 */
export async function subscribeNewsletter(email, { userId = null } = {}) {
  const value = String(email || '').trim().toLowerCase();
  if (!value) throw new Error('Email is required.');

  const row = {
    email: value,
    is_active: true,
    ...(userId ? { user_id: userId } : {}),
  };

  let error = null;
  const upsert = await supabase.from('subscribers').upsert(row, { onConflict: 'email' });
  error = upsert.error;

  if (error) {
    // Fallback for schemas without upsert/unique email constraint.
    const insert = await supabase.from('subscribers').insert(row);
    if (insert.error && !/duplicate|unique/i.test(insert.error.message || '')) {
      throw new Error(insert.error.message || 'Subscription failed.');
    }
    if (insert.error && /duplicate|unique/i.test(insert.error.message || '')) {
      throw new Error('This email is already subscribed.');
    }
  }

  const welcome = await sendWelcomeEmail(value);
  return { email: value, welcome };
}
