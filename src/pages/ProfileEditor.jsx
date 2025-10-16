// src/pages/ProfileEditor.jsx
import React, { useEffect, useMemo, useState } from 'react';
import {
  getMyProfile, upsertMyProfile, checkHandleUnique,
  uploadAvatar, uploadBanner,
  listSection, addSection, updateSection, deleteSection,
  sections,
} from '../lib/profileApi';
import { supabase } from '../lib/supabaseClient';

function LabeledInput({ label, ...props }) {
  return (
    <label className="block mb-3">
      <span className="block text-sm font-medium mb-1">{label}</span>
      <input className="w-full border rounded px-3 py-2" {...props} />
    </label>
  );
}
function TextArea({ label, ...props }) {
  return (
    <label className="block mb-3">
      <span className="block text-sm font-medium mb-1">{label}</span>
      <textarea className="w-full border rounded px-3 py-2" rows={props.rows ?? 4} {...props} />
    </label>
  );
}
function SectionRow({ item, onEdit, onDelete, titleKey, subtitleKey, right }) {
  return (
    <div className="flex items-start justify-between border rounded p-3 mb-2">
      <div>
        <div className="font-semibold">{item[titleKey]}</div>
        <div className="text-sm opacity-80">{item[subtitleKey]}</div>
        {right ? <div className="text-xs opacity-70 mt-1">{right(item)}</div> : null}
      </div>
      <div className="flex gap-2">
        <button className="text-blue-600" onClick={() => onEdit(item)}>Edit</button>
        <button className="text-red-600" onClick={() => onDelete(item.id)}>Delete</button>
      </div>
    </div>
  );
}

export default function ProfileEditor() {
  const [profile, setProfile] = useState(null);
  const [saving, setSaving] = useState(false);
  const [handleStatus, setHandleStatus] = useState(''); // '', 'checking', 'ok', 'taken'
  const [me, setMe] = useState(null);
  const [exp, setExp] = useState([]);
  const [edu, setEdu] = useState([]);
  const [message, setMessage] = useState('');

  useEffect(() => {
    (async () => {
      const { data: { user } } = await supabase.auth.getUser();
      setMe(user);
      const p = await getMyProfile();
      setProfile({
        full_name: p.full_name ?? '',
        display_name: p.display_name ?? '',
        handle: p.handle ?? (user?.email?.split('@')[0] || ''),
        headline: p.headline ?? '',
        summary: p.summary ?? '',
        location: p.location ?? '',
        industry: p.industry ?? '',
        website: p.website ?? '',
        github: p.github ?? '',
        twitter: p.twitter ?? '',
        photo_url: p.photo_url ?? '',
        banner_url: p.banner_url ?? '',
        is_public: p.is_public ?? true,
      });
      setExp(await listSection('experiences', user.id));
      setEdu(await listSection('educations', user.id));
    })();
  }, []);

  async function saveProfile(e) {
    e?.preventDefault();
    setSaving(true);
    setMessage('');
    try {
      // validate handle uniqueness if changed
      if (profile.handle) {
        const ok = await checkHandleUnique(profile.handle);
        // allow if it's our own handle; simplest: try upsert & rely on unique constraint
        if (!ok && profile.handle !== (me?.email?.split('@')[0] ?? '')) {
          setHandleStatus('taken');
          setSaving(false);
          return;
        }
        setHandleStatus('ok');
      }
      const saved = await upsertMyProfile(profile);
      setProfile(prev => ({ ...prev, ...saved }));
      setMessage('Profile saved ✅');
    } catch (err) {
      console.error(err);
      setMessage(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function onAvatarChange(ev) {
    const file = ev.target.files?.[0];
    if (!file) return;
    const url = await uploadAvatar(file);
    setProfile(p => ({ ...p, photo_url: url }));
  }
  async function onBannerChange(ev) {
    const file = ev.target.files?.[0];
    if (!file) return;
    const url = await uploadBanner(file);
    setProfile(p => ({ ...p, banner_url: url }));
  }

  // ---- experience & education simple forms ----
  const [draft, setDraft] = useState(null); // {table, data}
  function openDraft(table, data = {}) {
    setDraft({ table, data });
  }
  async function saveDraft() {
    const table = draft.table;
    const payload = draft.data;
    if (payload.id) {
      const updated = await updateSection(table, payload.id, payload);
      applyList(table, (list) => list.map(r => r.id === updated.id ? updated : r));
    } else {
      const created = await addSection(table, payload);
      applyList(table, (list) => [created, ...list]);
    }
    setDraft(null);
  }
  async function removeRow(table, id) {
    await deleteSection(table, id);
    applyList(table, (list) => list.filter(r => r.id !== id));
  }
  function applyList(table, updater) {
    if (table === sections.experiences) setExp(updater);
    if (table === sections.educations) setEdu(updater);
  }

  if (!profile) return <div className="p-6">Loading…</div>;

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">Edit Profile</h1>

      {/* Banner + Avatar */}
      <div className="relative mb-6">
        {profile.banner_url ? (
          <img src={profile.banner_url} alt="banner" className="w-full h-48 object-cover rounded" />
        ) : (
          <div className="w-full h-48 bg-gray-100 rounded" />
        )}
        <label className="absolute right-3 bottom-3 bg-white border rounded px-3 py-1 cursor-pointer">
          Change cover
          <input type="file" className="hidden" onChange={onBannerChange} />
        </label>
        <div className="absolute left-6 bottom-[-24px]">
          <div className="w-24 h-24 rounded-full border-4 border-white overflow-hidden bg-white">
            {profile.photo_url ? <img src={profile.photo_url} alt="avatar" className="w-full h-full object-cover" /> : null}
          </div>
          <label className="block mt-2 text-sm text-blue-700 cursor-pointer">
            Update photo
            <input type="file" className="hidden" onChange={onAvatarChange} />
          </label>
        </div>
      </div>

      <form onSubmit={saveProfile} className="mt-10">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <LabeledInput label="Full name" value={profile.full_name} onChange={e => setProfile(p => ({ ...p, full_name: e.target.value }))} />
          <LabeledInput label="Handle (public URL)" value={profile.handle} onChange={e => { setHandleStatus(''); setProfile(p => ({ ...p, handle: e.target.value.toLowerCase().replace(/[^a-z0-9\-]/g,'-') })); }} />
          <LabeledInput label="Headline" value={profile.headline} onChange={e => setProfile(p => ({ ...p, headline: e.target.value }))} />
          <LabeledInput label="Location" value={profile.location} onChange={e => setProfile(p => ({ ...p, location: e.target.value }))} />
          <LabeledInput label="Industry" value={profile.industry} onChange={e => setProfile(p => ({ ...p, industry: e.target.value }))} />
          <LabeledInput label="Website" value={profile.website} onChange={e => setProfile(p => ({ ...p, website: e.target.value }))} />
          <LabeledInput label="GitHub" value={profile.github} onChange={e => setProfile(p => ({ ...p, github: e.target.value }))} />
          <LabeledInput label="Twitter/X" value={profile.twitter} onChange={e => setProfile(p => ({ ...p, twitter: e.target.value }))} />
        </div>
        <TextArea label="Summary" value={profile.summary} onChange={e => setProfile(p => ({ ...p, summary: e.target.value }))} />

        <label className="flex items-center gap-2 mb-4">
          <input type="checkbox" checked={!!profile.is_public} onChange={e => setProfile(p => ({ ...p, is_public: e.target.checked }))} />
          <span>Make my profile public</span>
        </label>

        <button disabled={saving} className="bg-black text-white px-4 py-2 rounded">{saving ? 'Saving…' : 'Save Profile'}</button>
        <span className="ml-3 text-sm">{handleStatus === 'taken' ? 'Handle already taken' : message}</span>
      </form>

      {/* Experiences */}
      <div className="mt-10">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-xl font-semibold">Experience</h2>
          <button className="text-blue-600" onClick={() => openDraft(sections.experiences, { title: '', company: '', start_date: '', end_date: null, is_current: false, location: '', description: '' })}>Add</button>
        </div>
        {exp.map(item => (
          <SectionRow key={item.id}
            item={item}
            titleKey="title"
            subtitleKey="company"
            right={(it) => `${it.start_date ?? ''} – ${it.is_current ? 'Present' : (it.end_date ?? '')}`}
            onEdit={(it) => openDraft(sections.experiences, it)}
            onDelete={(id) => removeRow(sections.experiences, id)}
          />
        ))}
      </div>

      {/* Education */}
      <div className="mt-8">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-xl font-semibold">Education</h2>
          <button className="text-blue-600" onClick={() => openDraft(sections.educations, { school: '', degree: '', field: '', start_year: null, end_year: null, description: '' })}>Add</button>
        </div>
        {edu.map(item => (
          <SectionRow key={item.id}
            item={item}
            titleKey="school"
            subtitleKey="degree"
            right={(it) => [it.field, [it.start_year, it.end_year].filter(Boolean).join('–')].filter(Boolean).join(' · ')}
            onEdit={(it) => openDraft(sections.educations, it)}
            onDelete={(id) => removeRow(sections.educations, id)}
          />
        ))}
      </div>

      {/* Draft modal (simple inline) */}
      {draft && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center">
          <div className="bg-white rounded p-4 w-full max-w-lg">
            <h3 className="font-semibold mb-3">{draft.table === sections.experiences ? 'Experience' : 'Education'}</h3>
            {draft.table === sections.experiences ? (
              <>
                <LabeledInput label="Title" value={draft.data.title || ''} onChange={e => setDraft(d => ({ ...d, data: { ...d.data, title: e.target.value } }))} />
                <LabeledInput label="Company" value={draft.data.company || ''} onChange={e => setDraft(d => ({ ...d, data: { ...d.data, company: e.target.value } }))} />
                <LabeledInput label="Location" value={draft.data.location || ''} onChange={e => setDraft(d => ({ ...d, data: { ...d.data, location: e.target.value } }))} />
                <div className="grid grid-cols-2 gap-3">
                  <LabeledInput type="date" label="Start date" value={draft.data.start_date || ''} onChange={e => setDraft(d => ({ ...d, data: { ...d.data, start_date: e.target.value } }))} />
                  <LabeledInput type="date" label="End date" value={draft.data.end_date || ''} onChange={e => setDraft(d => ({ ...d, data: { ...d.data, end_date: e.target.value } }))} />
                </div>
                <label className="flex items-center gap-2 mb-2">
                  <input type="checkbox" checked={!!draft.data.is_current} onChange={e => setDraft(d => ({ ...d, data: { ...d.data, is_current: e.target.checked } }))} />
                  <span>Currently working here</span>
                </label>
                <TextArea label="Description" value={draft.data.description || ''} onChange={e => setDraft(d => ({ ...d, data: { ...d.data, description: e.target.value } }))} />
              </>
            ) : (
              <>
                <LabeledInput label="School" value={draft.data.school || ''} onChange={e => setDraft(d => ({ ...d, data: { ...d.data, school: e.target.value } }))} />
                <LabeledInput label="Degree" value={draft.data.degree || ''} onChange={e => setDraft(d => ({ ...d, data: { ...d.data, degree: e.target.value } }))} />
                <LabeledInput label="Field" value={draft.data.field || ''} onChange={e => setDraft(d => ({ ...d, data: { ...d.data, field: e.target.value } }))} />
                <div className="grid grid-cols-2 gap-3">
                  <LabeledInput label="Start year" type="number" value={draft.data.start_year || ''} onChange={e => setDraft(d => ({ ...d, data: { ...d.data, start_year: e.target.valueAsNumber || null } }))} />
                  <LabeledInput label="End year" type="number" value={draft.data.end_year || ''} onChange={e => setDraft(d => ({ ...d, data: { ...d.data, end_year: e.target.valueAsNumber || null } }))} />
                </div>
                <TextArea label="Description" value={draft.data.description || ''} onChange={e => setDraft(d => ({ ...d, data: { ...d.data, description: e.target.value } }))} />
              </>
            )}

            <div className="flex justify-end gap-2 mt-3">
              <button className="px-3 py-2" onClick={() => setDraft(null)}>Cancel</button>
              <button className="bg-black text-white px-3 py-2 rounded" onClick={saveDraft}>Save</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
