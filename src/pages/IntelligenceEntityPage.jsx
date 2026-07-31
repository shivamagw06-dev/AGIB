import { Link, useParams } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { ArrowLeft, ExternalLink } from 'lucide-react';
import { useIntelligenceEntity } from '@/hooks/useIntelligencePlatform';
import { entityPublicPath } from '@/lib/intelligencePlatformApi';
import '@/components/private-equity/editorial/peEditorial.css';

function Timeline({ events }) {
  if (!events?.length) {
    return <p className="text-sm text-[var(--pe-muted)]">No timeline events yet.</p>;
  }
  return (
    <ol className="space-y-0 border-l-2 border-[var(--pe-border)] ml-3">
      {events.map((event) => (
        <li key={event.id} className="relative pl-6 pb-6 last:pb-0">
          <span className="absolute -left-[5px] top-1.5 w-2 h-2 rounded-full bg-[var(--pe-accent)]" />
          <time className="text-[10px] uppercase tracking-wider text-[var(--pe-muted)]">
            {new Date(event.occurred_at).getFullYear()}
          </time>
          <p className="font-medium mt-1">{event.title}</p>
          {event.description && (
            <p className="text-sm text-[var(--pe-muted)] mt-1 leading-relaxed">{event.description}</p>
          )}
        </li>
      ))}
    </ol>
  );
}

function Relationships({ relationships }) {
  if (!relationships?.length) {
    return <p className="text-sm text-[var(--pe-muted)]">No relationships mapped yet.</p>;
  }
  const grouped = {};
  relationships.forEach((rel) => {
    const key = rel.relation_type.replace(/_/g, ' ');
    if (!grouped[key]) grouped[key] = [];
    if (rel.other_entity) grouped[key].push(rel);
  });
  return (
    <div className="space-y-4">
      {Object.entries(grouped).map(([type, rows]) => (
        <div key={type}>
          <p className="text-[10px] font-bold uppercase tracking-wider text-[var(--pe-muted)] mb-2">{type}</p>
          <ul className="space-y-2">
            {rows.slice(0, 8).map((rel) => (
              <li key={rel.id}>
                <Link
                  to={entityPublicPath(rel.other_entity)}
                  className="text-sm text-[var(--pe-accent)] no-underline hover:underline"
                >
                  {rel.other_entity.name}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}

export default function IntelligenceEntityPage() {
  const { slug } = useParams();
  const { data, loading, error } = useIntelligenceEntity(slug);
  const entity = data?.entity;

  if (loading) {
    return (
      <div className="pe-editorial pe-loading py-24 text-center text-[var(--pe-muted)]">
        Loading entity intelligence…
      </div>
    );
  }

  if (error || !entity) {
    return (
      <div className="pe-editorial pe-editorial-inner py-16">
        <Link to="/private-markets" className="inline-flex items-center gap-2 text-sm text-[var(--pe-accent)] no-underline mb-6">
          <ArrowLeft size={16} /> Private Markets Intelligence
        </Link>
        <p>Entity not found.</p>
      </div>
    );
  }

  const meta = entity.metadata || {};
  const typeLabel = entity.entity_type.replace(/_/g, ' ');

  return (
    <div className="pe-editorial">
      <Helmet>
        <title>{entity.name} | Private Markets Intelligence | AGI</title>
      </Helmet>
      <div className="pe-editorial-inner py-10">
        <Link to="/private-markets" className="inline-flex items-center gap-2 text-sm text-[var(--pe-muted)] no-underline mb-8 hover:text-[var(--pe-accent)]">
          <ArrowLeft size={16} /> Private Markets Intelligence
        </Link>

        <section className="pe-card p-6 md:p-10 mb-8">
          <p className="pe-tag capitalize">{typeLabel}</p>
          <h1 className="font-serif text-3xl md:text-4xl font-semibold mt-2">{entity.name}</h1>
          {entity.description && (
            <p className="text-[var(--pe-muted)] text-lg mt-4 max-w-3xl leading-relaxed">{entity.description}</p>
          )}
          {entity.tags?.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-5">
              {entity.tags.slice(0, 8).map((tag) => (
                <span key={tag} className="pe-tag border border-[var(--pe-border)] px-2 py-1">{tag}</span>
              ))}
            </div>
          )}
          {meta.website && (
            <a
              href={meta.website.startsWith('http') ? meta.website : `https://${meta.website}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-sm text-[var(--pe-accent)] mt-5 no-underline hover:underline"
            >
              Website <ExternalLink size={14} />
            </a>
          )}
        </section>

        {entity.ai_summary && (
          <section className="pe-card p-6 md:p-8 mb-8 border-l-4 border-l-[var(--pe-accent)]">
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[var(--pe-accent)] mb-3">
              AI Intelligence Summary
            </p>
            <p className="text-base leading-relaxed text-[var(--pe-text)]">{entity.ai_summary}</p>
            {entity.ai_summary_updated_at && (
              <p className="text-xs text-[var(--pe-muted)] mt-4">
                Updated {new Date(entity.ai_summary_updated_at).toLocaleDateString()}
              </p>
            )}
          </section>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <section className="pe-card p-6">
            <h2 className="font-serif text-xl font-semibold mb-5">Timeline</h2>
            <Timeline events={data.timeline} />
          </section>
          <section className="pe-card p-6">
            <h2 className="font-serif text-xl font-semibold mb-5">Relationships</h2>
            <Relationships relationships={data.relationships} />
          </section>
        </div>
      </div>
    </div>
  );
}
