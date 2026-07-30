import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  RefreshCw,
  Upload,
  Search,
  Download,
  Play,
  Eye,
  X,
  AlertTriangle,
  ArrowLeft,
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { isAdmin } from '@/lib/adminAuth';
import Forbidden403 from '@/components/admin/Forbidden403';
import {
  getKocDesk,
  getKocCompany,
  uploadKocKnowledge,
  runKocAction,
  getKocAudit,
} from '@/lib/intelligenceApi';
import './knowledgeOps.css';

const DOC_TYPES = [
  { value: 'annual_report', label: 'Annual Report' },
  { value: 'quarterly_results', label: 'Quarterly Results' },
  { value: 'investor_presentation', label: 'Investor Presentation' },
  { value: 'transcript', label: 'Transcript' },
  { value: 'shareholding', label: 'Shareholding' },
  { value: 'corporate_action', label: 'Corporate Action' },
  { value: 'management_guidance', label: 'Management Guidance' },
  { value: 'segment_data', label: 'Segment Data' },
  { value: 'credit_rating', label: 'Credit Rating' },
  { value: 'investor_day', label: 'Investor Day' },
  { value: 'other', label: 'Other' },
];

const CLASS_LABELS = {
  annual_reports: 'Annual Reports',
  quarterly_results: 'Quarterly Results',
  financial_statements: 'Financial Statements',
  earnings_presentations: 'Investor Presentations',
  earnings_call_transcripts: 'Transcripts',
  shareholding: 'Shareholding',
  corporate_actions: 'Corporate Actions',
  management_guidance: 'Guidance',
  segment_kpis: 'Segment Data',
  company_memory: 'Company Memory',
  knowledge_graph: 'Knowledge Graph',
};

function fmt(v) {
  if (v == null || v === '') return '—';
  if (typeof v === 'number') return Number.isInteger(v) ? String(v) : v.toFixed(1);
  return String(v);
}

function PriorityBadge({ priority }) {
  const p = String(priority || 'Medium').toLowerCase();
  return <span className={`koc-badge ${p}`}>{priority || 'Medium'}</span>;
}

function StatusDot({ ok, warn }) {
  const cls = ok ? 'ok' : warn ? 'warn' : 'bad';
  return <span className={`koc-dot ${cls}`} />;
}

function Kpi({ label, value, onClick }) {
  return (
    <div className="koc-kpi">
      <button type="button" onClick={onClick}>
        <div className="label">{label}</div>
        <div className="value">{fmt(value)}</div>
      </button>
    </div>
  );
}

function UploadModal({ open, ticker, documentType, company, actor, onClose, onDone }) {
  const [dtype, setDtype] = useState(documentType || 'investor_presentation');
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  useEffect(() => {
    if (open) {
      setDtype(documentType || 'investor_presentation');
      setFile(null);
      setError('');
      setResult(null);
    }
  }, [open, documentType]);

  if (!open) return null;

  const submit = async () => {
    if (!file || !ticker) {
      setError('Choose a company and a file.');
      return;
    }
    setBusy(true);
    setError('');
    try {
      const buf = await file.arrayBuffer();
      const bytes = new Uint8Array(buf);
      let binary = '';
      bytes.forEach((b) => {
        binary += String.fromCharCode(b);
      });
      const content_base64 = btoa(binary);
      const res = await uploadKocKnowledge({
        ticker,
        document_type: dtype,
        filename: file.name,
        content_base64,
        mime_type: file.type || undefined,
        actor: actor || 'admin',
      });
      setResult(res);
      onDone?.(res);
    } catch (err) {
      setError(err?.message || 'Upload failed');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="koc-modal-backdrop" role="dialog" aria-modal="true">
      <div className="koc-modal">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="koc-kicker">Manual Knowledge Upload</p>
            <h2 className="mt-1 text-lg font-semibold">
              {company || ticker} · Upload Knowledge
            </h2>
            <p className="mt-1 text-xs text-[var(--koc-muted)]">
              Store → checksum → parse → evidence → memory → readiness. Append-only; never overwrites.
            </p>
          </div>
          <button type="button" className="koc-btn" onClick={onClose} aria-label="Close">
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="mt-4 space-y-3">
          <label className="block text-xs font-semibold uppercase tracking-wide text-[var(--koc-caption)]">
            Document type
            <select
              className="koc-select mt-1 w-full"
              value={dtype}
              onChange={(e) => setDtype(e.target.value)}
            >
              {DOC_TYPES.map((d) => (
                <option key={d.value} value={d.value}>
                  {d.label}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-xs font-semibold uppercase tracking-wide text-[var(--koc-caption)]">
            File (PDF / PPT / DOCX / XLSX / ZIP)
            <input
              type="file"
              className="mt-1 block w-full text-sm"
              accept=".pdf,.ppt,.pptx,.doc,.docx,.xls,.xlsx,.zip"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
            />
          </label>
          {error ? (
            <p className="flex items-center gap-2 text-sm text-[var(--koc-red)]">
              <AlertTriangle className="h-4 w-4" /> {error}
            </p>
          ) : null}
          {result?.ok ? (
            <div className="border border-[var(--koc-line)] bg-[var(--koc-green-bg)] p-3 text-xs">
              Uploaded · hash {(result.upload?.sha256 || '').slice(0, 16)}… · evidence{' '}
              {(result.upload?.evidence_ids || []).join(', ') || '—'}
            </div>
          ) : null}
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" className="koc-btn" onClick={onClose}>
              Cancel
            </button>
            <button type="button" className="koc-btn primary" disabled={busy} onClick={submit}>
              <Upload className="h-3.5 w-3.5" />
              {busy ? 'Processing…' : 'Upload & process'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function KnowledgeOperations() {
  const { user } = useAuth();
  const [desk, setDesk] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [actionBusy, setActionBusy] = useState('');
  const [audit, setAudit] = useState(null);
  const [uploadState, setUploadState] = useState({
    open: false,
    ticker: '',
    company: '',
    documentType: 'investor_presentation',
  });

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [d, a] = await Promise.all([
        getKocDesk({ scope: 'TOP20' }),
        getKocAudit({ limit: 20 }).catch(() => null),
      ]);
      setDesk(d);
      setAudit(a);
    } catch (err) {
      setError(err?.message || 'Failed to load Knowledge Operations');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isAdmin(user)) load();
  }, [user, load]);

  const openCompany = async (ticker) => {
    setSelected(ticker);
    try {
      const d = await getKocCompany(ticker);
      setDetail(d);
    } catch (err) {
      setDetail({ error: err?.message });
    }
  };

  const openUpload = (row, missingClass) => {
    const map = {
      annual_reports: 'annual_report',
      quarterly_results: 'quarterly_results',
      financial_statements: 'quarterly_results',
      earnings_presentations: 'investor_presentation',
      earnings_call_transcripts: 'transcript',
      shareholding: 'shareholding',
      corporate_actions: 'corporate_action',
      management_guidance: 'management_guidance',
      segment_kpis: 'segment_data',
    };
    setUploadState({
      open: true,
      ticker: row.ticker || row,
      company: row.company || row.ticker || row,
      documentType: map[missingClass] || 'other',
    });
  };

  const runAction = async (action, ticker) => {
    setActionBusy(action);
    try {
      await runKocAction({ action, ticker, actor: user?.email || 'admin' });
      await load();
      if (ticker) await openCompany(ticker);
    } catch (err) {
      setError(err?.message || 'Action failed');
    } finally {
      setActionBusy('');
    }
  };

  const kpis = desk?.kpis || {};
  const inbox = desk?.missing_inbox || {};
  const table = desk?.coverage_table || [];
  const timeline = desk?.ingestion_timeline || [];
  const summary = desk?.daily_summary || {};
  const queue = desk?.knowledge_queue || {};
  const collectors = desk?.collector_health || [];
  const heatmap = desk?.coverage_heatmap || {};
  const versions = desk?.knowledge_versions || [];

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return table;
    return table.filter(
      (r) =>
        String(r.ticker || '')
          .toLowerCase()
          .includes(q) ||
        String(r.company || '')
          .toLowerCase()
          .includes(q) ||
        (r.missing_items || []).join(' ').toLowerCase().includes(q)
    );
  }, [table, query]);

  const exportCsv = () => {
    const header = [
      'ticker',
      'company',
      'coverage_pct',
      'knowledge_confidence',
      'research_readiness',
      'claim_safe',
      'coverage_state',
      'missing',
    ];
    const lines = [header.join(',')];
    filtered.forEach((r) => {
      lines.push(
        [
          r.ticker,
          JSON.stringify(r.company || ''),
          r.coverage_pct,
          r.knowledge_confidence,
          r.research_readiness,
          r.claim_safe,
          JSON.stringify(r.coverage_state || ''),
          JSON.stringify((r.missing_items || []).join('; ')),
        ].join(',')
      );
    });
    const blob = new Blob([lines.join('\n')], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'knowledge-operations-coverage.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!isAdmin(user)) {
    return <Forbidden403 resource="Knowledge Operations" />;
  }

  return (
    <div className="koc-root">
      <div className="koc-shell space-y-6">
        <header className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="koc-kicker">Admin only · Institutional Knowledge OS</p>
            <h1 className="koc-title mt-2">Knowledge Operations</h1>
            <p className="mt-2 max-w-2xl text-sm text-[var(--koc-muted)]">
              Monitor, validate and improve institutional knowledge across the entire AGI universe.
            </p>
            <p className="mt-2 text-[11px] text-[var(--koc-caption)]">
              Generated {desk?.generated_at || '—'} · {desk?.version || 'koc-01'} · Evidence immutable
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link to="/" className="koc-btn">
              <ArrowLeft className="h-3.5 w-3.5" /> Home
            </Link>
            <button type="button" className="koc-btn" onClick={exportCsv}>
              <Download className="h-3.5 w-3.5" /> Export
            </button>
            <button type="button" className="koc-btn primary" onClick={load} disabled={loading}>
              <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </header>

        {error ? (
          <div className="koc-panel flex items-start gap-2 border-[var(--koc-red)] bg-[var(--koc-red-bg)] p-3 text-sm text-[var(--koc-red)]">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        ) : null}

        {/* KPIs */}
        <section className="grid gap-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-7">
          <Kpi label="Companies Covered" value={kpis.companies_covered} />
          <Kpi label="ICC Complete" value={kpis.institutional_coverage_complete} />
          <Kpi label="Research Ready" value={kpis.research_ready} />
          <Kpi label="Knowledge Ready" value={kpis.knowledge_ready} />
          <Kpi label="Knowledge Confidence" value={kpis.knowledge_confidence} />
          <Kpi label="Evidence Objects" value={kpis.evidence_objects} />
          <Kpi label="Docs Collected Today" value={kpis.documents_collected_today} />
          <Kpi label="Docs Processed Today" value={kpis.documents_processed_today} />
          <Kpi label="Claims Created Today" value={kpis.claims_created_today} />
          <Kpi label="Research Invalidated" value={kpis.research_invalidated_today} />
          <Kpi
            label="Collector Success %"
            value={kpis.collector_success_pct != null ? `${kpis.collector_success_pct}` : null}
          />
          <Kpi label="Collector Health" value={kpis.collector_health} />
          <Kpi
            label="Scheduler"
            value={
              kpis.scheduler_status === true
                ? 'Enabled'
                : kpis.scheduler_status === false
                  ? 'Off'
                  : kpis.scheduler_status
            }
          />
          <Kpi label="Knowledge Latency" value={kpis.knowledge_latency} />
        </section>

        {/* Missing Knowledge Inbox — primary workflow */}
        <section className="koc-panel p-4">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <p className="koc-kicker">Missing Knowledge Inbox</p>
              <h2 className="mt-1 text-lg font-semibold">
                {inbox.title || "Today's Highest-Impact Missing Knowledge"}
              </h2>
              <p className="mt-1 text-xs text-[var(--koc-muted)]">
                {inbox.workflow || 'Clear the inbox — do not search for gaps.'} · {fmt(inbox.count)}{' '}
                items · Critical {fmt(inbox.by_priority?.Critical)} · High{' '}
                {fmt(inbox.by_priority?.High)}
              </p>
            </div>
          </div>
          <div className="mt-4 overflow-x-auto">
            <table className="koc-table">
              <thead>
                <tr>
                  <th>Company</th>
                  <th>Missing</th>
                  <th>Priority</th>
                  <th>Coverage</th>
                  <th>Upload</th>
                </tr>
              </thead>
              <tbody>
                {(inbox.items || []).slice(0, 25).map((item) => (
                  <tr key={`${item.ticker}-${item.missing_class}`}>
                    <td>
                      <button
                        type="button"
                        className="font-semibold hover:underline"
                        onClick={() => openCompany(item.ticker)}
                      >
                        {item.company || item.ticker}
                      </button>
                      <div className="koc-mono text-[11px] text-[var(--koc-caption)]">
                        {item.ticker}
                      </div>
                    </td>
                    <td>{item.missing}</td>
                    <td>
                      <PriorityBadge priority={item.priority} />
                    </td>
                    <td className="koc-mono">{fmt(item.coverage_pct)}%</td>
                    <td>
                      {item.uploadable ? (
                        <button
                          type="button"
                          className="koc-btn"
                          onClick={() => openUpload(item, item.missing_class)}
                          title="Upload Knowledge"
                        >
                          <Upload className="h-3.5 w-3.5" /> Upload
                        </button>
                      ) : (
                        <button
                          type="button"
                          className="koc-btn"
                          disabled={!!actionBusy}
                          onClick={() => runAction('run_auto_repair', item.ticker)}
                        >
                          Repair
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
                {!inbox.items?.length && !loading ? (
                  <tr>
                    <td colSpan={5} className="text-[var(--koc-muted)]">
                      No missing knowledge in scope — inbox clear.
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </section>

        {/* Section 1 — Ingestion timeline */}
        <section className="koc-panel p-4">
          <p className="koc-kicker">Section 1</p>
          <h2 className="mt-1 text-lg font-semibold">Today&apos;s Knowledge Ingestion</h2>
          <div className="mt-3">
            {timeline.length ? (
              timeline.slice(0, 12).map((ev, idx) => (
                <div className="koc-timeline-item" key={`${ev.timestamp}-${idx}`}>
                  <div className="koc-mono text-sm font-medium">{ev.time || '—'}</div>
                  <div>
                    <div className="flex flex-wrap items-center gap-2 text-sm">
                      <span className="font-semibold">{ev.ticker || '—'}</span>
                      <span className="text-[var(--koc-muted)]">{ev.document_type}</span>
                      <span className="koc-pill">
                        <StatusDot ok={ev.status === 'Collected'} />
                        {ev.status || '—'}
                      </span>
                    </div>
                    <div className="mt-1 grid gap-1 text-xs text-[var(--koc-muted)] sm:grid-cols-2 lg:grid-cols-4">
                      <span>Source · {ev.source || '—'}</span>
                      <span>Evidence · {fmt(ev.evidence_objects)}</span>
                      <span>Claims · {fmt(ev.claims_extracted)}</span>
                      <span>
                        Knowledge updated · {ev.knowledge_updated ? 'Yes' : 'No'} · Research
                        invalidated · {ev.research_invalidated ? 'Yes' : 'No'}
                      </span>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm text-[var(--koc-muted)]">
                No ingestion events yet. Run CGL or upload knowledge to populate the timeline.
              </p>
            )}
          </div>
        </section>

        {/* Section 2 — Daily summary */}
        <section className="koc-panel p-4">
          <p className="koc-kicker">Section 2</p>
          <h2 className="mt-1 text-lg font-semibold">Daily Knowledge Summary</h2>
          <div className="mt-3 grid gap-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6">
            {[
              ['Companies Updated', summary.companies_updated],
              ['Documents Downloaded', summary.documents_downloaded],
              ['Evidence Objects Added', summary.evidence_objects_added],
              ['Financial Statements Parsed', summary.financial_statements_parsed],
              ['Annual Reports', summary.annual_reports],
              ['Quarterly Results', summary.quarterly_results],
              ['Investor Presentations', summary.investor_presentations],
              ['Transcripts', summary.transcripts],
              ['Shareholding Files', summary.shareholding_files],
              ['Corporate Actions', summary.corporate_actions],
              ['Management Guidance', summary.management_guidance],
              ['Segment KPIs', summary.segment_kpis],
              ['KG Updates', summary.knowledge_graph_updates],
              ['Memory Refreshes', summary.company_memory_refreshes],
              ['Research Pack Refreshes', summary.research_pack_refreshes],
              ['Knowledge Version', summary.knowledge_version_created],
            ].map(([label, value]) => (
              <Kpi key={label} label={label} value={value} />
            ))}
          </div>
        </section>

        {/* Section 3 — Coverage table */}
        <section className="koc-panel p-4">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <p className="koc-kicker">Section 3</p>
              <h2 className="mt-1 text-lg font-semibold">Institutional Coverage Table</h2>
            </div>
            <div className="relative">
              <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[var(--koc-caption)]" />
              <input
                className="koc-input w-64 pl-8"
                placeholder="Search ticker / company / missing"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </div>
          </div>
          <div className="mt-4 overflow-x-auto">
            <table className="koc-table">
              <thead>
                <tr>
                  <th>Ticker</th>
                  <th>Company</th>
                  <th>Coverage %</th>
                  <th>Confidence</th>
                  <th>Readiness</th>
                  <th>Claim Safe</th>
                  <th>State</th>
                  <th>Evidence</th>
                  <th>Missing</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((r) => (
                  <tr key={r.ticker}>
                    <td className="koc-mono font-semibold">{r.ticker}</td>
                    <td>{r.company}</td>
                    <td className="koc-mono">{fmt(r.coverage_pct)}%</td>
                    <td className="koc-mono">{fmt(r.knowledge_confidence)}</td>
                    <td className="koc-mono">{fmt(r.research_readiness)}</td>
                    <td>
                      <span className="koc-pill">
                        <StatusDot ok={!!r.claim_safe} />
                        {r.claim_safe ? 'Yes' : 'No'}
                      </span>
                    </td>
                    <td className="text-xs">{r.coverage_state || r.status || '—'}</td>
                    <td className="koc-mono">{fmt(r.evidence_count)}</td>
                    <td className="max-w-[220px] text-xs text-[var(--koc-muted)]">
                      {(r.missing_items || []).slice(0, 4).join(', ') || '—'}
                    </td>
                    <td>
                      <div className="flex flex-wrap gap-1">
                        <button type="button" className="koc-btn" onClick={() => openCompany(r.ticker)}>
                          <Eye className="h-3.5 w-3.5" /> View
                        </button>
                        <button
                          type="button"
                          className="koc-btn"
                          disabled={!!actionBusy}
                          onClick={() => runAction('run_icf_dispatch', r.ticker)}
                        >
                          Refresh
                        </button>
                        <button type="button" className="koc-btn" onClick={() => openUpload(r)}>
                          <Upload className="h-3.5 w-3.5" /> Upload
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Section 4 — Company detail */}
        {selected ? (
          <section className="koc-panel p-4" id="company-detail">
            <p className="koc-kicker">Section 4 · Company Detail</p>
            <h2 className="mt-1 text-lg font-semibold">{selected}</h2>
            {detail?.error ? (
              <p className="mt-2 text-sm text-[var(--koc-red)]">{detail.error}</p>
            ) : (
              <>
                <p className="mt-1 text-xs text-[var(--koc-muted)]">
                  Research ready · {detail?.pack_summary?.research_ready ? 'Yes' : 'No'} · Claim safe ·{' '}
                  {detail?.pack_summary?.claim_safe ? 'Yes' : 'No'} · Evidence ·{' '}
                  {fmt(detail?.pack_summary?.evidence_count)}
                </p>
                <div className="koc-progress-grid mt-4">
                  {Object.entries(detail?.progress || detail?.row?.progress || {}).map(
                    ([key, state]) => (
                      <div key={key} className={`koc-progress-item ${state}`}>
                        <div className="font-semibold">{CLASS_LABELS[key] || key}</div>
                        <div className="mt-1 capitalize text-[11px]">{state}</div>
                      </div>
                    )
                  )}
                </div>
              </>
            )}
          </section>
        ) : null}

        {/* Section 6 — Queue */}
        <section className="koc-panel p-4">
          <p className="koc-kicker">Section 6</p>
          <h2 className="mt-1 text-lg font-semibold">Knowledge Queue</h2>
          <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
            {(desk?.queue_stages || []).map((stage) => (
              <div key={stage} className="border border-[var(--koc-line)] p-3">
                <div className="text-[10px] font-bold uppercase tracking-wide text-[var(--koc-caption)]">
                  {stage}
                </div>
                <div className="koc-mono mt-1 text-xl">
                  {fmt((queue.stages || {})[stage] || 0)}
                </div>
              </div>
            ))}
          </div>
          {(queue.items || []).length ? (
            <div className="mt-3 overflow-x-auto">
              <table className="koc-table">
                <thead>
                  <tr>
                    <th>Ticker</th>
                    <th>Type</th>
                    <th>Stage</th>
                    <th>Status</th>
                    <th>Created</th>
                  </tr>
                </thead>
                <tbody>
                  {(queue.items || []).slice(0, 15).map((q) => (
                    <tr key={q.queue_id}>
                      <td className="koc-mono">{q.ticker}</td>
                      <td>{q.document_type}</td>
                      <td>{q.stage}</td>
                      <td>{q.status}</td>
                      <td className="koc-mono text-xs">{(q.created_at || '').slice(0, 19)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </section>

        {/* Section 7 — Collectors */}
        <section className="koc-panel p-4">
          <p className="koc-kicker">Section 7</p>
          <h2 className="mt-1 text-lg font-semibold">Collector Health</h2>
          <div className="mt-3 overflow-x-auto">
            <table className="koc-table">
              <thead>
                <tr>
                  <th>Collector</th>
                  <th>Health</th>
                  <th>Success Rate</th>
                  <th>Retry</th>
                </tr>
              </thead>
              <tbody>
                {collectors.map((c) => (
                  <tr key={c.collector}>
                    <td>{c.collector}</td>
                    <td>
                      <span className="koc-pill">
                        <StatusDot
                          ok={c.health === 'Healthy'}
                          warn={c.health === 'Degraded'}
                        />
                        {c.health}
                      </span>
                    </td>
                    <td className="koc-mono">{fmt(c.success_rate)}</td>
                    <td>
                      <button
                        type="button"
                        className="koc-btn"
                        disabled={!!actionBusy}
                        onClick={() => runAction('run_cgl')}
                      >
                        Retry
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Section 10 — Versions */}
        <section className="koc-panel p-4">
          <p className="koc-kicker">Section 10</p>
          <h2 className="mt-1 text-lg font-semibold">Knowledge Versions</h2>
          <div className="mt-3 overflow-x-auto">
            <table className="koc-table">
              <thead>
                <tr>
                  <th>Version</th>
                  <th>Companies Updated</th>
                  <th>Evidence Added</th>
                  <th>Research Invalidated</th>
                </tr>
              </thead>
              <tbody>
                {(versions.length ? versions : [{ knowledge_version: '—' }]).map((v, i) => (
                  <tr key={v.snapshot_id || v.knowledge_version || i}>
                    <td className="koc-mono">{v.knowledge_version || v.version || '—'}</td>
                    <td className="koc-mono">
                      {fmt(
                        Array.isArray(v.companies_updated)
                          ? v.companies_updated.length
                          : v.companies_updated
                      )}
                    </td>
                    <td className="koc-mono">{fmt(v.evidence_added)}</td>
                    <td className="koc-mono">
                      {fmt(
                        Array.isArray(v.research_invalidated)
                          ? v.research_invalidated.length
                          : v.research_invalidated
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Section 11 — Heatmap */}
        <section className="koc-panel p-4">
          <p className="koc-kicker">Section 11</p>
          <h2 className="mt-1 text-lg font-semibold">Coverage Heatmap</h2>
          <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
            {['TOP20', 'NIFTY50', 'NIFTY100', 'NIFTY500'].map((band) => {
              const cell = heatmap[band] || {};
              return (
                <div key={band} className="koc-heat-cell">
                  <div className="text-[10px] font-bold uppercase tracking-wide text-[var(--koc-caption)]">
                    {band}
                  </div>
                  {cell.coverage_pct != null ? (
                    <div className="mt-2 space-y-1 text-xs">
                      <div>
                        Coverage <span className="koc-mono">{fmt(cell.coverage_pct)}%</span>
                      </div>
                      <div>
                        Confidence{' '}
                        <span className="koc-mono">{fmt(cell.knowledge_confidence)}</span>
                      </div>
                      <div>
                        Research ready <span className="koc-mono">{fmt(cell.research_ready)}</span>
                      </div>
                      <div>
                        Claim safe <span className="koc-mono">{fmt(cell.claim_safe_pct)}%</span>
                      </div>
                      <div>
                        ICC <span className="koc-mono">{fmt(cell.icc_complete)}</span>
                      </div>
                    </div>
                  ) : (
                    <p className="mt-2 text-xs text-[var(--koc-muted)]">{cell.note || '—'}</p>
                  )}
                </div>
              );
            })}
          </div>
        </section>

        {/* Section 12 — Actions */}
        <section className="koc-panel p-4">
          <p className="koc-kicker">Section 12</p>
          <h2 className="mt-1 text-lg font-semibold">Actions</h2>
          <p className="mt-1 text-xs text-[var(--koc-muted)]">
            Every action is audit-logged. Evidence is never overwritten.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            {[
              ['run_full_coverage', 'Run Full Coverage'],
              ['run_cgl', 'Run CGL'],
              ['run_kil', 'Run KIL'],
              ['run_research_refresh', 'Research Refresh'],
              ['run_knowledge_validation', 'Knowledge Validation'],
              ['run_company_memory_refresh', 'Memory Refresh'],
              ['run_research_readiness', 'Research Readiness'],
              ['run_auto_repair', 'Auto Repair'],
              ['rebuild_knowledge_graph', 'Rebuild KG'],
            ].map(([action, label]) => (
              <button
                key={action}
                type="button"
                className="koc-btn"
                disabled={!!actionBusy}
                onClick={() =>
                  runAction(
                    action,
                    ['run_cgl', 'run_kil', 'run_full_coverage'].includes(action)
                      ? undefined
                      : selected || 'RELIANCE'
                  )
                }
              >
                <Play className="h-3.5 w-3.5" />
                {actionBusy === action ? 'Running…' : label}
              </button>
            ))}
          </div>
        </section>

        {/* Audit */}
        <section className="koc-panel p-4">
          <p className="koc-kicker">Security · Audit log</p>
          <h2 className="mt-1 text-lg font-semibold">Recent Operations</h2>
          <div className="mt-3 overflow-x-auto">
            <table className="koc-table">
              <thead>
                <tr>
                  <th>When</th>
                  <th>Actor</th>
                  <th>Action</th>
                  <th>Company</th>
                  <th>Hash</th>
                </tr>
              </thead>
              <tbody>
                {(audit?.entries || []).map((e) => (
                  <tr key={e.audit_id}>
                    <td className="koc-mono text-xs">{(e.when || '').slice(0, 19)}</td>
                    <td className="text-xs">{e.actor}</td>
                    <td>{e.action}</td>
                    <td className="koc-mono">{e.ticker || '—'}</td>
                    <td className="koc-mono text-xs">
                      {(e.document_hash || '').slice(0, 12) || '—'}
                    </td>
                  </tr>
                ))}
                {!audit?.entries?.length ? (
                  <tr>
                    <td colSpan={5} className="text-[var(--koc-muted)]">
                      No audited actions yet.
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </section>
      </div>

      <UploadModal
        open={uploadState.open}
        ticker={uploadState.ticker}
        company={uploadState.company}
        documentType={uploadState.documentType}
        actor={user?.email}
        onClose={() => setUploadState((s) => ({ ...s, open: false }))}
        onDone={() => load()}
      />
    </div>
  );
}
