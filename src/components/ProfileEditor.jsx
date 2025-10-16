import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '@/lib/supabaseClient.js';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { EditorContent, useEditor } from '@tiptap/react';

/* ---------- TipTap v3 extensions ---------- */
import StarterKit from '@tiptap/starter-kit';
import Placeholder from '@tiptap/extension-placeholder';
import Link from '@tiptap/extension-link';
import Underline from '@tiptap/extension-underline';
import Highlight from '@tiptap/extension-highlight';
import TextAlign from '@tiptap/extension-text-align';
import { TextStyle } from '@tiptap/extension-text-style';
import Color from '@tiptap/extension-color';
import HorizontalRule from '@tiptap/extension-horizontal-rule';
import TaskList from '@tiptap/extension-task-list';
import TaskItem from '@tiptap/extension-task-item';
import { Table } from '@tiptap/extension-table';
import { TableRow } from '@tiptap/extension-table-row';
import { TableCell } from '@tiptap/extension-table-cell';
import { TableHeader } from '@tiptap/extension-table-header';
import CodeBlockLowlight from '@tiptap/extension-code-block-lowlight';

/* ---------- Lowlight for syntax highlighting ---------- */
import { lowlight } from 'lowlight/lib/core.js';
import javascript from 'highlight.js/lib/languages/javascript';
import xml from 'highlight.js/lib/languages/xml';
import jsonLang from 'highlight.js/lib/languages/json';
lowlight.registerLanguage('javascript', javascript);
lowlight.registerLanguage('xml', xml);
lowlight.registerLanguage('json', jsonLang);

/* ---------- Custom image extension ---------- */
import { CustomImage } from '@/extensions/CustomImage';

/* ---------- Helpers ---------- */
function wordCountFromHTML(html = '') {
  const text = html.replace(/<[^>]*>/g, ' ');
  return text.split(/\s+/).filter(Boolean).length;
}
function readingTime(html = '') {
  return Math.max(1, Math.round(wordCountFromHTML(html) / 200));
}

/* ============================================================ */
/* ------------------- COMPONENT START ------------------------- */
/* ============================================================ */

export default function ProfileEditor() {
  // ✅ Hooks declared unconditionally at the top (fixes React error #310)
  const { user } = useAuth();
  const navigate = useNavigate();

  const [title, setTitle] = useState('');
  const [excerpt, setExcerpt] = useState('');
  const [coverUrl, setCoverUrl] = useState('');
  const [tagsInput, setTagsInput] = useState('');
  const [saving, setSaving] = useState(false);
  const [errorText, setErrorText] = useState('');
  const [dirty, setDirty] = useState(false);

  // ✅ Editor (no character limit)
  const editor = useEditor({
    extensions: [
      StarterKit.configure({ history: true, codeBlock: false }),
      Placeholder.configure({ placeholder: 'Start writing your bio or profile…' }),
      Link.configure({ openOnClick: false, autolink: true }),
      CustomImage,
      Underline,
      Highlight,
      TextStyle,
      Color,
      TextAlign.configure({ types: ['heading', 'paragraph'] }),
      HorizontalRule,
      TaskList,
      TaskItem.configure({ nested: true }),
      Table.configure({ resizable: true }),
      TableRow,
      TableHeader,
      TableCell,
      CodeBlockLowlight.configure({ lowlight }),
    ],
    content: '',
    autofocus: true,
    onUpdate: () => setDirty(true),
  });

  // ✅ Access Control
  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background text-foreground">
        <p className="text-lg font-medium">Please log in to edit your profile.</p>
      </div>
    );
  }

  // ✅ Load Profile Data
  useEffect(() => {
    if (!editor || !user) return;

    (async () => {
      try {
        const { data, error } = await supabase
          .from('profiles')
          .select('id, title, excerpt, content_md, cover_url, tags')
          .eq('id', user.id)
          .maybeSingle();

        if (error) {
          console.error('Profile load error:', error);
          return;
        }

        if (data) {
          setTitle(data.title || '');
          setExcerpt(data.excerpt || '');
          setCoverUrl(data.cover_url || '');
          setTagsInput(Array.isArray(data.tags) ? data.tags.join(', ') : '');
          editor.commands.setContent(data.content_md || '', { emitUpdate: false });
          setDirty(false);
        }
      } catch (err) {
        console.error('Error loading profile:', err);
      }
    })();
  }, [user, editor]);

  // ✅ Upload Helpers
  async function uploadToBucket(bucket, file) {
    const path = `${user.id}/${Date.now()}-${file.name}`;
    const { error } = await supabase.storage.from(bucket).upload(path, file, {
      cacheControl: '3600',
      upsert: false,
    });
    if (error) throw error;
    const { data: pub } = supabase.storage.from(bucket).getPublicUrl(path);
    return pub.publicUrl;
  }

  async function chooseCover() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.onchange = async () => {
      const file = input.files?.[0];
      if (!file) return;
      try {
        const url = await uploadToBucket('covers', file);
        setCoverUrl(url);
        setDirty(true);
      } catch (e) {
        console.error('Cover upload failed:', e);
        alert('Cover upload failed: ' + (e?.message || e));
      }
    };
    input.click();
  }

  // ✅ Save Profile
  async function saveProfile() {
    const html = editor?.getHTML() || '';
    const tags = tagsInput.split(',').map((t) => t.trim()).filter(Boolean);

    const payload = {
      id: user.id,
      title,
      excerpt,
      content_md: html,
      cover_url: coverUrl || null,
      tags,
      updated_at: new Date().toISOString(),
    };

    setSaving(true);
    try {
      const { error } = await supabase.from('profiles').upsert(payload);
      if (error) throw error;
      setDirty(false);
      setErrorText('');
      alert('✅ Profile saved successfully!');
    } catch (err) {
      console.error('Save profile error:', err);
      setErrorText(err?.message || 'Failed to save profile');
    } finally {
      setSaving(false);
    }
  }

  // ✅ Derived Stats
  const html = editor?.getHTML() || '';
  const minutes = useMemo(() => readingTime(html), [html]);
  const words = useMemo(() => wordCountFromHTML(html), [html]);

  // ✅ Render
  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-5xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-6">Edit Profile</h1>

        {/* COVER IMAGE */}
        <div className="mb-6">
          {coverUrl ? (
            <div>
              <img src={coverUrl} alt="Cover" className="w-full rounded-xl border" />
              <div className="mt-3 flex gap-2">
                <Button variant="outline" onClick={chooseCover}>
                  Change Cover
                </Button>
                <Button variant="ghost" onClick={() => setCoverUrl('')}>
                  Remove
                </Button>
              </div>
            </div>
          ) : (
            <div
              className="w-full h-52 rounded-xl border border-dashed flex items-center justify-center cursor-pointer bg-white"
              onClick={chooseCover}
            >
              <span className="text-sm text-gray-500">
                Add a cover image (click to upload)
              </span>
            </div>
          )}
        </div>

        {/* PROFILE FIELDS */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium mb-1">Profile Title</label>
            <input
              className="w-full p-3 rounded-lg border bg-white text-black placeholder-gray-500"
              placeholder="Your headline or role"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium mb-1">Bio Summary</label>
            <input
              className="w-full p-3 rounded-lg border bg-white text-black placeholder-gray-500"
              placeholder="Brief summary about you"
              value={excerpt}
              onChange={(e) => setExcerpt(e.target.value)}
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium mb-1">Skills / Tags</label>
            <input
              className="w-full p-3 rounded-lg border bg-white text-black placeholder-gray-500"
              placeholder="finance, markets, investing"
              value={tagsInput}
              onChange={(e) => setTagsInput(e.target.value)}
            />
          </div>
        </div>

        {/* EDITOR */}
        <div className="bg-white text-black border rounded-xl p-5 min-h-[300px] shadow-sm">
          <EditorContent editor={editor} className="tiptap" />
        </div>

        {errorText && <p className="mt-3 text-sm text-red-600">{errorText}</p>}

        {/* FOOTER */}
        <div className="mt-6 flex flex-wrap items-center gap-3">
          <Button variant="outline" onClick={saveProfile} disabled={saving}>
            {saving ? 'Saving…' : 'Save Profile'}
          </Button>
          <span className="ml-auto text-sm text-gray-500">
            {minutes} min · {words} words
          </span>
        </div>
      </div>
    </div>
  );
}
