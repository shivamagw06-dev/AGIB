import { useCallback, useEffect, useState } from 'react';
import { GraduationCap, Network, RefreshCw, AlertTriangle } from 'lucide-react';
import {
  getAcademyCausalModels,
  getAcademyCompletion,
  getAcademyDashboard,
  getAcademyExams,
  getAcademyHealth,
  getAcademyQuality,
  teachAcademyConcept,
} from '@/lib/intelligenceApi';
import { Button } from '@/components/ui/button';

function Stat({ label, value, hint }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="text-3xl font-bold mt-1 text-slate-900">{value}</p>
      {hint ? <p className="text-xs text-slate-400 mt-1">{hint}</p> : null}
    </div>
  );
}

export default function FinanceAcademy() {
  const [health, setHealth] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [quality, setQuality] = useState(null);
  const [exams, setExams] = useState(null);
  const [completion, setCompletion] = useState(null);
  const [causal, setCausal] = useState(null);
  const [conceptId, setConceptId] = useState('inflation');
  const [lesson, setLesson] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [h, d, q, e, c, cm] = await Promise.all([
        getAcademyHealth(),
        getAcademyDashboard(),
        getAcademyQuality(),
        getAcademyExams(),
        getAcademyCompletion(),
        getAcademyCausalModels(),
      ]);
      setHealth(h);
      setDashboard(d);
      setQuality(q);
      setExams(e);
      setCompletion(c);
      setCausal(cm);
    } catch (err) {
      setError(err?.message || 'Failed to load Finance Academy');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const onTeach = async (e) => {
    e?.preventDefault?.();
    setBusy('teach');
    setError('');
    try {
      const result = await teachAcademyConcept(conceptId.trim() || 'inflation');
      setLesson(result);
    } catch (err) {
      setError(err?.message || 'Teach failed');
    } finally {
      setBusy('');
    }
  };

  const concepts = dashboard?.concepts || [];
  const examSuite = exams?.suite || completion?.exam_suite || {};

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-[10px] uppercase tracking-[0.2em] text-emerald-600 font-semibold">
            Finance Academy v1.0
          </p>
          <h1 className="text-2xl font-bold text-slate-900 mt-1">AGI Finance Academy</h1>
          <p className="text-sm text-slate-500 mt-1 max-w-2xl">
            Institutional economics curriculum from Mankiw — understanding via knowledge objects, causal
            graphs, and financial implications. Not a summariser. Not an engine.
          </p>
        </div>
        <Button variant="outline" onClick={load} disabled={loading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {error ? (
        <div className="flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          <AlertTriangle className="h-4 w-4 mt-0.5" />
          <span>{error}</span>
        </div>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Concepts" value={health?.concept_count ?? concepts.length ?? '—'} hint="Canonical objects" />
        <Stat label="Chapters mapped" value={health?.chapter_count ?? '—'} hint="Mankiw 7e course map" />
        <Stat
          label="Quality"
          value={quality?.passed ? 'Pass' : quality ? 'Review' : '—'}
          hint={`${quality?.publishable ?? 0} publishable`}
        />
        <Stat
          label="Understanding exams"
          value={examSuite.complete ? 'Pass' : examSuite.total != null ? `${examSuite.passed}/${examSuite.total}` : '—'}
          hint="Mechanism tests, not quotes"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="bg-white rounded-xl border border-slate-200 p-5 space-y-4">
          <div className="flex items-center gap-2">
            <GraduationCap className="h-5 w-5 text-emerald-600" />
            <h2 className="font-semibold text-slate-900">Teach a concept</h2>
          </div>
          <form onSubmit={onTeach} className="flex flex-wrap gap-2">
            <select
              className="border border-slate-200 rounded-lg px-3 py-2 text-sm min-w-[220px]"
              value={conceptId}
              onChange={(ev) => setConceptId(ev.target.value)}
            >
              {concepts.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.concept}
                </option>
              ))}
            </select>
            <Button type="submit" disabled={busy === 'teach'}>
              {busy === 'teach' ? 'Teaching…' : 'Teach'}
            </Button>
          </form>
          {lesson ? (
            <div className="text-sm space-y-2 text-slate-700">
              <p>
                <span className="font-medium text-slate-900">What it is: </span>
                {lesson.what_it_is}
              </p>
              <p>
                <span className="font-medium text-slate-900">Investor lens: </span>
                {(lesson.how_investors_should_think || []).slice(0, 2).join(' · ')}
              </p>
              <p className="text-xs text-slate-400">{lesson.teaching_rule}</p>
            </div>
          ) : null}
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5 space-y-4">
          <div className="flex items-center gap-2">
            <Network className="h-5 w-5 text-emerald-600" />
            <h2 className="font-semibold text-slate-900">Causal models</h2>
          </div>
          <ul className="space-y-3 text-sm text-slate-700 max-h-72 overflow-auto">
            {(causal?.models || []).map((m) => (
              <li key={m.model_id} className="border-b border-slate-100 pb-2">
                <p className="font-medium text-slate-900">{m.name}</p>
                <p className="text-xs text-slate-500 mt-1">{(m.chain || []).join(' → ')}</p>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-5">
        <h2 className="font-semibold text-slate-900 mb-3">Completion criteria</h2>
        <div className="grid gap-2 sm:grid-cols-2 text-sm">
          {Object.entries(completion?.criteria || {}).map(([key, ok]) => (
            <div key={key} className="flex items-center justify-between border border-slate-100 rounded-lg px-3 py-2">
              <span className="text-slate-600">{key.replaceAll('_', ' ')}</span>
              <span className={ok ? 'text-emerald-600 font-medium' : 'text-amber-600 font-medium'}>
                {ok ? 'Yes' : 'No'}
              </span>
            </div>
          ))}
        </div>
        <p className="text-xs text-slate-400 mt-3">
          Architecture v1.0.1 locked · soft consumers only · PDF provenance local/gitignored
        </p>
      </div>
    </div>
  );
}
