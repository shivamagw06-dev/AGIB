import { Link } from 'react-router-dom';

const footerLinks = [
  { label: 'About', to: '/about' },
  { label: 'Disclaimer', to: '/disclaimer' },
  { label: 'SEBI Disclosure', to: '/sebi-disclosure' },
  { label: 'Privacy Policy', to: '/privacy' },
  { label: 'Contact', to: '/contact' },
];

export default function Footer() {
  return (
    <footer className="bg-white border-t border-slate-200">
      <div className="max-w-6xl mx-auto px-6 py-10">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div>
            <Link to="/" className="text-base font-semibold text-slate-900 hover:text-blue-800 transition-colors">
              Agarwal Global Investments
            </Link>
            <p className="mt-2 text-sm text-slate-500 max-w-md leading-relaxed">
              Independent market research for Indian investors. For informational purposes only — not investment advice.
            </p>
          </div>

          <nav className="flex flex-wrap gap-x-6 gap-y-2 text-sm">
            {footerLinks.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                className="text-slate-600 hover:text-slate-900 transition-colors"
              >
                {link.label}
              </Link>
            ))}
          </nav>
        </div>

        <p className="mt-8 pt-6 border-t border-slate-100 text-xs text-slate-400">
          © {new Date().getFullYear()} Agarwal Global Investments. All rights reserved.
        </p>
      </div>
    </footer>
  );
}
