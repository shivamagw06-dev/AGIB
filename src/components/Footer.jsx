import { Link } from 'react-router-dom';
import Logo from '@/components/Layout/Logo';

const footerLinks = [
  { label: 'About', to: '/about' },
  { label: 'Contact', to: '/contact' },
  { label: 'Privacy Policy', to: '/privacy' },
  { label: 'Terms of Service', to: '/terms' },
  { label: 'Disclaimer', to: '/disclaimer' },
  { label: 'SEBI Disclosure', to: '/sebi-disclosure' },
];

export default function Footer() {
  return (
    <footer className="bg-[#f7f7f7] border-t border-[#dddddd]">
      <div className="max-w-[1600px] mx-auto px-4 sm:px-6 py-10">
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-8">
          <div>
            <Logo compact className="mb-3" />
            <p className="text-xs text-[#767676] max-w-sm leading-relaxed mt-2">
              Independent equity research for Indian investors. For informational purposes only — not investment advice.
            </p>
          </div>

          <nav className="flex flex-wrap gap-x-5 gap-y-2 text-xs">
            {footerLinks.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                className="text-[#555555] hover:text-[#ff6600] transition-colors"
              >
                {link.label}
              </Link>
            ))}
          </nav>
        </div>

        <p className="mt-8 pt-5 border-t border-[#dddddd] text-[11px] text-[#767676]">
          © {new Date().getFullYear()} Agarwal Global Investments. All rights reserved.
        </p>
      </div>
    </footer>
  );
}
