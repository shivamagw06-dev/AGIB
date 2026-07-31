import { useCallback, useEffect, useMemo, useState } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { Download, Plus, Upload, X } from 'lucide-react';
import {
  createCmsRecord,
  deleteCmsRecord,
  exportCmsModuleCsv,
  fetchCmsRecord,
  fetchCmsRecords,
  importCmsModuleCsv,
  publishCmsRecord,
  updateCmsRecord,
} from '@/lib/intelligenceCmsApi';
import { useAuth } from '@/contexts/AuthContext';

const SLUG_TO_MODULE = {
  'valuation-monitor': 'valuation_monitor',
  transactions: 'transactions',
  'pe-firms': 'pe_firms',
  'portfolio-companies': 'portfolio_companies',
  funds: 'funds',
  industries: 'industries',
  people: 'people',
  'editors-desk': 'editors_desk',
};

function DetailDrawer({ record, moduleDef, onClose, onSave, actor }) {
  const [form, setForm] = useState({ data: {}, detail: {}, status: 'draft', relationships: [] });
  const [versions, setVersions] = useState([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!record) return;
    setForm({
      data: { ...record.data },
      detail: { ...record.detail },
      status: record.status,
      relationships: [...(record.relationships || [])],
    });
    fetchCmsRecord(record.id).then((res) => setVersions(res.versions || []));
  }, [record]);

  if (!record || !moduleDef) return null;

  const setData = (key, val) => setForm((f) => ({ ...f, data: { ...f.data, [key]: val } }));
  const setDetail = (key, val) => setForm((f) => ({ ...f, detail: { ...f.detail, [key]: val } }));

  const save = async (publish = false) => {
    setSaving(true);
    try {
      const body = { ...form, actor };
      if (publish) body.status = 'published';
      await onSave(record.id, body, publish);
      onClose();
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/30">
      <div className="w-full max-w-lg bg-white h-full shadow-xl flex flex-col">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200">
          <h2 className="font-semibold text-slate-900">Record detail</h2>
          <button type="button" onClick={onClose} aria-label="Close"><X size={20} /></button>
        </div>
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          <label className="block text-sm">
            <span className="text-slate-500">Status</span>
            <select
              className="mt-1 w-full border border-slate-200 rounded-md px-3 py-2"
              value={form.status}
              onChange={(e) => setForm((f) => ({ ...f, status: e.target.value }))}
            >
              {['draft', 'review', 'published', 'archived'].map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </label>
          {(moduleDef.columns || []).map((col) => (
            <label key={col.key} className="block text-sm">
              <span className="text-slate-500">{col.label}</span>
              <input
                className="mt-1 w-full border border-slate-200 rounded-md px-3 py-2"
                value={form.data[col.key] || ''}
                onChange={(e) => setData(col.key, e.target.value)}
              />
            </label>
          ))}
          {(moduleDef.detailFields || []).map((field) => (
            <label key={field.key} className="block text-sm">
              <span className="text-slate-500">{field.label}</span>
              {field.type === 'textarea' ? (
                <textarea
                  rows={4}
                  className="mt-1 w-full border border-slate-200 rounded-md px-3 py-2"
                  value={form.detail[field.key] || ''}
                  onChange={(e) => setDetail(field.key, e.target.value)}
                />
              ) : (
                <input
                  className="mt-1 w-full border border-slate-200 rounded-md px-3 py-2"
                  value={form.detail[field.key] || ''}
                  onChange={(e) => setDetail(field.key, e.target.value)}
                />
              )}
            </label>
          ))}
          <div>
            <h3 className="text-sm font-medium text-slate-700 mb-2">Relationships</h3>
            <p className="text-xs text-slate-400 mb-2">Link to companies, industries, PE firms, articles, transactions, funds, people.</p>
            {(form.relationships || []).map((rel, i) => (
              <div key={i} className="flex gap-2 mb-2">
                <input
                  placeholder="Type"
                  className="flex-1 border rounded px-2 py-1 text-sm"
                  value={rel.relation_type || ''}
                  onChange={(e) => {
                    const rels = [...form.relationships];
                    rels[i] = { ...rels[i], relation_type: e.target.value };
                    setForm((f) => ({ ...f, relationships: rels }));
                  }}
                />
                <input
                  placeholder="Label"
                  className="flex-[2] border rounded px-2 py-1 text-sm"
                  value={rel.target_label || ''}
                  onChange={(e) => {
                    const rels = [...form.relationships];
                    rels[i] = { ...rels[i], target_label: e.target.value };
                    setForm((f) => ({ ...f, relationships: rels }));
                  }}
                />
              </div>
            ))}
            <button
              type="button"
              className="text-sm text-[#0b3b60] font-medium"
              onClick={() => setForm((f) => ({
                ...f,
                relationships: [...(f.relationships || []), { relation_type: 'company', target_label: '' }],
              }))}
            >
              + Add relationship
            </button>
          </div>
          {versions.length > 0 && (
            <div className="pt-4 border-t">
              <h3 className="text-sm font-medium text-slate-700">Version history</h3>
              <ul className="mt-2 text-xs text-slate-500 space-y-1">
                {versions.slice(0, 5).map((v) => (
                  <li key={v.id}>v{v.version} · {v.changed_by} · {new Date(v.created_at).toLocaleString()}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
        <div className="p-4 border-t border-slate-200 flex gap-2">
          <button type="button" className="flex-1 py-2 rounded-md bg-slate-100 text-sm font-medium" onClick={() => save(false)} disabled={saving}>
            Save draft
          </button>
          <button type="button" className="flex-1 py-2 rounded-md bg-[#0b3b60] text-white text-sm font-medium" onClick={() => save(true)} disabled={saving}>
            Publish
          </button>
        </div>
      </div>
    </div>
  );
}

export default function IntelligenceModulePage() {
  const { moduleSlug } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const moduleId = SLUG_TO_MODULE[moduleSlug];
  const { user } = useAuth();
  const actor = user?.email || 'admin';

  const [moduleDef, setModuleDef] = useState(null);
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState('');
  const [status, setStatus] = useState(searchParams.get('status') || '');
  const [selected, setSelected] = useState(null);

  const reload = useCallback(async () => {
    if (!moduleId) return;
    setLoading(true);
    try {
      const res = await fetchCmsRecords(moduleId, { status: status || undefined, q: q || undefined });
      setModuleDef(res.module);
      setRecords(res.records);
    } finally {
      setLoading(false);
    }
  }, [moduleId, status, q]);

  useEffect(() => { reload(); }, [reload]);

  const gridCols = useMemo(() => (moduleDef?.columns || []).filter((c) => c.grid !== false), [moduleDef]);

  const handleNew = async () => {
    const data = {};
    gridCols.forEach((c) => { data[c.key] = ''; });
    const rec = await createCmsRecord(moduleId, { data, status: 'draft', actor });
    setSelected(rec);
    reload();
  };

  const handleSave = async (id, body, publish) => {
    if (publish) await publishCmsRecord(id, actor);
    else await updateCmsRecord(id, { ...body, actor });
    reload();
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this record?')) return;
    await deleteCmsRecord(id);
    reload();
  };

  const handleImport = async (file) => {
    const csv = await file.text();
    await importCmsModuleCsv(moduleId, csv, actor);
    reload();
  };

  if (!moduleId) {
    return <div className="p-8 text-slate-500">Module not found.</div>;
  }

  return (
    <div className="p-6 lg:p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">{moduleDef?.label || moduleSlug}</h1>
        <p className="text-slate-500 mt-1">{moduleDef?.description}</p>
      </div>

      <div className="flex flex-wrap gap-2 mb-4 items-center">
        <input
          type="search"
          placeholder="Search…"
          className="border border-slate-200 rounded-md px-3 py-2 text-sm w-48"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <select
          className="border border-slate-200 rounded-md px-3 py-2 text-sm"
          value={status}
          onChange={(e) => {
            setStatus(e.target.value);
            setSearchParams(e.target.value ? { status: e.target.value } : {});
          }}
        >
          <option value="">All statuses</option>
          {['draft', 'review', 'published', 'archived'].map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <button type="button" onClick={handleNew} className="inline-flex items-center gap-1 px-3 py-2 bg-[#0b3b60] text-white text-sm rounded-md">
          <Plus size={16} /> New entry
        </button>
        <button type="button" onClick={() => exportCmsModuleCsv(moduleId)} className="inline-flex items-center gap-1 px-3 py-2 border text-sm rounded-md">
          <Download size={16} /> Export CSV
        </button>
        <label className="inline-flex items-center gap-1 px-3 py-2 border text-sm rounded-md cursor-pointer">
          <Upload size={16} /> Import CSV
          <input type="file" accept=".csv,text/csv" className="hidden" onChange={(e) => e.target.files?.[0] && handleImport(e.target.files[0])} />
        </label>
      </div>

      <div className="bg-white border border-slate-200 rounded-lg overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50">
              {gridCols.map((c) => (
                <th key={c.key} className="text-left px-3 py-2 font-medium text-slate-600">{c.label}</th>
              ))}
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2">Updated</th>
              <th className="px-3 py-2" />
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={gridCols.length + 3} className="p-8 text-center text-slate-400">Loading…</td></tr>
            ) : records.map((r) => (
              <tr
                key={r.id}
                className="border-b border-slate-100 hover:bg-slate-50 cursor-pointer"
                onClick={() => setSelected(r)}
              >
                {gridCols.map((c) => (
                  <td key={c.key} className="px-3 py-2">{r.data?.[c.key] || '—'}</td>
                ))}
                <td className="px-3 py-2"><span className="text-xs uppercase tracking-wide text-[#0b3b60]">{r.status}</span></td>
                <td className="px-3 py-2 text-slate-400 text-xs">{new Date(r.updated_at).toLocaleDateString()}</td>
                <td className="px-3 py-2">
                  <button
                    type="button"
                    className="text-red-600 text-xs"
                    onClick={(e) => { e.stopPropagation(); handleDelete(r.id); }}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selected && (
        <DetailDrawer
          record={selected}
          moduleDef={moduleDef}
          onClose={() => setSelected(null)}
          onSave={handleSave}
          actor={actor}
        />
      )}
    </div>
  );
}
