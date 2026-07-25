import { useMemo, useState } from 'react';
import { Check, Loader2 } from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';
import { subscribeNewsletter } from '@/lib/subscribeNewsletter';
import { AGI_LETTERS, defaultLetterPreferences } from '@/config/agiLetters';

export default function NewsletterSection({ initialSelected = null }) {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const initialPrefs = useMemo(
    () => defaultLetterPreferences(initialSelected),
    [initialSelected]
  );
  const [prefs, setPrefs] = useState(initialPrefs);

  const toggle = (key) => {
    setPrefs((prev) => {
      const next = { ...prev, [key]: !prev[key] };
      if (!Object.values(next).some(Boolean)) next.agi_markets = true;
      return next;
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await subscribeNewsletter(email, { preferences: prefs, source: 'homepage' });
      toast({
        title: 'Subscribed to AGI Letters',
        description: 'Check your inbox for a welcome email from updates@agarwalglobalinvestments.com.',
      });
      setEmail('');
    } catch (err) {
      toast({ title: 'Subscription failed', description: err.message, variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="py-12 border-t border-[#dddddd] bg-[#fafafa]" aria-labelledby="agi-letters-heading">
      <div className="max-w-[1600px] mx-auto px-4 sm:px-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start border border-[#dddddd] bg-white p-6 md:p-10">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-wider text-[#ff6600]">AGI Letters</p>
            <h2 id="agi-letters-heading" className="mt-2 text-2xl font-bold text-[#111111]">
              Four desks. One inbox.
            </h2>
            <p className="mt-2 text-sm text-[#555555] max-w-xl">
              Choose the AGI publications you want. Each letter has a clear schedule and purpose.
            </p>

            <div className="mt-6 space-y-4">
              {AGI_LETTERS.map((letter) => (
                <div key={letter.key} className="border-b border-[#eeeeee] pb-4 last:border-0 last:pb-0">
                  <div className="flex items-baseline justify-between gap-3">
                    <h3 className="text-sm font-bold text-[#111111]">{letter.name}</h3>
                    <span className="text-[11px] font-semibold text-[#767676] whitespace-nowrap">
                      {letter.schedule}
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-[#444444]">{letter.tagline}</p>
                </div>
              ))}
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              {AGI_LETTERS.map((letter) => (
                <label
                  key={letter.key}
                  className={`flex cursor-pointer items-start gap-3 border px-3 py-3 transition-colors ${
                    prefs[letter.key]
                      ? 'border-[#111111] bg-[#fafafa]'
                      : 'border-[#dddddd] hover:border-[#999999]'
                  }`}
                >
                  <input
                    type="checkbox"
                    className="mt-1"
                    checked={Boolean(prefs[letter.key])}
                    onChange={() => toggle(letter.key)}
                  />
                  <span className="min-w-0">
                    <span className="block text-sm font-bold text-[#111111]">{letter.name}</span>
                    <span className="block text-xs text-[#767676] mt-0.5">{letter.schedule}</span>
                  </span>
                  {prefs[letter.key] ? <Check className="ml-auto mt-0.5 h-4 w-4 text-[#008001] shrink-0" /> : null}
                </label>
              ))}
            </div>

            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Email address"
              disabled={loading}
              className="w-full border border-[#cccccc] px-4 py-3 text-sm focus:border-[#111111] focus:outline-none"
            />
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[#111111] text-white text-sm font-bold py-3 hover:bg-[#333333] transition-colors disabled:opacity-60 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" /> Subscribing…
                </>
              ) : (
                'Subscribe to selected letters'
              )}
            </button>
            <p className="text-[10px] text-[#767676]">
              Free · Unsubscribe anytime · Sent from updates@agarwalglobalinvestments.com
            </p>
          </form>
        </div>
      </div>
    </section>
  );
}
