import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { EditorContent, useEditor } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Placeholder from '@tiptap/extension-placeholder';
import Link from '@tiptap/extension-link';
import Highlight from '@tiptap/extension-highlight';
import TextAlign from '@tiptap/extension-text-align';
import { TextStyle } from '@tiptap/extension-text-style';
import Color from '@tiptap/extension-color';
import HorizontalRule from '@tiptap/extension-horizontal-rule';
import { Table } from '@tiptap/extension-table';
import TableRow from '@tiptap/extension-table-row';
import TableCell from '@tiptap/extension-table-cell';
import TableHeader from '@tiptap/extension-table-header';
import { Eye, Save, Send, ImageIcon, Loader2 } from 'lucide-react';
import { supabase } from '@/lib/supabaseClient';
import { useAuth } from '@/contexts/AuthContext';
import useCategories from '@/hooks/useCategories';
import EditorToolbar from '@/components/editor/EditorToolbar';
import ArticlePreview from '@/components/editor/ArticlePreview';
import { CustomImage } from '@/extensions/CustomImage';
import { IframeEmbed } from '@/extensions/IframeEmbed';
import {
  generateUniqueSlug,
  htmlToExcerpt,
  readingTime,
  toSlug,
  wordCountFromHTML,
} from '@/lib/articleUtils';
import { Button } from '@/components/ui/button';

const AUTOSAVE_MS = 4000;

function toEmbedUrl(raw) {
  const url = raw.trim();
  if (!url) return null;
  const yt = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([\w-]+)/);
  if (yt) return `https://www.youtube.com/embed/${yt[1]}`;
  if (/vimeo\.com\/(\d+)/.test(url)) return url.replace('vimeo.com/', 'player.vimeo.com/video/');
  return url;
}

export default function ArticleEditor() {
  const { slug: editSlugParam } = useParams();
  const editSlug = editSlugParam ? decodeURIComponent(editSlugParam) : '';
  const navigate = useNavigate();
  const { user } = useAuth();
  const { categories, loading: categoriesLoading } = useCategories();

  const [title, setTitle] = useState('');
  const [slug, setSlug] = useState('');
  const [slugManual, setSlugManual] = useState(false);
  const [metaDescription, setMetaDescription] = useState('');
  const [section, setSection] = useState('');
  const [tagsInput, setTagsInput] = useState('');
  const [coverUrl, setCoverUrl] = useState('');
  const [draftId, setDraftId] = useState(null);
  const [status, setStatus] = useState('draft');
  const [saving, setSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState(null);
  const [error, setError] = useState('');
  const [previewOpen, setPreviewOpen] = useState(false);
  const [loaded, setLoaded] = useState(!editSlug);

  const pendingContentRef = useRef('');
  const autosaveTimer = useRef(null);
  const dirtyRef = useRef(false);

  const extensions = useMemo(
    () => [
      StarterKit.configure({ heading: { levels: [1, 2, 3] } }),
      Placeholder.configure({ placeholder: 'Start writing your research or market update…' }),
      Link.configure({ openOnClick: false, autolink: true }),
      CustomImage,
      IframeEmbed,
      Highlight,
      TextStyle,
      Color,
      HorizontalRule,
      TextAlign.configure({ types: ['heading', 'paragraph'] }),
      Table.configure({ resizable: true }),
      TableRow,
      TableHeader,
      TableCell,
    ],
    []
  );

  const editor = useEditor({
    extensions,
    content: '<p></p>',
    editorProps: {
      attributes: {
        class: 'prose prose-lg max-w-none min-h-[420px] px-8 py-6 focus:outline-none',
      },
    },
    onUpdate: () => {
      dirtyRef.current = true;
    },
  });

  useEffect(() => {
    if (!categoriesLoading && categories.length && !section) {
      setSection(categories[0].name);
    }
  }, [categories, categoriesLoading, section]);

  useEffect(() => {
    if (!slugManual && title) setSlug(toSlug(title));
  }, [title, slugManual]);

  useEffect(() => {
    if (!editSlug || !user) return;
    let mounted = true;

    (async () => {
      const { data, error: loadError } = await supabase
        .from('articles')
        .select('id, title, slug, section, excerpt, meta_description, content_md, content, cover_url, tags, status')
        .eq('slug', editSlug)
        .maybeSingle();

      if (!mounted) return;
      if (loadError || !data) {
        setError('Article not found.');
        setLoaded(true);
        return;
      }

      setDraftId(data.id);
      setTitle(data.title || '');
      setSlug(data.slug || '');
      setSlugManual(true);
      setMetaDescription(data.meta_description || data.excerpt || '');
      setSection(data.section || '');
      setCoverUrl(data.cover_url || '');
      setTagsInput(Array.isArray(data.tags) ? data.tags.join(', ') : '');
      setStatus(data.status || 'draft');

      const html = data.content_md || data.content || '';
      if (editor) editor.commands.setContent(html, false);
      else pendingContentRef.current = html;

      setLoaded(true);
    })();

    return () => {
      mounted = false;
    };
  }, [editSlug, user, editor]);

  useEffect(() => {
    if (editor && pendingContentRef.current) {
      editor.commands.setContent(pendingContentRef.current, false);
      pendingContentRef.current = '';
    }
  }, [editor]);

  const uploadFile = useCallback(
    async (bucket, file) => {
      const path = `${user.id}/${Date.now()}-${file.name}`;
      const { error: uploadError } = await supabase.storage.from(bucket).upload(path, file);
      if (uploadError) throw uploadError;
      const { data } = supabase.storage.from(bucket).getPublicUrl(path);
      return data.publicUrl;
    },
    [user.id]
  );

  const insertImage = useCallback(async () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.onchange = async () => {
      const file = input.files?.[0];
      if (!file || !editor) return;
      try {
        const url = await uploadFile('images', file);
        editor.chain().focus().setImage({ src: url }).run();
      } catch (err) {
        alert(`Image upload failed: ${err.message}`);
      }
    };
    input.click();
  }, [editor, uploadFile]);

  const insertVideo = useCallback(() => {
    const raw = window.prompt('Paste YouTube, Vimeo, or embed URL');
    const src = toEmbedUrl(raw || '');
    if (!src || !editor) return;
    editor.chain().focus().setIframeEmbed({ src, title: 'Video embed', height: 420 }).run();
  }, [editor]);

  const insertChart = useCallback(() => {
    const raw = window.prompt('Paste TradingView or chart embed URL');
    if (!raw?.trim() || !editor) return;
    editor.chain().focus().setIframeEmbed({ src: raw.trim(), title: 'Chart embed', height: 480 }).run();
  }, [editor]);

  const chooseCover = useCallback(async () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.onchange = async () => {
      const file = input.files?.[0];
      if (!file) return;
      try {
        const url = await uploadFile('covers', file);
        setCoverUrl(url);
        dirtyRef.current = true;
      } catch (err) {
        alert(`Cover upload failed: ${err.message}`);
      }
    };
    input.click();
  }, [uploadFile]);

  const buildPayload = useCallback(
    (publishStatus) => {
      const html = editor?.getHTML() || '';
      const tags = tagsInput.split(',').map((t) => t.trim()).filter(Boolean);
      const excerpt = metaDescription.trim() || htmlToExcerpt(html, 320);

      const payload = {
        author_id: user.id,
        title: title.trim() || 'Untitled',
        slug: slug || toSlug(title) || `draft-${Date.now()}`,
        section,
        excerpt,
        content_md: html,
        content: html,
        cover_url: coverUrl || null,
        tags: tags.length ? tags : null,
        status: publishStatus,
      };

      if (metaDescription.trim()) payload.meta_description = metaDescription.trim();
      if (publishStatus === 'published') payload.published_at = new Date().toISOString();

      return payload;
    },
    [editor, tagsInput, metaDescription, user.id, title, slug, section, coverUrl]
  );

  const persist = useCallback(
    async (publishStatus, { silent = false } = {}) => {
      if (!editor) return null;
      setSaving(true);
      setError('');

      try {
        let articleSlug = slug || (await generateUniqueSlug(title, draftId));
        if (!slugManual) setSlug(articleSlug);

        const payload = { ...buildPayload(publishStatus), slug: articleSlug };

        let result;
        if (draftId) {
          result = await supabase.from('articles').update(payload).eq('id', draftId).select('id, slug, status').single();
        } else {
          result = await supabase.from('articles').insert(payload).select('id, slug, status').single();
        }

        let { data, error: saveError } = result;

        if (saveError?.message?.includes('meta_description')) {
          const { meta_description, ...fallbackPayload } = payload;
          result = draftId
            ? await supabase.from('articles').update(fallbackPayload).eq('id', draftId).select('id, slug, status').single()
            : await supabase.from('articles').insert(fallbackPayload).select('id, slug, status').single();
          ({ data, error: saveError } = result);
        }
        if (saveError) throw saveError;

        setDraftId(data.id);
        setSlug(data.slug);
        setStatus(data.status);
        setLastSaved(new Date());
        dirtyRef.current = false;

        if (!silent && publishStatus === 'published') {
          navigate(`/article/${data.slug}`);
        }

        return data;
      } catch (err) {
        const msg = err?.message || 'Save failed';
        setError(msg);
        if (!silent) alert(msg);
        return null;
      } finally {
        setSaving(false);
      }
    },
    [editor, slug, slugManual, title, draftId, buildPayload, navigate]
  );

  useEffect(() => {
    if (!editor || !loaded || !user) return;

    autosaveTimer.current = setInterval(() => {
      if (dirtyRef.current && title.trim()) {
        persist('draft', { silent: true });
      }
    }, AUTOSAVE_MS);

    return () => clearInterval(autosaveTimer.current);
  }, [editor, loaded, user, title, persist]);

  const html = editor?.getHTML() || '';
  const words = wordCountFromHTML(html);
  const minutes = readingTime(html);

  if (!loaded) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-400">
        <Loader2 className="animate-spin mr-2" size={20} /> Loading editor…
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Top bar */}
      <div className="shrink-0 bg-white border-b border-slate-200 px-6 py-3 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3 text-sm text-slate-500">
          <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${status === 'published' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'}`}>
            {status}
          </span>
          {saving ? (
            <span className="flex items-center gap-1"><Loader2 size={14} className="animate-spin" /> Saving…</span>
          ) : lastSaved ? (
            <span>Saved {lastSaved.toLocaleTimeString()}</span>
          ) : (
            <span>Auto-save enabled</span>
          )}
          <span>· {words} words · {minutes} min read</span>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => setPreviewOpen(true)}>
            <Eye size={15} className="mr-1.5" /> Preview
          </Button>
          <Button variant="outline" size="sm" onClick={() => persist('draft')} disabled={saving}>
            <Save size={15} className="mr-1.5" /> Save Draft
          </Button>
          <Button size="sm" className="bg-blue-700 hover:bg-blue-800" onClick={() => persist('published')} disabled={saving || !title.trim()}>
            <Send size={15} className="mr-1.5" /> Publish
          </Button>
        </div>
      </div>

      {error && (
        <div className="mx-6 mt-4 px-4 py-3 rounded-lg bg-red-50 text-red-700 text-sm border border-red-200">{error}</div>
      )}

      <div className="flex-1 flex overflow-hidden">
        {/* Editor column */}
        <div className="flex-1 overflow-y-auto bg-slate-50">
          {/* Cover */}
          <div className="bg-white border-b border-slate-200">
            {coverUrl ? (
              <div className="relative group">
                <img src={coverUrl} alt="Cover" className="w-full max-h-72 object-cover" />
                <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-3">
                  <Button size="sm" variant="secondary" onClick={chooseCover}>Change</Button>
                  <Button size="sm" variant="secondary" onClick={() => setCoverUrl('')}>Remove</Button>
                </div>
              </div>
            ) : (
              <button
                type="button"
                onClick={chooseCover}
                className="w-full h-40 flex flex-col items-center justify-center gap-2 text-slate-400 hover:bg-slate-50 transition-colors border-b border-dashed border-slate-200"
              >
                <ImageIcon size={24} />
                <span className="text-sm">Add featured image</span>
              </button>
            )}
          </div>

          <div className="max-w-4xl mx-auto">
            <input
              value={title}
              onChange={(e) => {
                setTitle(e.target.value);
                dirtyRef.current = true;
              }}
              placeholder="Headline — e.g. Morning Market Update: Nifty Holds 24,800"
              className="w-full px-8 pt-8 pb-4 text-3xl md:text-4xl font-bold text-slate-900 bg-white border-b border-slate-100 outline-none placeholder:text-slate-300"
            />

            <div className="bg-white border border-slate-200 rounded-b-xl shadow-sm mx-4 mb-8 overflow-hidden">
              <EditorToolbar editor={editor} onInsertImage={insertImage} onInsertVideo={insertVideo} onInsertChart={insertChart} />
              <EditorContent editor={editor} />
            </div>
          </div>
        </div>

        {/* SEO sidebar */}
        <aside className="w-80 shrink-0 bg-white border-l border-slate-200 overflow-y-auto p-5 space-y-5">
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-widest text-slate-400 mb-3">Publishing</h3>
            <label className="block text-sm font-medium text-slate-700 mb-1">Category</label>
            <select
              className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm"
              value={section}
              onChange={(e) => {
                setSection(e.target.value);
                dirtyRef.current = true;
              }}
            >
              {categories.map((cat) => (
                <option key={cat.id || cat.slug} value={cat.name}>{cat.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">URL Slug</label>
            <input
              className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm font-mono"
              value={slug}
              onChange={(e) => {
                setSlug(toSlug(e.target.value));
                setSlugManual(true);
                dirtyRef.current = true;
              }}
            />
            <p className="text-xs text-slate-400 mt-1">/article/{slug || '…'}</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Meta Description</label>
            <textarea
              className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm resize-none"
              rows={3}
              maxLength={160}
              placeholder="SEO summary (160 chars max)"
              value={metaDescription}
              onChange={(e) => {
                setMetaDescription(e.target.value);
                dirtyRef.current = true;
              }}
            />
            <p className="text-xs text-slate-400 mt-1">{metaDescription.length}/160</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Tags</label>
            <input
              className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm"
              placeholder="nifty, rbi, banking"
              value={tagsInput}
              onChange={(e) => {
                setTagsInput(e.target.value);
                dirtyRef.current = true;
              }}
            />
            <p className="text-xs text-slate-400 mt-1">Comma-separated</p>
          </div>

          <div className="pt-4 border-t border-slate-100">
            <h3 className="text-xs font-semibold uppercase tracking-widest text-slate-400 mb-2">SEO Preview</h3>
            <div className="rounded-lg border border-slate-200 p-3 bg-slate-50">
              <p className="text-blue-700 text-sm font-medium line-clamp-1">{title || 'Article Title'}</p>
              <p className="text-green-700 text-xs mt-0.5 truncate">agarwalglobalinvestments.com/article/{slug || '…'}</p>
              <p className="text-slate-600 text-xs mt-1 line-clamp-2">
                {metaDescription || htmlToExcerpt(html, 120) || 'Meta description will appear here.'}
              </p>
            </div>
          </div>
        </aside>
      </div>

      <ArticlePreview
        open={previewOpen}
        onClose={() => setPreviewOpen(false)}
        article={{ title, section, metaDescription, coverUrl, status }}
        html={html}
      />
    </div>
  );
}
