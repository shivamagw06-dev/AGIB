import { useState } from 'react';
import { Check, Loader2 } from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/lib/supabaseClient';

const BENEFITS = [
  'Morning Market Update',
  'Mid-day Update',
  'Market Close Summary',
  'Weekly Research Notes',
  'Special Reports',
];

export default function NewsletterSection() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const { error } = await supabase.from('subscribers').insert({ email: email.trim() });
      if (error) {
        throw new Error(
          error.message?.includes('duplicate') ? 'Already subscribed.' : error.message
        );
      }
      toast({ title: 'Subscribed', description: 'Welcome to AGI Research Brief.' });
      setEmail('');
    } catch (err) {
      toast({ title: 'Subscription failed', description: err.message, variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="py-12 border-t border-[#dddddd] bg-[#fafafa]">
      <div className="max-w-[1280px] mx-auto px-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center border border-[#dddddd] bg-white p-6 md:p-10">
          <div>
            <h2 className="text-2xl font-bold text-[#111111]">Join Thousands of Investors</h2>
            <p className="text-sm text-[#555555] mt-2">Receive:</p>
            <ul className="mt-4 space-y-2">
              {BENEFITS.map((b) => (
                <li key={b} className="flex items-center gap-2 text-sm text-[#333333]">
                  <Check className="w-4 h-4 text-[#008001] shrink-0" />
                  {b}
                </li>
              ))}
            </ul>
          </div>

          <form onSubmit={handleSubmit} className="space-y-3">
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
                'Subscribe'
              )}
            </button>
            <p className="text-[10px] text-[#767676]">
              Free · Unsubscribe anytime · No spam
            </p>
          </form>
        </div>
      </div>
    </section>
  );
}
