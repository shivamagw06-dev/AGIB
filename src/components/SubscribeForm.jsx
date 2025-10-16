// components/SubscribeForm.jsx
import { useState } from "react";
import { supabase } from "@/lib/supabaseClient";

export default function SubscribeForm() {
  const [email, setEmail] = useState("");
  const [ok, setOk] = useState(false);
  const [err, setErr] = useState("");

  async function onSubmit(e) {
    e.preventDefault();
    setErr(""); setOk(false);

    // 1) insert subscriber (RLS policy already allows insert)
    const { error } = await supabase.from("subscribers").insert({ email });
    if (error) {
      setErr(error.message.includes("duplicate") ? "Already subscribed" : error.message);
      return;
    }

    try {
      // 2) ask Edge Function to send welcome email (safe; no API key in browser)
      await fetch(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/send-welcome`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          // use anon key to pass auth (function checks for Bearer)
          Authorization: `Bearer ${import.meta.env.VITE_SUPABASE_ANON_KEY}`,
        },
        body: JSON.stringify({ email }),
      });
    } catch (e) {
      console.error("send-welcome failed", e);
      // don't surface as a user error; they’re already subscribed
    }

    setOk(true);
    setEmail("");
  }

  return (
    <form onSubmit={onSubmit} className="flex gap-2">
      <input
        type="email"
        value={email}
        onChange={(e)=>setEmail(e.target.value)}
        placeholder="you@example.com"
        className="px-3 py-2 rounded border border-slate-300 w-64"
        required
      />
      <button className="px-4 py-2 rounded bg-amber-500 text-white">Subscribe</button>
      {ok && <span className="text-emerald-600 text-sm">Check your inbox ✉️</span>}
      {err && <span className="text-rose-600 text-sm">{err}</span>}
    </form>
  );
}
