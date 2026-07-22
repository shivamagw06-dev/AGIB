import { useState } from 'react';
import { Mail, Send } from 'lucide-react';
import PageShell from '@/components/Layout/PageShell';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/lib/supabaseClient';

const CONTACT_EMAIL = 'shivam@agarwalglobalinvestments.com';

export default function Contact() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    message: '',
  });
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.name.trim() || !formData.subject.trim() || !formData.message.trim()) {
      toast({
        title: 'Missing fields',
        description: 'Please fill out name, subject and message.',
        duration: 3000,
      });
      return;
    }

    try {
      setLoading(true);

      const { error } = await supabase.from('contact_messages').insert([
        {
          name: formData.name.trim(),
          email: formData.email?.trim() || null,
          subject: formData.subject.trim(),
          message: formData.message.trim(),
        },
      ]);

      if (error) throw error;

      toast({
        title: 'Message sent',
        description: 'Thank you — we will respond as soon as possible.',
        duration: 4000,
      });

      setFormData({ name: '', email: '', subject: '', message: '' });
    } catch (err) {
      console.error('Submission failed:', err);
      toast({
        title: 'Submission failed',
        description: 'Unable to send your message. Please email us directly.',
        variant: 'destructive',
        duration: 4000,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) =>
    setFormData((s) => ({ ...s, [e.target.name]: e.target.value }));

  return (
    <PageShell
      eyebrow="Contact"
      title="Get in Touch"
      description="Media inquiries, research partnerships, institutional subscriptions, and general feedback."
      metaTitle="Contact | Agarwal Global Investments"
    >
      <div className="grid lg:grid-cols-5 gap-10">
        <div className="lg:col-span-2 space-y-6">
          <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
            <div className="flex items-start gap-4">
              <div className="rounded-lg bg-blue-600/20 p-3 text-blue-400">
                <Mail size={22} />
              </div>
              <div>
                <h2 className="font-semibold text-white">Email</h2>
                <a
                  href={`mailto:${CONTACT_EMAIL}`}
                  className="text-blue-400 hover:underline text-sm mt-1 block"
                >
                  {CONTACT_EMAIL}
                </a>
                <p className="text-slate-500 text-xs mt-2">We typically respond within 1–2 business days.</p>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/5 p-6 text-sm text-slate-400 leading-relaxed">
            <p className="font-medium text-white mb-2">What to reach out about</p>
            <ul className="space-y-2">
              <li>· Institutional research subscriptions</li>
              <li>· Media &amp; press inquiries</li>
              <li>· Speaking &amp; webinar partnerships</li>
              <li>· Platform feedback</li>
            </ul>
          </div>
        </div>

        <form
          onSubmit={handleSubmit}
          className="lg:col-span-3 rounded-2xl border border-white/10 bg-white/5 p-6 lg:p-8 space-y-5"
        >
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-slate-300 mb-2">
              Full name
            </label>
            <Input
              id="name"
              name="name"
              required
              value={formData.name}
              onChange={handleChange}
              placeholder="Your name"
              className="bg-slate-900/50 border-white/15 text-white placeholder:text-slate-500"
            />
          </div>

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-slate-300 mb-2">
              Email <span className="text-slate-500">(optional)</span>
            </label>
            <Input
              id="email"
              name="email"
              type="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="you@company.com"
              className="bg-slate-900/50 border-white/15 text-white placeholder:text-slate-500"
            />
          </div>

          <div>
            <label htmlFor="subject" className="block text-sm font-medium text-slate-300 mb-2">
              Subject
            </label>
            <Input
              id="subject"
              name="subject"
              required
              value={formData.subject}
              onChange={handleChange}
              placeholder="How can we help?"
              className="bg-slate-900/50 border-white/15 text-white placeholder:text-slate-500"
            />
          </div>

          <div>
            <label htmlFor="message" className="block text-sm font-medium text-slate-300 mb-2">
              Message
            </label>
            <Textarea
              id="message"
              name="message"
              required
              rows={6}
              value={formData.message}
              onChange={handleChange}
              placeholder="Tell us about your inquiry…"
              className="bg-slate-900/50 border-white/15 text-white placeholder:text-slate-500"
            />
          </div>

          <Button
            type="submit"
            className="w-full bg-blue-600 hover:bg-blue-700"
            size="lg"
            disabled={loading}
          >
            {loading ? 'Sending…' : 'Send message'}
            {!loading && <Send className="ml-2 h-4 w-4" />}
          </Button>
        </form>
      </div>
    </PageShell>
  );
}
