import { Link } from 'react-router-dom';
import { Mail, Linkedin } from 'lucide-react';

const CONTACT_EMAIL = 'shivam@agarwalglobalinvestments.com';

const researchLinks = [
  { label: 'Research Library', to: '/sections/live-articles' },
  { label: 'Research Notes', to: '/sections/research-notes' },
  { label: 'Deal Tracker', to: '/sections/deal-tracker' },
  { label: 'Markets', to: '/markets' },
  { label: 'Opinions', to: '/sections/opinions-editorials' },
];

const companyLinks = [
  { label: 'About', to: '/about' },
  { label: 'Contact', to: '/contact' },
  { label: 'Events', to: '/events' },
];

const legalLinks = [
  { label: 'Privacy Policy', to: '/privacy' },
  { label: 'Terms of Service', to: '/terms' },
  { label: 'Disclaimer', to: '/disclaimer' },
];

export default function Footer() {
  return (
    <footer className="bg-slate-950 border-t border-white/10 text-slate-400">
      <div className="max-w-7xl mx-auto px-6 py-14">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-10 mb-12">
          <div className="lg:col-span-1">
            <Link to="/" className="text-xl font-bold text-white hover:text-blue-300 transition-colors">
              Agarwal Global Investments
            </Link>
            <p className="mt-4 text-sm leading-relaxed max-w-xs">
              Independent research on finance, economics, private markets, and global business.
            </p>
            <div className="flex gap-3 mt-5">
              <a
                href={`mailto:${CONTACT_EMAIL}`}
                className="rounded-lg border border-white/10 p-2.5 text-slate-400 hover:text-white hover:border-white/25 transition-colors"
                aria-label="Email"
              >
                <Mail size={18} />
              </a>
              <a
                href="https://www.linkedin.com"
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-lg border border-white/10 p-2.5 text-slate-400 hover:text-white hover:border-white/25 transition-colors"
                aria-label="LinkedIn"
              >
                <Linkedin size={18} />
              </a>
            </div>
          </div>

          <div>
            <h4 className="text-white font-semibold text-sm mb-4">Research</h4>
            <ul className="space-y-2.5 text-sm">
              {researchLinks.map((link) => (
                <li key={link.to}>
                  <Link to={link.to} className="hover:text-white transition-colors">
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="text-white font-semibold text-sm mb-4">Company</h4>
            <ul className="space-y-2.5 text-sm">
              {companyLinks.map((link) => (
                <li key={link.to}>
                  <Link to={link.to} className="hover:text-white transition-colors">
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="text-white font-semibold text-sm mb-4">Legal</h4>
            <ul className="space-y-2.5 text-sm">
              {legalLinks.map((link) => (
                <li key={link.to}>
                  <Link to={link.to} className="hover:text-white transition-colors">
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="border-t border-white/10 pt-8 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 text-xs">
          <p>© {new Date().getFullYear()} Agarwal Global Investments. All rights reserved.</p>
          <p className="text-slate-500 max-w-lg leading-relaxed">
            Content is for informational purposes only and does not constitute investment advice.{' '}
            <Link to="/disclaimer" className="text-blue-400 hover:underline">
              Read full disclaimer
            </Link>
            .
          </p>
        </div>
      </div>
    </footer>
  );
}
