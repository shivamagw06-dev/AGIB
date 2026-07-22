import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  FolderOpen,
  Plus,
  ExternalLink,
  LogOut,
  ChevronRight,
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

const navItems = [
  { to: '/admin', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/admin/articles/new', label: 'New Article', icon: Plus },
  { to: '/admin/categories', label: 'Categories', icon: FolderOpen },
];

export default function AdminLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex bg-slate-100">
      <aside className="w-64 shrink-0 bg-[#0c1220] text-white flex flex-col border-r border-slate-800">
        <div className="px-5 py-6 border-b border-slate-800">
          <p className="text-[10px] uppercase tracking-[0.2em] text-orange-400 font-semibold">AGIB CMS</p>
          <h1 className="text-lg font-bold mt-1">Content Studio</h1>
          <p className="text-xs text-slate-400 mt-1 truncate">{user?.email}</p>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}

          <button
            type="button"
            onClick={() => navigate('/admin/articles')}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
          >
            <FileText size={18} />
            All Articles
          </button>
        </nav>

        <div className="px-3 py-4 border-t border-slate-800 space-y-1">
          <button
            type="button"
            onClick={() => window.open('/', '_blank')}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
          >
            <ExternalLink size={16} />
            View Website
          </button>
          <button
            type="button"
            onClick={async () => {
              await logout();
              navigate('/login');
            }}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
          >
            <LogOut size={16} />
            Sign Out
          </button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-14 shrink-0 bg-white border-b border-slate-200 flex items-center justify-between px-6">
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <span>CMS</span>
            <ChevronRight size={14} />
            <span className="text-slate-900 font-medium">Editor</span>
          </div>
          <span className="text-xs text-slate-400">Publish market updates in real time</span>
        </header>

        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
