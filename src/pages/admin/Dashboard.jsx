import { Link, useNavigate } from 'react-router-dom';
import { Plus, FileText, Eye, Pencil, Trash2, Clock } from 'lucide-react';
import useArticlesAdmin from '@/hooks/useArticlesAdmin';
import { formatArticleDate } from '@/lib/articleUtils';
import { Button } from '@/components/ui/button';

export default function AdminDashboard() {
  const navigate = useNavigate();
  const { articles, loading, deleteArticle, stats } = useArticlesAdmin();

  const handleDelete = async (id, title) => {
    if (!window.confirm(`Delete "${title}"? This cannot be undone.`)) return;
    try {
      await deleteArticle(id);
    } catch (err) {
      alert(err.message || 'Delete failed');
    }
  };

  return (
    <div className="p-6 lg:p-8 max-w-7xl">
      <div className="flex flex-wrap items-start justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
          <p className="text-slate-500 mt-1">Manage your research articles and market updates</p>
        </div>
        <Button onClick={() => navigate('/admin/articles/new')} className="bg-blue-700 hover:bg-blue-800">
          <Plus size={16} className="mr-2" />
          New Article
        </Button>
      </div>

      <div className="grid sm:grid-cols-3 gap-4 mb-8">
        {[
          ['Total Articles', stats.total, 'text-slate-900'],
          ['Published', stats.published, 'text-green-600'],
          ['Drafts', stats.drafts, 'text-amber-600'],
        ].map(([label, value, color]) => (
          <div key={label} className="bg-white rounded-xl border border-slate-200 p-5">
            <p className="text-sm text-slate-500">{label}</p>
            <p className={`text-3xl font-bold mt-1 ${color}`}>{value}</p>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-2">
          <FileText size={18} className="text-slate-400" />
          <h2 className="font-semibold text-slate-900">Recent Articles</h2>
        </div>

        {loading ? (
          <p className="p-8 text-center text-slate-400">Loading articles…</p>
        ) : articles.length === 0 ? (
          <div className="p-12 text-center">
            <p className="text-slate-500 mb-4">No articles yet. Write your first market update or research report.</p>
            <Button onClick={() => navigate('/admin/articles/new')} className="bg-blue-700 hover:bg-blue-800">
              Create First Article
            </Button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-slate-500 uppercase text-xs tracking-wide">
                <tr>
                  <th className="text-left px-5 py-3 font-medium">Title</th>
                  <th className="text-left px-5 py-3 font-medium">Category</th>
                  <th className="text-left px-5 py-3 font-medium">Status</th>
                  <th className="text-left px-5 py-3 font-medium">Date</th>
                  <th className="text-right px-5 py-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {articles.map((article) => (
                  <tr key={article.id} className="hover:bg-slate-50/80">
                    <td className="px-5 py-4">
                      <p className="font-medium text-slate-900 line-clamp-1">{article.title}</p>
                      <p className="text-xs text-slate-400 mt-0.5">/{article.slug}</p>
                    </td>
                    <td className="px-5 py-4 text-slate-600">{article.section || '—'}</td>
                    <td className="px-5 py-4">
                      <span
                        className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                          article.status === 'published'
                            ? 'bg-green-100 text-green-700'
                            : 'bg-amber-100 text-amber-700'
                        }`}
                      >
                        {article.status}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-slate-500 whitespace-nowrap">
                      <span className="flex items-center gap-1">
                        <Clock size={13} />
                        {formatArticleDate(article.published_at || article.created_at)}
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex items-center justify-end gap-1">
                        {article.status === 'published' && (
                          <Link
                            to={`/article/${article.slug}`}
                            target="_blank"
                            className="p-2 rounded-md text-slate-400 hover:text-blue-600 hover:bg-blue-50"
                            title="View"
                          >
                            <Eye size={16} />
                          </Link>
                        )}
                        <button
                          type="button"
                          onClick={() => navigate(`/admin/articles/edit/${article.slug}`)}
                          className="p-2 rounded-md text-slate-400 hover:text-blue-600 hover:bg-blue-50"
                          title="Edit"
                        >
                          <Pencil size={16} />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDelete(article.id, article.title)}
                          className="p-2 rounded-md text-slate-400 hover:text-red-600 hover:bg-red-50"
                          title="Delete"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
