// supabase/functions/bright-service/index.ts
import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const RESEND_API_KEY = Deno.env.get("RESEND_API_KEY")!;

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

Deno.serve(async (req) => {
  try {
    // Accept either JSON body or ?email=...
    let email: string | null = null;

    const ct = req.headers.get("content-type") || "";
    if (ct.includes("application/json")) {
      const body = await req.json().catch(() => ({}));
      email = (body?.email ?? null) as string | null;
    }
    if (!email) {
      const url = new URL(req.url);
      email = url.searchParams.get("email");
    }
    if (!email) return json({ error: "email required" }, 400);

    // Send welcome email via Resend (set and verify your sender in Resend)
    const r = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${RESEND_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        from: "AGI Updates <updates@yourdomain.com>",
        to: email,
        subject: "Welcome to AGI Updates",
        html: `<p>Thanks for subscribing! You'll get an email when we publish new articles.</p>`,
      }),
    });

    if (!r.ok) {
      const t = await r.text();
      console.error("Resend error:", t);
      return json({ error: "email provider failed" }, 502);
    }

    return json({ ok: true, message: `Hello ${email}!` });
  } catch (e) {
    console.error(e);
    return json({ error: "internal error" }, 500);
  }
});
