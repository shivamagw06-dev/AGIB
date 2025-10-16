// src/pages/PublicProfile.jsx
import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { getPublicProfileByHandle } from '../lib/profileApi';

export default function PublicProfile() {
  const { handle } = useParams();
  const [data, setData] = useState(null);
  const [err, setErr] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const d = await getPublicProfileByHandle(handle);
        setData(d);
      } catch (e) {
        setErr('Profile not found or not public.');
      }
    })();
  }, [handle]);

  if (err) return <div className="p-6">{err}</div>;
  if (!data) return <div className="p-6">Loading…</div>;
  const { profile, experiences, educations, certifications, projects, skills } = data;

  return (
    <div className="max-w-4xl mx-auto">
      <div className="relative">
        {profile.banner_url ? (
          <img src={profile.banner_url} alt="banner" className="w-full h-56 object-cover" />
        ) : <div className="w-full h-56 bg-gray-100" />}
        <div className="absolute left-6 bottom-[-36px] w-28 h-28 rounded-full border-4 border-white overflow-hidden bg-white">
          {profile.photo_url ? <img src={profile.photo_url} alt="avatar" className="w-full h-full object-cover" /> : null}
        </div>
      </div>

      <div className="px-6 mt-12">
        <h1 className="text-3xl font-bold">{profile.full_name}</h1>
        <div className="text-lg opacity-80">{profile.headline}</div>
        <div className="text-sm opacity-70">{[profile.location, profile.industry].filter(Boolean).join(' · ')}</div>
        <div className="mt-3 space-x-3">
          {profile.website && <a className="underline" href={profile.website} target="_blank" rel="noreferrer">Website</a>}
          {profile.github && <a className="underline" href={profile.github} target="_blank" rel="noreferrer">GitHub</a>}
          {profile.twitter && <a className="underline" href={profile.twitter} target="_blank" rel="noreferrer">Twitter</a>}
        </div>

        {profile.summary && <p className="mt-6 whitespace-pre-wrap">{profile.summary}</p>}

        {/* Skills */}
        {skills?.length ? (
          <section className="mt-8">
            <h2 className="text-xl font-semibold mb-2">Skills</h2>
            <div className="flex flex-wrap gap-2">
              {skills.map(s => (
                <span key={s.skill_id} className="px-3 py-1 border rounded text-sm">
                  {s.skills?.name} {s.endorsement_count ? `· ${s.endorsement_count}` : ''}
                </span>
              ))}
            </div>
          </section>
        ) : null}

        {/* Experience */}
        {experiences?.length ? (
          <section className="mt-8">
            <h2 className="text-xl font-semibold mb-2">Experience</h2>
            {experiences.map(x => (
              <div key={x.id} className="border rounded p-3 mb-2">
                <div className="font-semibold">{x.title}</div>
                <div className="text-sm opacity-80">{x.company}</div>
                <div className="text-xs opacity-70 mb-2">
                  {[x.start_date, x.is_current ? 'Present' : x.end_date].filter(Boolean).join(' – ')}
                  {x.location ? ` · ${x.location}` : ''}
                </div>
                {x.description && <div className="text-sm whitespace-pre-wrap">{x.description}</div>}
              </div>
            ))}
          </section>
        ) : null}

        {/* Education */}
        {educations?.length ? (
          <section className="mt-8">
            <h2 className="text-xl font-semibold mb-2">Education</h2>
            {educations.map(e => (
              <div key={e.id} className="border rounded p-3 mb-2">
                <div className="font-semibold">{e.school}</div>
                <div className="text-sm opacity-80">{[e.degree, e.field].filter(Boolean).join(' · ')}</div>
                <div className="text-xs opacity-70 mb-2">{[e.start_year, e.end_year].filter(Boolean).join(' – ')}</div>
                {e.description && <div className="text-sm whitespace-pre-wrap">{e.description}</div>}
              </div>
            ))}
          </section>
        ) : null}

        {/* Projects */}
        {projects?.length ? (
          <section className="mt-8 mb-10">
            <h2 className="text-xl font-semibold mb-2">Projects</h2>
            {projects.map(p => (
              <div key={p.id} className="border rounded p-3 mb-2">
                <div className="font-semibold">
                  {p.url ? <a className="underline" href={p.url} target="_blank" rel="noreferrer">{p.name}</a> : p.name}
                </div>
                <div className="text-sm opacity-80">{p.role}</div>
                <div className="text-xs opacity-70 mb-2">{[p.start_date, p.end_date].filter(Boolean).join(' – ')}</div>
                {p.description && <div className="text-sm whitespace-pre-wrap">{p.description}</div>}
              </div>
            ))}
          </section>
        ) : null}
      </div>
    </div>
  );
}
