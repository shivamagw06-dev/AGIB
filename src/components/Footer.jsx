import { Link } from 'react-router-dom';
import Logo from '@/components/Layout/Logo';

const COLUMNS = [
  {
    title: 'Research',
    links: [
      { label: 'Research', to: '/sections/research-notes' },
      { label: 'Markets', to: '/markets' },
      { label: 'Company Intelligence', to: '/company-updates' },
      { label: 'Morning Office', to: '/#morning-office' },
      { label: 'Ask AGIB', to: '/ask' },
    ],
  },
  {
    title: 'Platform',
    links: [
      { label: 'Macro', to: '/macro-intelligence' },
      { label: 'IPO', to: '/ipo-intelligence' },
      { label: 'Global', to: '/global' },
      { label: 'API', to: '/contact' },
      { label: 'Documentation', to: '/contact' },
    ],
  },
  {
    title: 'Legal',
    links: [
      { label: 'About', to: '/about' },
      { label: 'Privacy', to: '/privacy' },
      { label: 'Terms', to: '/terms' },
      { label: 'Disclaimer', to: '/disclaimer' },
      { label: 'SEBI Disclosure', to: '/sebi-disclosure' },
    ],
  },
];

export default function Footer() {
  return (
    <footer className="bg-[#0b1f33] text-white">
      <div className="max-w-[1800px] mx-auto px-4 sm:px-6 py-12">
        <div className="grid grid-cols-1 gap-10 md:grid-cols-[1.2fr_repeat(3,1fr)]">
          <div>
            <Logo compact className="mb-3 brightness-0 invert" />
            <p className="mt-3 max-w-sm text-xs leading-relaxed text-white/65">
              AGIB institutional investment intelligence for professional investors. Informational research only — not investment advice.
            </p>
            <a
              href="https://www.linkedin.com"
              target="_blank"
              rel="noreferrer"
              className="mt-4 inline-block text-xs font-bold text-[#ffb366] hover:text-white"
            >
              LinkedIn →
            </a>
          </div>

          {COLUMNS.map((col) => (
            <nav key={col.title} aria-label={col.title}>
              <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-white/45">{col.title}</p>
              <ul className="mt-3 space-y-2">
                {col.links.map((link) => (
                  <li key={link.label}>
                    <Link to={link.to} className="text-sm text-white/80 hover:text-[#ffb366]">
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>
          ))}
        </div>

        <p className="mt-10 border-t border-white/10 pt-5 text-[11px] text-white/45">
          © {new Date().getFullYear()} Agarwal Global Investments. All rights reserved.
        </p>
      </div>
    </footer>
  );
}
