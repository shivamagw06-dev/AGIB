// supabase/functions/notify-new-article/index.ts
import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const RESEND_API_KEY = Deno.env.get("re_QPXXxVoU_MLMbb8D5hUYmSbG8crJgeJfw")!;
const SITE_ORIGIN = Deno.env.get("SITE_ORIGIN") || "https://agarwalglobalinvestments.com";

type Payload = { title: string; slug: string; summary?: string };

Deno.serve(async (req) => {
  try {
    // Basic protection: require either Authorization header OR shared secret
    const auth = req.headers.get("authorization") || "";
    const cronSecret = req.headers.get("x-cron-secret");
    const allowed =
      auth.startsWith("Bearer ") ||
      (cronSecret && cronSecret === Deno.env.get("CRON_SECRET"));

    if (!allowed) return new Response("Unauthorized", { status: 401 });

    const { title, slug, summary } = (await req.json()) as Payload;
    if (!title || !slug) return new Response("Missing title/slug", { status: 400 });

    // Fetch active subscribers via PostgREST (functions run with service role)
    const { SUPABASE_URL, SUPABASE_ANON_KEY } = Deno.env.toObject();
    const r = await fetch(`${SUPABASE_URL}/rest/v1/subscribers?select=email&is_active=eq.true`, {
      headers: { apikey: SUPABASE_ANON_KEY!, Authorization: `Bearer ${SUPABASE_ANON_KEY}` },
    });
    if (!r.ok) return new Response("Failed to fetch subscribers", { status: 500 });
    const list = (await r.json()) as { email: string }[];

    if (!Array.isArray(list) || list.length === 0) {
      return new Response("No subscribers", { status: 200 });
    }

    const url = `${SITE_ORIGIN}/article/${encodeURIComponent(slug)}`;
    const subject = `New article: ${title}`;
    const html = `
      <div style="font-family:system-ui,Segoe UI,Roboto,Arial">
        <h2>${title}</h2>
        ${summary ? `<p>${summary}</p>` : ""}
        <p><a href="${url}">Read it on Agarwal Global Investments →</a></p>
        <hr/>
        <p style="color:#6b7280;font-size:12px">
          You received this because you subscribed at ${SITE_ORIGIN}.
          <a href="${SITE_ORIGIN}/unsubscribe?email={{email}}">Unsubscribe</a>.
        </p>
      </div>
    `;

    // send in chunks of ~80 to avoid provider limits
    for (let i = 0; i < list.length; i += 80) {
      const chunk = list.slice(i, i + 80).map((x) => x.email);
      const send = await fetch("https://api.resend.com/emails", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${RESEND_API_KEY}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          from: "AGI Updates <updates@yourdomain.com>", // set this sender in Resend
          to: chunk,
          subject,
          html,
        }),
      });
      if (!send.ok) {
        const txt = await send.text();
        console.error("Resend error:", txt);
        return new Response("Email provider failed", { status: 502 });
      }
    }

    return new Response("ok", { status: 200 });
  } catch (e) {
    console.error(e);
    return new Response("Failed", { status: 500 });
  }
});

