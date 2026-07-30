# Fix: cannot sign up / no verification email

## Confirmed production failure

Supabase Auth returns:

`Database error saving new user`

for **new** signups. This is almost always a broken `auth.users` → `public.profiles` trigger.

Supabase’s own SMTP recovery mail also fails (`Error sending recovery email`).  
AGI branded Resend path works for **existing** users via:

`POST /api/auth/send-verification` → `magiclink`

## Immediate founder unblock

For `shivam.agw06@gmail.com`, send:

```bash
curl -X POST https://finance-news-backend-19i5.onrender.com/api/auth/send-verification \
  -H 'Content-Type: application/json' \
  -d '{"email":"shivam.agw06@gmail.com","fullName":"Shivam","redirectTo":"https://agarwalglobalinvestments.com/verify-email"}'
```

Check inbox/spam for **support@agarwalglobalinvestments.com**.

## Permanent fix (run in Supabase SQL Editor)

Open:

https://supabase.com/dashboard/project/zrvdtpxfmuijhionbaxr/sql/new

Paste and run the full contents of:

`supabase/migrations/20260726100000_fix_auth_signup_profiles_trigger.sql`

Then verify:

```bash
curl -sS https://zrvdtpxfmuijhionbaxr.supabase.co/auth/v1/signup \
  -H "apikey: $ANON_KEY" -H "Authorization: Bearer $ANON_KEY" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"agi.probe.$(date +%s)@example.com\",\"password\":\"TestPass123!@#\"}"
```

Expected: HTTP 200 (not `Database error saving new user`).

## Also configure Supabase SMTP (Resend)

Authentication → SMTP:

- Host: `smtp.resend.com`
- Port: `465`
- Username: `resend`
- Password: Resend API key
- Sender: `support@agarwalglobalinvestments.com`
