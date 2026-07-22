import { Helmet } from 'react-helmet-async';
import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

export default function PageShell({
  title,
  description,
  metaTitle,
  eyebrow,
  backTo = '/',
  backLabel = 'Back to Home',
  children,
  className = '',
}) {
  return (
    <div className={`bg-slate-950 min-h-screen ${className}`}>
      <Helmet>
        <title>{metaTitle || `${title} | Agarwal Global Investments`}</title>
        {description && <meta name="description" content={description} />}
      </Helmet>

      <div className="border-b border-white/10 bg-slate-950">
        <div className="max-w-4xl mx-auto px-6 py-14 lg:py-16">
          <Link
            to={backTo}
            className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white mb-8 transition-colors"
          >
            <ArrowLeft size={16} />
            {backLabel}
          </Link>
          {eyebrow && (
            <span className="text-blue-400 text-sm font-semibold uppercase tracking-widest">
              {eyebrow}
            </span>
          )}
          <h1 className="mt-3 text-3xl md:text-4xl lg:text-5xl font-bold text-white tracking-tight">
            {title}
          </h1>
          {description && (
            <p className="mt-4 text-lg text-slate-400 max-w-3xl leading-relaxed">{description}</p>
          )}
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-6 py-12 lg:py-16">{children}</div>
    </div>
  );
}

export function LegalSection({ title, children }) {
  return (
    <section className="mb-10">
      <h2 className="text-xl font-semibold text-white mb-3">{title}</h2>
      <div className="text-slate-300 leading-relaxed space-y-3 text-[15px]">{children}</div>
    </section>
  );
}
